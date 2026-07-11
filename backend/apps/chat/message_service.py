import base64

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.whatsapp.providers.factory import get_provider

from .conversation_lifecycle import user_can_send_message
from .models import Conversation, Message


def _extract_external_id_from_result(channel, result: dict) -> str:
  if channel.is_meta_cloud:
    messages = result.get('messages', [])
    if messages:
      return messages[0].get('id', '')
    return ''

  key = result.get('key', {})
  external_id = f"{key.get('remoteJid', '')}:{key.get('id', '')}"
  return external_id if external_id != ':' else ''


def _resolve_recipient(channel, contact) -> str:
  """Define destinatário para envio conforme o provider."""
  external_id = contact.external_id or ''
  if channel.is_evolution:
    if external_id.endswith('@lid'):
      return external_id
    if external_id.endswith('@s.whatsapp.net'):
      return external_id.split('@')[0]
  if contact.phone:
    if channel.is_evolution and '@' not in external_id and len(contact.phone) >= 14:
      return f'{contact.phone}@lid'
    return contact.phone
  return external_id.split('@')[0]


def _format_agent_whatsapp_text(user, content: str) -> str:
    """Formata texto para WhatsApp com nome do atendente em negrito."""
    display = (user.get_full_name() or '').strip() or user.username
    body = (content or '').strip()
    return f'*{display}*\n{body}' if body else f'*{display}*'


def send_outbound_message(user, conversation: Conversation, validated_data: dict, *, force: bool = False) -> Message:
  if not force and not user_can_send_message(user, conversation):
    raise PermissionDenied('Você não pode enviar mensagens nesta conversa.')

  content = validated_data.get('content', '')
  message_type = validated_data.get('message_type', Message.MessageType.TEXT)
  media_file = validated_data.get('media')

  if message_type == Message.MessageType.TEXT and not content.strip():
    raise ValidationError({'content': 'Conteúdo obrigatório para mensagem de texto.'})

  if message_type != Message.MessageType.TEXT and not media_file:
    raise ValidationError({'media': 'Arquivo de mídia obrigatório.'})

  channel = conversation.channel
  recipient = _resolve_recipient(channel, conversation.contact)
  provider = get_provider(channel)

  message = Message.objects.create(
    conversation=conversation,
    direction=Message.Direction.OUTBOUND,
    message_type=message_type,
    content=content,
    status=Message.DeliveryStatus.PENDING,
    sent_by=user,
  )

  try:
    if message_type == Message.MessageType.TEXT:
      whatsapp_text = _format_agent_whatsapp_text(user, content)
      result = provider.send_text(recipient, whatsapp_text)
    else:
      message.media_file = media_file
      message.save(update_fields=['media_file'])
      media_file.seek(0)
      b64 = base64.b64encode(media_file.read()).decode('utf-8')
      mediatype = message_type
      if mediatype == Message.MessageType.STICKER:
        mediatype = 'image'
      caption = _format_agent_whatsapp_text(user, content) if content.strip() else ''
      result = provider.send_media(
        number=recipient,
        mediatype=mediatype,
        media=b64,
        caption=caption,
        file_name=getattr(media_file, 'name', 'arquivo'),
      )

    external_id = _extract_external_id_from_result(channel, result)
    if external_id:
      message.external_id = external_id
    message.status = Message.DeliveryStatus.SENT
    message.save()

  except RuntimeError as exc:
    message.status = Message.DeliveryStatus.FAILED
    message.save(update_fields=['status'])
    raise ValidationError({'detail': str(exc)}) from exc

  conversation.last_message_at = timezone.now()
  conversation.last_message_preview = (content or message_type)[:255]
  conversation.save(update_fields=['last_message_at', 'last_message_preview', 'updated_at'])

  return message
