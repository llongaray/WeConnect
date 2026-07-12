"""Cookie de dispositivo confiável para pular 2FA em logins futuros."""

import os
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from apps.accounts.models import TrustedDevice, User
from apps.accounts.services.audit import get_client_ip

TRUSTED_DEVICE_DAYS = int(os.getenv('TRUSTED_DEVICE_DAYS', '30'))
TRUSTED_DEVICE_MAX = int(os.getenv('TRUSTED_DEVICE_MAX', '10'))


def _cookie_max_age() -> int:
    return TRUSTED_DEVICE_DAYS * 86400


def _cookie_secure() -> bool:
    return not settings.DEBUG


def _parse_cookie(raw: str | None) -> tuple[str, str] | None:
    if not raw or '.' not in raw:
        return None
    device_uuid, token = raw.split('.', 1)
    if not device_uuid or not token:
        return None
    return device_uuid, token


def _get_active_device(device_uuid: str) -> TrustedDevice | None:
    try:
        device = TrustedDevice.objects.get(
            device_uuid=device_uuid,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
    except TrustedDevice.DoesNotExist:
        return None
    return device


def get_trusted_device_from_request(request) -> TrustedDevice | None:
    """Retorna dispositivo confiável válido a partir do cookie, ou None."""
    parsed = _parse_cookie(request.COOKIES.get(settings.TRUSTED_DEVICE_COOKIE_NAME))
    if not parsed:
        return None
    device_uuid, token = parsed
    device = _get_active_device(device_uuid)
    if not device or not check_password(token, device.token_hash):
        return None
    return device


def is_trusted_for_user(user: User, request) -> bool:
    """Verifica se o cookie pertence ao usuário autenticado por senha."""
    device = get_trusted_device_from_request(request)
    if not device or device.user_id != user.id:
        return False
    device.last_used_at = timezone.now()
    device.save(update_fields=['last_used_at'])
    return True


def _trim_excess_devices(user: User) -> None:
    active = (
        TrustedDevice.objects.filter(
            user=user,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by('-last_used_at', '-created_at')
    )
    excess = list(active[TRUSTED_DEVICE_MAX:])
    if excess:
        TrustedDevice.objects.filter(pk__in=[item.pk for item in excess]).delete()


def issue_trusted_device(response, user: User, request):
    """Registra dispositivo confiável e define cookie HttpOnly."""
    _trim_excess_devices(user)
    token = secrets.token_urlsafe(32)
    device = TrustedDevice.objects.create(
        user=user,
        token_hash=make_password(token),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:255],
        ip_address=get_client_ip(request) or None,
        expires_at=timezone.now() + timedelta(days=TRUSTED_DEVICE_DAYS),
    )
    response.set_cookie(
        settings.TRUSTED_DEVICE_COOKIE_NAME,
        f'{device.device_uuid}.{token}',
        max_age=_cookie_max_age(),
        httponly=True,
        secure=_cookie_secure(),
        samesite='Lax',
        path='/',
    )
    return response


def revoke_all_trusted_devices(user: User) -> int:
    """Revoga todos os dispositivos confiáveis do usuário (ex.: troca de senha)."""
    now = timezone.now()
    return TrustedDevice.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=now)
