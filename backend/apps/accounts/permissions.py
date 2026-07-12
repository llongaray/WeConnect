from rest_framework.permissions import BasePermission

from apps.accounts.services.capabilities import (
    is_platform_admin,
    is_platform_operator,
    user_has_capability,
)


class IsSuperUser(BasePermission):
    """Permite acesso apenas ao superuser da plataforma."""

    def has_permission(self, request, view):
        return is_platform_admin(request.user)


class HasCapability(BasePermission):
    """Permissão baseada em capability RBAC."""

    capability = ''

    def has_permission(self, request, view):
        cap = getattr(view, 'required_capability', None) or self.capability
        if not cap:
            return False
        return user_has_capability(request.user, cap)


class CanManageCompanies(HasCapability):
    capability = 'manage_companies'


class CanViewAudit(HasCapability):
    capability = 'view_audit'


class CanViewSecurity(HasCapability):
    capability = 'view_security'


class IsTenantAdmin(HasCapability):
    capability = 'manage_tenant'


class CanViewContacts(HasCapability):
    capability = 'view_contacts'


class CanManageLgpd(HasCapability):
    capability = 'manage_lgpd'


class IsGestor(BasePermission):
    """Permite acesso apenas a gestores de empresa."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_gestor
            and user.company_id
        )


class IsGestorOrSuperUser(BasePermission):
    """Gestor da empresa ou operador da plataforma (superuser/suporte)."""

    def has_permission(self, request, view):
        return user_has_capability(request.user, 'manage_tenant')


class IsAdmin(BasePermission):
    """Alias de compatibilidade para administração de tenant."""

    def has_permission(self, request, view):
        return IsGestorOrSuperUser().has_permission(request, view)


class IsAdminOrSupervisor(BasePermission):
    """Gestor, operador plataforma ou supervisor."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if is_platform_operator(user) or user.is_gestor:
            return True
        return user.is_supervisor
