from rest_framework.permissions import BasePermission

from apps.accounts.services.capabilities import is_platform_operator
from apps.accounts.totp_service import user_requires_totp_setup
from apps.platform_chat.services import user_can_access_room


class IsPlatformChatOperator(BasePermission):
    """Apenas superuser ou suporte WeConnect com 2FA configurado."""

    message = 'Acesso restrito à equipe WeConnect.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user_requires_totp_setup(user):
            return False
        return is_platform_operator(user)


class CanAccessPlatformRoom(BasePermission):
    """Usuário pode acessar a sala solicitada."""

    def has_object_permission(self, request, view, obj):
        return user_can_access_room(request.user, obj)
