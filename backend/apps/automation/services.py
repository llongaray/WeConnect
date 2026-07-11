from django.utils import timezone

from apps.chat.message_service import (
    _extract_external_id_from_result,
    _resolve_recipient,
)
from apps.chat.models import Conversation, Message
from apps.whatsapp.providers.factory import get_provider


def send_automated_message(conversation: Conversation, content: str) -> Message | None:
    """Envia mensagem de texto automática do chatbot (sem usuário autenticado)."""
    if not content or not content.strip():
        return None

    channel = conversation.channel
    recipient = _resolve_recipient(channel, conversation.contact)
    provider = get_provider(channel)

    message = Message.objects.create(
        conversation=conversation,
        direction=Message.Direction.OUTBOUND,
        message_type=Message.MessageType.TEXT,
        content=content.strip(),
        status=Message.DeliveryStatus.PENDING,
        sent_by=None,
    )

    try:
        result = provider.send_text(recipient, content.strip())
        external_id = _extract_external_id_from_result(channel, result)
        if external_id:
            message.external_id = external_id
        message.status = Message.DeliveryStatus.SENT
        message.save()
    except RuntimeError:
        message.status = Message.DeliveryStatus.FAILED
        message.save(update_fields=['status'])
        return message

    conversation.last_message_at = timezone.now()
    conversation.last_message_preview = content.strip()[:255]
    conversation.save(update_fields=['last_message_at', 'last_message_preview', 'updated_at'])

    from apps.chat.services import _broadcast_message

    _broadcast_message(message, conversation)
    return message
