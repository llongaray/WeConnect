import io
import os
import secrets

import qrcode
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts.models import User

TOTP_PENDING_TTL = 300
TOTP_SETUP_TTL = 600
TOTP_ISSUER = 'WeConnect'


def get_totp_required_roles() -> list[str]:
    raw = os.getenv('TOTP_REQUIRED_ROLES', 'superuser,gestor')
    return [part.strip() for part in raw.split(',') if part.strip()]


def user_has_totp(user: User) -> bool:
    return TOTPDevice.objects.filter(user=user, confirmed=True).exists()


def user_requires_totp_setup(user: User) -> bool:
    if user_has_totp(user):
        return False
    if user.is_staff and not user.is_superuser:
        return True
    roles = get_totp_required_roles()
    if user.is_superuser and 'superuser' in roles:
        return True
    if user.role == User.Role.GESTOR and 'gestor' in roles:
        return True
    return False


def get_access_mode(user: User) -> str:
    """Modo de acesso da sessão: setup_only até concluir 2FA."""
    return 'setup_only' if user_requires_totp_setup(user) else 'full'


def superuser_requires_totp(user: User) -> bool:
    return user_requires_totp_setup(user)


def create_totp_device(user: User) -> tuple[TOTPDevice, str]:
    """Cria dispositivo TOTP não confirmado e retorna URI para QR."""
    TOTPDevice.objects.filter(user=user, confirmed=False).delete()
    device = TOTPDevice.objects.create(user=user, name='default', confirmed=False)
    uri = device.config_url
    return device, uri


def qr_code_base64(uri: str) -> str:
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    import base64

    return base64.b64encode(buffer.getvalue()).decode('ascii')


def confirm_totp_device(user: User, code: str) -> bool:
    device = TOTPDevice.objects.filter(user=user, confirmed=False).order_by('-id').first()
    if not device:
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if not device:
            return False
    if not device.verify_token(code):
        return False
    device.confirmed = True
    device.save(update_fields=['confirmed'])
    return True


def verify_totp_code(user: User, code: str) -> bool:
    for device in TOTPDevice.objects.filter(user=user, confirmed=True):
        if device.verify_token(code):
            return True
    return False


def disable_totp(user: User) -> None:
    TOTPDevice.objects.filter(user=user).delete()


def _pending_key(token: str) -> str:
    return f'totp:pending:{token}'


def _setup_key(token: str) -> str:
    return f'totp:setup:{token}'


def create_pending_login(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    cache.set(_pending_key(token), user_id, TOTP_PENDING_TTL)
    return token


def pop_pending_login(token: str) -> int | None:
    key = _pending_key(token)
    user_id = cache.get(key)
    if user_id is None:
        return None
    cache.delete(key)
    return int(user_id)


def create_pending_setup(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    cache.set(_setup_key(token), user_id, TOTP_SETUP_TTL)
    return token


def get_pending_setup_user(token: str) -> int | None:
    user_id = cache.get(_setup_key(token))
    return int(user_id) if user_id is not None else None


def pop_pending_setup(token: str) -> int | None:
    key = _setup_key(token)
    user_id = cache.get(key)
    if user_id is None:
        return None
    cache.delete(key)
    return int(user_id)


def generate_backup_codes(user: User, count: int = 8) -> list[str]:
    """Gera códigos de backup e persiste hashes no perfil."""
    from apps.accounts.models import UserSecurityProfile

    profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
    codes = [secrets.token_hex(4).upper() for _ in range(count)]
    profile.backup_codes = [make_password(code) for code in codes]
    profile.save(update_fields=['backup_codes'])
    return codes


def verify_backup_code(user: User, code: str) -> bool:
    from apps.accounts.models import UserSecurityProfile

    try:
        profile = user.security_profile
    except UserSecurityProfile.DoesNotExist:
        return False
    normalized = code.strip().upper().replace('-', '')
    remaining: list[str] = []
    used = False
    for hashed in profile.backup_codes:
        if not used and check_password(normalized, hashed):
            used = True
            continue
        remaining.append(hashed)
    if used:
        profile.backup_codes = remaining
        profile.save(update_fields=['backup_codes'])
    return used
