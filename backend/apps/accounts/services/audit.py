from apps.accounts.models import AuditLog, Company, User

# Campos que nunca devem ser persistidos em metadata de auditoria
_SENSITIVE_METADATA_KEYS = frozenset({
    'password',
    'password1',
    'password2',
    'old_password',
    'new_password',
    'secret',
    'token',
    'refresh',
    'access',
    'api_key',
    'webhook_secret',
    'credentials',
    'cpf',
    'email',
    'phone',
    'content',
    'access_token',
    'verify_token',
})


def sanitize_metadata(metadata: dict | None) -> dict:
    """Remove campos sensíveis antes de gravar audit log."""
    if not metadata:
        return {}
    cleaned: dict = {}
    for key, value in metadata.items():
        key_lower = str(key).lower()
        if key_lower in _SENSITIVE_METADATA_KEYS or 'password' in key_lower or 'secret' in key_lower or 'token' in key_lower:
            cleaned[key] = '[REDACTED]'
        elif isinstance(value, dict):
            cleaned[key] = sanitize_metadata(value)
        else:
            cleaned[key] = value
    return cleaned


def get_client_ip(request) -> str | None:
    """Extrai IP do cliente a partir do request."""
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit(
    *,
    action: str,
    entity_type: str,
    entity_id: str | int = '',
    entity_label: str = '',
    actor: User | None = None,
    company: Company | None = None,
    metadata: dict | None = None,
    request=None,
) -> AuditLog:
    """Registra evento de auditoria."""
    return AuditLog.objects.create(
        actor=actor,
        company=company,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else '',
        entity_label=entity_label,
        metadata=sanitize_metadata(metadata),
        ip_address=get_client_ip(request),
    )
