import logging

from apps.accounts.models import Company, SecurityEvent
from apps.accounts.services.security_alerts import maybe_alert_for_event

logger = logging.getLogger('security')


def log_security_event(
    event_type: str,
    *,
    ip_address: str | None = None,
    username: str = '',
    channel_id: int | None = None,
    company: Company | None = None,
    company_id: int | None = None,
    metadata: dict | None = None,
) -> SecurityEvent:
    resolved_company_id = company_id
    if company is not None:
        resolved_company_id = company.id

    event = SecurityEvent.objects.create(
        event_type=event_type,
        company_id=resolved_company_id,
        ip_address=ip_address,
        username=username,
        channel_id=channel_id,
        metadata=metadata or {},
    )
    maybe_alert_for_event(
        event_type,
        ip_address=ip_address,
        username=username,
        metadata=metadata,
    )
    logger.info(
        'security_event type=%s ip=%s user=%s company=%s',
        event_type,
        ip_address or '',
        username or '',
        resolved_company_id or '',
    )
    return event
