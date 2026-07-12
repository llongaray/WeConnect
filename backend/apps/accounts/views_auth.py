import os

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.captcha import verify_turnstile
from apps.accounts.cookie_auth import clear_jwt_cookies, get_refresh_from_request, set_jwt_cookies
from apps.accounts.models import AuditLog, SecurityEvent, User
from apps.accounts.serializers import UserPublicSerializer
from apps.accounts.services.audit import get_client_ip, log_audit
from apps.accounts.services.login_security import (
    LOGIN_GENERIC_MESSAGE,
    clear_success,
    get_failure_count,
    is_blocked,
    register_failure,
    remaining_lockout_seconds,
)
from apps.accounts.services.security_events import log_security_event
from apps.accounts.services.capabilities import get_user_capabilities
from apps.accounts.services.trusted_device import is_trusted_for_user, issue_trusted_device
from apps.accounts.throttles import AuthRateThrottle
from apps.accounts.totp_service import (
    create_pending_login,
    create_pending_setup,
    get_access_mode,
    get_pending_setup_user,
    pop_pending_login,
    user_requires_totp_setup,
    user_has_totp,
    verify_backup_code,
    verify_totp_code,
)

CAPTCHA_AFTER_FAILURES = int(os.getenv('CAPTCHA_AFTER_FAILURES', '3'))


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['is_superuser'] = user.is_superuser
        if user.company_id:
            token['company_id'] = user.company_id
            token['company_code'] = user.company.code
        return token

    def validate(self, attrs):
        request = self.context.get('request')
        ip = get_client_ip(request)
        username = attrs.get('username', '')

        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            result = register_failure(ip, username)
            log_audit(
                action=AuditLog.Action.LOGIN_FAILED,
                entity_type='auth',
                entity_label=username,
                metadata={
                    'reason': 'invalid_credentials',
                    'attempt': result['attempt_count'],
                    'max_attempts': result['max_attempts'],
                },
                request=request,
            )
            log_security_event(
                SecurityEvent.EventType.LOGIN_FAILED,
                ip_address=ip,
                username=username,
                metadata={'attempt': result['attempt_count']},
            )
            if result['locked']:
                log_audit(
                    action=AuditLog.Action.LOGIN_BLOCKED,
                    entity_type='auth',
                    entity_label=username,
                    metadata={
                        'reason': 'brute_force',
                        'attempt': result['attempt_count'],
                    },
                    request=request,
                )
                log_security_event(
                    SecurityEvent.EventType.LOGIN_BLOCKED,
                    ip_address=ip,
                    username=username,
                    metadata={'reason': 'brute_force'},
                )
            raise AuthenticationFailed(LOGIN_GENERIC_MESSAGE) from None

        user = self.user

        if user.company_id and not user.company.is_active:
            log_audit(
                action=AuditLog.Action.LOGIN_BLOCKED,
                entity_type='user',
                entity_id=user.id,
                entity_label=user.username,
                actor=user,
                company=user.company,
                metadata={'reason': 'company_inactive'},
                request=request,
            )
            raise AuthenticationFailed('Empresa inativa. Entre em contato com o suporte.')

        if not user.is_active:
            raise AuthenticationFailed('Usuário inativo.')

        clear_success(ip, username)

        data['user'] = UserPublicSerializer(user).data
        data['is_superuser'] = user.is_superuser
        return data


def _build_session_payload(user: User, refresh: RefreshToken | None = None) -> dict:
    """Monta payload de sessão sem expor tokens JWT no corpo JSON."""
    return {
        'user': UserPublicSerializer(user).data,
        'is_superuser': user.is_superuser,
        'requires_totp_setup': user_requires_totp_setup(user),
        'totp_enabled': user_has_totp(user),
        'access_mode': get_access_mode(user),
        'requires_privacy_acceptance': user.privacy_terms_accepted_at is None,
        'capabilities': get_user_capabilities(user),
        'is_weconnect_support': bool(user.is_staff and not user.is_superuser),
    }


def _build_login_response(user: User, refresh: RefreshToken) -> dict:
    return _build_session_payload(user)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        username = request.data.get('username', '')

        if is_blocked(ip, username):
            remaining = remaining_lockout_seconds(ip, username)
            log_audit(
                action=AuditLog.Action.LOGIN_BLOCKED,
                entity_type='auth',
                entity_label=username,
                metadata={'reason': 'brute_force', 'remaining_seconds': remaining},
                request=request,
            )
            log_security_event(
                SecurityEvent.EventType.LOGIN_BLOCKED,
                ip_address=ip,
                username=username,
                metadata={'remaining_seconds': remaining},
            )
            return Response(
                {
                    'detail': LOGIN_GENERIC_MESSAGE,
                    'lockout_seconds': remaining,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        failures = get_failure_count(ip, username)
        requires_captcha = failures >= CAPTCHA_AFTER_FAILURES
        if requires_captcha and settings.TURNSTILE_SECRET_KEY:
            captcha_token = request.data.get('captcha_token', '')
            if not verify_turnstile(captcha_token, ip):
                return Response(
                    {
                        'detail': 'Verificação CAPTCHA obrigatória.',
                        'requires_captcha': True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (AuthenticationFailed, ValidationError):
            failures = get_failure_count(ip, username)
            return Response(
                {
                    'detail': LOGIN_GENERIC_MESSAGE,
                    'requires_captcha': failures >= CAPTCHA_AFTER_FAILURES and bool(settings.TURNSTILE_SECRET_KEY),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.user

        if user_requires_totp_setup(user):
            setup_token = create_pending_setup(user.id)
            data = _build_session_payload(user)
            return Response(
                {
                    **data,
                    'setup_token': setup_token,
                    'detail': 'Configure 2FA antes de continuar.',
                },
                status=status.HTTP_200_OK,
            )

        if user_has_totp(user):
            if is_trusted_for_user(user, request):
                log_security_event(
                    SecurityEvent.EventType.TOTP_SUCCESS,
                    ip_address=ip,
                    username=user.username,
                    company=user.company,
                    metadata={'trusted_device': True},
                )
                refresh = RefreshToken.for_user(user)
                data = _build_login_response(user, refresh)
                response = Response(data, status=status.HTTP_200_OK)
                return set_jwt_cookies(response, str(refresh.access_token), str(refresh))

            pending = create_pending_login(user.id)
            return Response(
                {
                    'requires_totp': True,
                    'pending_token': pending,
                    'requires_captcha': False,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        refresh = RefreshToken.for_user(user)
        data = _build_login_response(user, refresh)
        response = Response(data, status=status.HTTP_200_OK)
        return set_jwt_cookies(response, str(refresh.access_token), str(refresh))


class LoginPrecheckView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def get(self, request):
        ip = get_client_ip(request)
        username = request.query_params.get('username', '')
        failures = get_failure_count(ip, username)
        return Response({
            'requires_captcha': failures >= CAPTCHA_AFTER_FAILURES and bool(settings.TURNSTILE_SECRET_KEY),
            'locked': is_blocked(ip, username),
            'lockout_seconds': remaining_lockout_seconds(ip, username),
            'turnstile_site_key': settings.TURNSTILE_SITE_KEY,
        })


class LoginTotpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        ip = get_client_ip(request)
        pending = request.data.get('pending_token', '')
        code = request.data.get('code', '')
        user_id = pop_pending_login(pending)
        if not user_id:
            return Response({'detail': 'Sessão expirada. Faça login novamente.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'Usuário inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        valid = verify_totp_code(user, code) or verify_backup_code(user, code)
        if not valid:
            log_security_event(
                SecurityEvent.EventType.TOTP_FAILED,
                ip_address=ip,
                username=user.username,
                company=user.company,
            )
            log_audit(
                action=AuditLog.Action.TOTP_FAILED,
                entity_type='auth',
                entity_label=user.username,
                actor=user,
                request=request,
            )
            return Response({'detail': 'Código 2FA inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        log_security_event(
            SecurityEvent.EventType.TOTP_SUCCESS,
            ip_address=ip,
            username=user.username,
            company=user.company,
        )
        log_audit(
            action=AuditLog.Action.TOTP_SUCCESS,
            entity_type='auth',
            entity_label=user.username,
            actor=user,
            request=request,
        )

        refresh = RefreshToken.for_user(user)
        data = _build_login_response(user, refresh)
        response = Response(data, status=status.HTTP_200_OK)
        response = set_jwt_cookies(response, str(refresh.access_token), str(refresh))
        if request.data.get('trust_device'):
            issue_trusted_device(response, user, request)
        return response


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        refresh_value = get_refresh_from_request(request)
        payload = dict(request.data) if request.data else {}
        if refresh_value and 'refresh' not in payload:
            payload['refresh'] = refresh_value
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        response = Response({'detail': 'Token renovado.'}, status=status.HTTP_200_OK)
        access = validated.get('access')
        refresh = validated.get('refresh') or refresh_value
        if access:
            set_jwt_cookies(response, access, refresh)
        return response


class LogoutView(APIView):
    """Invalida refresh token via blacklist JWT."""
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        refresh = get_refresh_from_request(request)
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return clear_jwt_cookies(response)


class SessionView(APIView):
    """Retorna usuário autenticado via cookie JWT."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(_build_session_payload(user))


class AcceptPrivacyView(APIView):
    """Registra aceite da política de privacidade (primeiro acesso)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.privacy_terms_accepted_at:
            user.privacy_terms_accepted_at = timezone.now()
            user.save(update_fields=['privacy_terms_accepted_at'])
            log_audit(
                action=AuditLog.Action.UPDATE,
                entity_type='user',
                entity_id=user.id,
                entity_label=user.username,
                actor=user,
                company=user.company,
                metadata={'privacy_terms_accepted': True},
                request=request,
            )
        return Response(_build_session_payload(user))


class AcceptPrivacyPendingView(APIView):
    """Aceite de privacidade durante onboarding 2FA (sem JWT, via setup_token)."""
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        setup_token = request.data.get('setup_token', '')
        user_id = get_pending_setup_user(setup_token)
        if not user_id:
            return Response({'detail': 'Sessão expirada. Faça login novamente.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'Usuário inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.privacy_terms_accepted_at:
            user.privacy_terms_accepted_at = timezone.now()
            user.save(update_fields=['privacy_terms_accepted_at'])
            log_audit(
                action=AuditLog.Action.UPDATE,
                entity_type='user',
                entity_id=user.id,
                entity_label=user.username,
                actor=user,
                company=user.company,
                metadata={'privacy_terms_accepted': True},
                request=request,
            )
        data = _build_session_payload(user)
        return Response(data, status=status.HTTP_200_OK)


class CsrfTokenView(APIView):
    """Emite cookie CSRF para double-submit (mutações API)."""
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        from django.middleware.csrf import get_token
        return Response({'csrfToken': get_token(request)})
