import hashlib
import hmac
import logging
import secrets

from django.conf import settings

from apps.accounts.models import SecurityEvent
from apps.accounts.services.audit import get_client_ip
from apps.accounts.services.security_events import log_security_event

logger = logging.getLogger('security')
WEBHOOK_RATE_LIMIT = int(__import__('os').getenv('WEBHOOK_RATE_LIMIT_PER_MINUTE', '120'))
WEBHOOK_RATE_WINDOW_SECONDS = 60


def _rate_key(ip: str | None, channel_id: int) -> str:
    return f'webhook:rate:{ip or "unknown"}:{channel_id}'


def check_webhook_rate_limit(request, channel_id: int) -> bool:
    """Retorna True se dentro do limite; False se excedeu."""
    from django.core.cache import cache

    ip = get_client_ip(request) or 'unknown'
    key = _rate_key(ip, channel_id)
    current = cache.get(key)
    if current is None:
        cache.set(key, 1, WEBHOOK_RATE_WINDOW_SECONDS)
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, WEBHOOK_RATE_WINDOW_SECONDS)
        return True
    if count > WEBHOOK_RATE_LIMIT:
        log_security_event(
            SecurityEvent.EventType.RATE_LIMIT_HIT,
            ip_address=ip if ip != 'unknown' else None,
            channel_id=channel_id,
            metadata={'source': 'webhook'},
        )
        return False
    return True


def log_webhook_auth_failure(request, channel_id: int, reason: str, company_id: int | None = None) -> None:
    """Registra tentativa inválida de webhook."""
    ip = get_client_ip(request)
    logger.warning(
        'Webhook rejeitado canal=%s ip=%s motivo=%s',
        channel_id,
        ip,
        reason,
    )
    log_security_event(
        SecurityEvent.EventType.WEBHOOK_REJECTED,
        ip_address=ip,
        channel_id=channel_id,
        company_id=company_id,
        metadata={'reason': reason},
    )


def validate_meta_hub_signature(request, app_secret: str) -> bool:
    """Valida X-Hub-Signature-256 conforme documentação Meta."""
    if not app_secret:
        return False
    signature_header = request.headers.get('X-Hub-Signature-256', '')
    if not signature_header.startswith('sha256='):
        return False
    received = signature_header[7:]
    expected = hmac.new(
        app_secret.encode('utf-8'),
        request.body,
        hashlib.sha256,
    ).hexdigest()
    return secrets.compare_digest(received, expected)


def reject_query_secret_in_production(request) -> bool:
    """Em produção, secret via query string não é aceito (vaza em logs)."""
    return not settings.DEBUG and bool(request.GET.get('secret'))

