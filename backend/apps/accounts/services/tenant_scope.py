"""Validação central de escopo multi-empresa (tenant)."""

from __future__ import annotations

from rest_framework.exceptions import ValidationError

from apps.accounts.models import Company, User
from apps.accounts.services.capabilities import is_platform_operator
from apps.whatsapp.models import Channel


class TenantScopeError(ValidationError):
    """Erro de violação de escopo entre entidades de empresas distintas."""


def resolve_company_for_request(user: User, company_id: int | str | None) -> Company | None:
    """Resolve empresa ativa para a requisição conforme papel do usuário."""
    if is_platform_operator(user):
        if not company_id:
            return None
        try:
            pk = int(company_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError({'company_id': 'company_id inválido.'}) from exc
        company = Company.objects.filter(pk=pk, is_active=True).first()
        if not company:
            raise ValidationError({'company_id': 'Empresa inválida ou inativa.'})
        return company
    if not user.company_id:
        return None
    if not user.company.is_active:
        raise ValidationError({'detail': 'Empresa inativa.'})
    return user.company


def require_company_for_superuser(user: User, company: Company | None) -> Company:
    """Exige company_id explícito para superuser em APIs tenant-scoped."""
    if not user.is_superuser:
        if company is None:
            raise ValidationError({'detail': 'Usuário sem empresa vinculada.'})
        return company
    if company is None:
        raise ValidationError({'company_id': 'Informe company_id para operar no escopo da empresa.'})
    return company


def validate_entities_same_company(*entities, company: Company) -> None:
    """Garante que entidades com company_id pertencem ao mesmo tenant."""
    for entity in entities:
        if entity is None:
            continue
        entity_company_id = getattr(entity, 'company_id', None)
        if entity_company_id is None:
            entity_company = getattr(entity, 'company', None)
            entity_company_id = getattr(entity_company, 'id', None) if entity_company else None
        if entity_company_id is not None and entity_company_id != company.id:
            raise TenantScopeError({'detail': 'Recurso pertence a outra empresa.'})


def validate_channel_ids_for_company(channel_ids: list[int], company: Company) -> list[Channel]:
    """Valida que todos os canais pertencem à empresa informada."""
    if not channel_ids:
        return []
    channels = list(Channel.objects.filter(pk__in=channel_ids, company=company))
    if len(channels) != len(set(channel_ids)):
        raise TenantScopeError({'channel_ids': 'Um ou mais canais não pertencem à empresa.'})
    return channels


def validate_channel_for_company(channel: Channel, company: Company) -> Channel:
    """Valida canal único no escopo da empresa."""
    if channel.company_id != company.id:
        raise TenantScopeError({'channel': 'Canal não pertence à empresa informada.'})
    return channel
