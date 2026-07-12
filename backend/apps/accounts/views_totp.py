from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.cookie_auth import set_jwt_cookies
from apps.accounts.models import AuditLog, SecurityEvent, User
from apps.accounts.views_auth import _build_session_payload
from apps.accounts.services.audit import log_audit
from apps.accounts.services.security_events import log_security_event
from apps.accounts.services.trusted_device import revoke_all_trusted_devices
from apps.accounts.throttles import AuthRateThrottle
from apps.accounts.totp_service import (
    confirm_totp_device,
    create_totp_device,
    disable_totp,
    generate_backup_codes,
    get_pending_setup_user,
    pop_pending_setup,
    qr_code_base64,
    user_has_totp,
    verify_totp_code,
)


class TotpSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if user_has_totp(request.user):
            return Response({'detail': '2FA já está ativo.'}, status=status.HTTP_400_BAD_REQUEST)
        device, uri = create_totp_device(request.user)
        return Response({
            'qr_code_base64': qr_code_base64(uri),
            'otpauth_uri': uri,
            'device_id': device.id,
        })


class TotpSetupPendingView(APIView):
    """Inicia setup 2FA com token temporário pós-login."""
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
        if user_has_totp(user):
            return Response({'detail': '2FA já está ativo.'}, status=status.HTTP_400_BAD_REQUEST)
        device, uri = create_totp_device(user)
        return Response({
            'qr_code_base64': qr_code_base64(uri),
            'otpauth_uri': uri,
            'device_id': device.id,
        })


class TotpConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '')
        if not confirm_totp_device(request.user, code):
            return Response({'detail': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        backup_codes = generate_backup_codes(request.user)
        log_audit(
            action=AuditLog.Action.TOTP_ENABLED,
            entity_type='user',
            entity_id=request.user.id,
            entity_label=request.user.username,
            actor=request.user,
            request=request,
        )
        log_security_event(
            SecurityEvent.EventType.TOTP_SUCCESS,
            ip_address=request.META.get('REMOTE_ADDR'),
            username=request.user.username,
            company=request.user.company,
            metadata={'action': 'totp_setup_completed'},
        )
        refresh = RefreshToken.for_user(request.user)
        data = _build_session_payload(request.user)
        data['totp_enabled'] = True
        response = Response({**data, 'backup_codes': backup_codes}, status=status.HTTP_200_OK)
        return set_jwt_cookies(response, str(refresh.access_token), str(refresh))


class TotpConfirmPendingView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        setup_token = request.data.get('setup_token', '')
        code = request.data.get('code', '')
        user_id = get_pending_setup_user(setup_token)
        if not user_id:
            return Response({'detail': 'Sessão expirada. Faça login novamente.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'Usuário inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        if not confirm_totp_device(user, code):
            return Response({'detail': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        backup_codes = generate_backup_codes(user)
        log_audit(
            action=AuditLog.Action.TOTP_ENABLED,
            entity_type='user',
            entity_id=user.id,
            entity_label=user.username,
            actor=user,
            request=request,
        )
        pop_pending_setup(setup_token)
        refresh = RefreshToken.for_user(user)
        data = _build_session_payload(user)
        data['totp_enabled'] = True
        response = Response({**data, 'backup_codes': backup_codes}, status=status.HTTP_200_OK)
        return set_jwt_cookies(response, str(refresh.access_token), str(refresh))


class TotpDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '')
        if not verify_totp_code(request.user, code):
            return Response({'detail': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        disable_totp(request.user)
        revoke_all_trusted_devices(request.user)
        log_audit(
            action=AuditLog.Action.TOTP_DISABLED,
            entity_type='user',
            entity_id=request.user.id,
            entity_label=request.user.username,
            actor=request.user,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TotpStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'enabled': user_has_totp(request.user)})
