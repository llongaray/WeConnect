import logging
import secrets

from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.accounts.authentication import CookieJWTAuthentication
from apps.accounts.totp_service import user_requires_totp_setup

logger = logging.getLogger(__name__)


def _resolve_authenticated_user(request):
    """Resolve usuário JWT (cookie) para middlewares antes do DRF."""
    if getattr(request, 'user', None) and request.user.is_authenticated:
        return request.user
    auth = CookieJWTAuthentication()
    try:
        result = auth.authenticate(request)
    except InvalidToken:
        return None
    if not result:
        return None
    user, _token = result
    request.user = user
    return user


class ActiveAccountMiddleware:
    """Bloqueia requisições autenticadas de usuário ou empresa inativos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/api/auth/login') or path.startswith('/api/auth/login/precheck'):
            return self.get_response(request)

        user = _resolve_authenticated_user(request)
        if user and user.is_authenticated:
            if not user.is_active:
                from django.http import JsonResponse
                return JsonResponse({'detail': 'Usuário inativo.'}, status=403)
            if user.company_id:
                company = user.company
                if company and not company.is_active:
                    from django.http import JsonResponse
                    return JsonResponse({'detail': 'Empresa inativa.'}, status=403)
        return self.get_response(request)


class PrivacyAcceptanceGateMiddleware:
    """Bloqueia API v1 até o usuário aceitar a política de privacidade."""

    SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/api/v1/'):
            user = _resolve_authenticated_user(request)
            if user and user.is_authenticated and not user.privacy_terms_accepted_at:
                if not self._is_allowed(request, path):
                    from django.http import JsonResponse
                    return JsonResponse(
                        {
                            'detail': 'Aceite a política de privacidade para continuar.',
                            'requires_privacy_acceptance': True,
                        },
                        status=403,
                    )
        return self.get_response(request)

    def _is_allowed(self, request, path: str) -> bool:
        # Perfil e empresas (GET) liberados para exibir dados básicos durante onboarding
        if path.startswith('/api/v1/profile'):
            return True
        if path.startswith('/api/v1/companies') and request.method in self.SAFE_METHODS:
            return True
        return False


class TotpSetupGateMiddleware:
    """Bloqueia API v1 enquanto 2FA obrigatório não estiver configurado."""

    SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/api/v1/'):
            user = _resolve_authenticated_user(request)
            if user and user.is_authenticated and user_requires_totp_setup(user):
                if not self._is_allowed(request, path):
                    from django.http import JsonResponse
                    return JsonResponse(
                        {
                            'detail': 'Configure 2FA antes de continuar.',
                            'requires_totp_setup': True,
                        },
                        status=403,
                    )
        return self.get_response(request)

    def _is_allowed(self, request, path: str) -> bool:
        # Apenas perfil e listagem de empresas (GET) durante onboarding 2FA
        if path.startswith('/api/v1/profile'):
            return True
        if path.startswith('/api/v1/companies') and request.method in self.SAFE_METHODS:
            return True
        return False


class ApiCsrfMiddleware:
    """Valida header X-CSRFToken em mutações da API autenticada."""

    SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})
    EXEMPT_PREFIXES = (
        '/api/webhooks/',
        '/api/auth/login/',
        '/api/auth/login/totp/',
        '/api/auth/login/precheck/',
        '/api/auth/totp/setup-pending/',
        '/api/auth/totp/confirm-pending/',
        '/api/auth/accept-privacy-pending/',
        '/api/auth/csrf/',
    )
    CSRF_PROTECTED_AUTH_PATHS = (
        '/api/auth/refresh/',
        '/api/auth/logout/',
        '/api/auth/accept-privacy/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._must_validate(request):
            cookie_token = request.COOKIES.get(settings.CSRF_COOKIE_NAME, '')
            header_token = request.META.get('HTTP_X_CSRFTOKEN', '')
            if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
                from django.http import JsonResponse
                return JsonResponse({'detail': 'CSRF token inválido ou ausente.'}, status=403)
        return self.get_response(request)

    def _must_validate(self, request) -> bool:
        if request.method in self.SAFE_METHODS:
            return False
        path = request.path
        for auth_path in self.CSRF_PROTECTED_AUTH_PATHS:
            if path.startswith(auth_path):
                return True
        if not path.startswith('/api/v1/'):
            return False
        for prefix in self.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return False
        return True
