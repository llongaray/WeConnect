from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Permite acesso apenas a administradores."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsAdminOrSupervisor(BasePermission):
    """Administradores e supervisores."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_supervisor)
        )
