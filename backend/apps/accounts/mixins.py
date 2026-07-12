from rest_framework.exceptions import ValidationError

from apps.accounts.models import Company
from apps.accounts.services.capabilities import is_platform_operator
from apps.accounts.services.tenant_scope import require_company_for_superuser, resolve_company_for_request


class CompanyScopedMixin:
    """Filtra queryset pelo escopo da empresa do usuário autenticado."""

    company_field = 'company'
    superuser_requires_company = True

    def get_company_scope(self) -> Company | None:
        user = self.request.user
        company_id = self.request.query_params.get('company_id')
        if is_platform_operator(user) and not self.superuser_requires_company:
            if company_id:
                return resolve_company_for_request(user, company_id)
            return None
        return resolve_company_for_request(user, company_id) if is_platform_operator(user) else user.company

    def require_tenant_company(self) -> Company:
        """Retorna empresa obrigatória para operações tenant-scoped."""
        return require_company_for_superuser(self.request.user, self.get_company_scope())

    def filter_queryset_by_company(self, queryset):
        user = self.request.user
        if is_platform_operator(user) and not self.superuser_requires_company:
            company = self.get_company_scope()
            if company is not None:
                return queryset.filter(**{self.company_field: company})
            return queryset

        company = self.get_company_scope()
        if company is not None:
            return queryset.filter(**{self.company_field: company})
        if is_platform_operator(user):
            raise ValidationError({'company_id': 'Informe company_id para operar no escopo da empresa.'})
        return queryset.none()
