import httpx
from django.conf import settings


def verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    """Valida token Cloudflare Turnstile (tier gratuito)."""
    secret = settings.TURNSTILE_SECRET_KEY
    if not secret:
        return True
    if not token:
        return False
    try:
        response = httpx.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': secret,
                'response': token,
                'remoteip': remote_ip or '',
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return bool(response.json().get('success'))
    except httpx.HTTPError:
        return False
