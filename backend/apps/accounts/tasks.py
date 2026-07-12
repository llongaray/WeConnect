from celery import shared_task
from django.core.management import call_command


@shared_task(name='accounts.purge_security_events')
def purge_security_events_task(days: int = 90) -> None:
    """Remove eventos de segurança antigos (retenção padrão 90 dias)."""
    call_command('purge_security_events', days=days)


@shared_task(name='accounts.purge_audit_logs')
def purge_audit_logs_task(days: int = 365) -> int:
    """Remove logs de auditoria antigos."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.accounts.models import AuditLog

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
    return deleted
