import hashlib
import hmac
import time

from django.conf import settings


MEDIA_URL_TTL_SECONDS = 300


def build_signed_media_url(request, message_id: int) -> str | None:
    expires = int(time.time()) + MEDIA_URL_TTL_SECONDS
    user_id = ''
    if getattr(request, 'user', None) and request.user.is_authenticated:
        user_id = str(request.user.id)
    signature = _sign(message_id, expires, user_id)
    base = request.build_absolute_uri(f'/api/v1/media/{message_id}/')
    query = f'exp={expires}&sig={signature}'
    if user_id:
        query = f'{query}&uid={user_id}'
    return f'{base}?{query}'


def verify_media_signature(message_id: int, expires: str, signature: str, user_id: str = '') -> bool:
    try:
        exp_int = int(expires)
    except (TypeError, ValueError):
        return False
    if exp_int < int(time.time()):
        return False
    expected = _sign(message_id, exp_int, user_id)
    return hmac.compare_digest(expected, signature or '')


def _sign(message_id: int, expires: int, user_id: str = '') -> str:
    payload = f'{message_id}:{expires}:{user_id}'
    return hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
