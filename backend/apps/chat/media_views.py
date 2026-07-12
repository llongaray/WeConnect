import mimetypes
import os

from django.http import FileResponse, Http404
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.accounts.models import SecurityEvent
from apps.accounts.services.security_events import log_security_event
from apps.chat.conversation_lifecycle import user_can_access_conversation
from apps.chat.media_urls import verify_media_signature
from apps.chat.models import Message


class MessageMediaView(APIView):
    """Serve mídia de mensagem após validar assinatura ou acesso à conversa."""

    permission_classes = [AllowAny]

    def get(self, request, message_id: int):
        try:
            message = Message.objects.select_related(
                'conversation__channel__company',
            ).get(pk=message_id)
        except Message.DoesNotExist as exc:
            raise Http404 from exc

        exp = request.query_params.get('exp', '')
        sig = request.query_params.get('sig', '')
        uid = request.query_params.get('uid', '')
        if verify_media_signature(message_id, exp, sig, uid):
            if uid and (not request.user.is_authenticated or str(request.user.id) != uid):
                raise Http404
            return self._file_response(message)

        user = request.user
        if user.is_authenticated and user_can_access_conversation(user, message.conversation):
            return self._file_response(message)

        if user.is_authenticated:
            log_security_event(
                SecurityEvent.EventType.IDOR_BLOCKED,
                ip_address=request.META.get('REMOTE_ADDR'),
                username=user.username,
                company=message.conversation.channel.company,
                metadata={'resource': 'message_media', 'message_id': message_id},
            )
        raise Http404

    def _file_response(self, message: Message) -> FileResponse:
        if not message.media_file:
            raise Http404
        content_type, _ = mimetypes.guess_type(message.media_file.name)
        filename = os.path.basename(message.media_file.name)
        response = FileResponse(
            message.media_file.open('rb'),
            content_type=content_type or 'application/octet-stream',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
