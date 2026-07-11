from rest_framework.permissions import BasePermission

from .conversation_lifecycle import user_can_access_conversation, user_can_send_message


class IsConversationAccessible(BasePermission):
    """Verifica se o usuário pode acessar a conversa."""

    def has_object_permission(self, request, view, obj):
        return user_can_access_conversation(request.user, obj)


class CanSendMessage(BasePermission):
    """Verifica se o usuário pode enviar mensagem na conversa."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return user_can_access_conversation(request.user, obj)
        return user_can_send_message(request.user, obj)
