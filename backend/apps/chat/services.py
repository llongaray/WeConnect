import base64
import logging
import re
from dataclasses import dataclass
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.whatsapp.models import Channel

from .models import Contact, Conversation, Message

from .conversation_lifecycle import resolve_for_inbound

logger = logging.getLogger(__name__)


@dataclass
class NormalizedMessage:
  external_id: str
  external_contact_id: str
  contact_name: str
  phone: str
  message_type: str
  content: str
  raw_data: dict
  is_outbound_echo: bool = False


def _extract_phone(external_id: str) -> str:
  if not external_id:
    return ''
  phone = external_id.split('@')[0]
  return re.sub(r'\D', '', phone)


def _resolve_evolution_contact_ids(msg_data: dict) -> tuple[str, str]:
  """Resolve JID e telefone do contato (suporta @lid e remoteJidAlt)."""
  key = msg_data.get('key', {})
  remote_jid = key.get('remoteJid', '')
  remote_jid_alt = key.get('remoteJidAlt', '') or msg_data.get('remoteJidAlt', '')
  sender_pn = msg_data.get('senderPn', '') or key.get('senderPn', '')

  contact_jid = remote_jid
  if remote_jid.endswith('@lid'):
    if remote_jid_alt and not remote_jid_alt.endswith('@lid'):
      contact_jid = remote_jid_alt
    elif sender_pn:
      digits = re.sub(r'\D', '', sender_pn.split('@')[0])
      if digits:
        contact_jid = f'{digits}@s.whatsapp.net'

  phone = _extract_phone(contact_jid)
  if contact_jid.endswith('@lid'):
    phone = ''
  return contact_jid, phone


def _chat_company_group(company_id: int) -> str:
    return f'chat_company_{company_id}'


def _chat_superuser_group() -> str:
    return 'chat_superuser'


def _broadcast_chat_event(company_id: int, event: str, data: dict) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    payload = {
        'type': 'chat.event',
        'event': event,
        'data': data,
    }
    async_to_sync(channel_layer.group_send)(_chat_company_group(company_id), payload)
    async_to_sync(channel_layer.group_send)(_chat_superuser_group(), payload)


def broadcast_conversation_updated(conversation: Conversation):
  from .serializers import ConversationSerializer

  payload = ConversationSerializer(conversation).data
  company_id = conversation.channel.company_id
  _broadcast_chat_event(
      company_id,
      'conversation.updated',
      {
          'conversation': payload,
          'conversation_id': conversation.id,
      },
  )


def _broadcast_message(message: Message, conversation: Conversation):
  from .serializers import MessageSerializer

  payload = MessageSerializer(message).data
  company_id = conversation.channel.company_id
  _broadcast_chat_event(
      company_id,
      'message.new',
      {
          'message': payload,
          'conversation_id': conversation.id,
      },
  )


class ChatWebhookService:
  """Processa eventos de mensagem de múltiplos providers."""

  @classmethod
  def handle_evolution_messages_upsert(cls, channel: Channel, data):
    messages = data if isinstance(data, list) else data.get('messages', [data])
    for msg_data in messages:
      if not isinstance(msg_data, dict):
        continue
      normalized = cls.parse_evolution_message(msg_data)
      if normalized.is_outbound_echo:
        continue
      cls.save_inbound_message(channel, normalized)

  @classmethod
  def handle_evolution_send_message(cls, channel: Channel, data):
    messages = data if isinstance(data, list) else [data]
    for msg_data in messages:
      if not isinstance(msg_data, dict):
        continue
      normalized = cls.parse_evolution_message(msg_data)
      if normalized.external_id:
        Message.objects.filter(
          external_id=normalized.external_id,
          conversation__channel=channel,
        ).update(status=Message.DeliveryStatus.SENT)

  @classmethod
  def handle_evolution_messages_update(cls, channel: Channel, data):
    updates = data if isinstance(data, list) else [data]
    status_map = {
      0: Message.DeliveryStatus.PENDING,
      1: Message.DeliveryStatus.SENT,
      2: Message.DeliveryStatus.DELIVERED,
      3: Message.DeliveryStatus.READ,
      4: Message.DeliveryStatus.READ,
    }
    for update in updates:
      if not isinstance(update, dict):
        continue
      key = update.get('key', {})
      external_id = f"{key.get('remoteJid', '')}:{key.get('id', '')}"
      if not external_id or external_id == ':':
        continue
      ack = update.get('update', {}).get('status') or update.get('status')
      if ack is not None:
        new_status = status_map.get(int(ack), Message.DeliveryStatus.SENT)
        Message.objects.filter(
          external_id=external_id,
          conversation__channel=channel,
        ).update(status=new_status)

  @classmethod
  def handle_meta_webhook(cls, channel: Channel, payload: dict):
    for entry in payload.get('entry', []):
      for change in entry.get('changes', []):
        value = change.get('value', {})
        for msg_data in value.get('messages', []):
          normalized = cls.parse_meta_message(msg_data, value)
          cls.save_inbound_message(channel, normalized)
        for status_data in value.get('statuses', []):
          cls._handle_meta_status(status_data)

  @classmethod
  def handle_meta_messaging_webhook(cls, channel: Channel, payload: dict):
    """Processa webhooks Messenger (page) e Instagram (instagram)."""
    for entry in payload.get('entry', []):
      for event in entry.get('messaging', []):
        if 'message' not in event:
          continue
        normalized = cls.parse_meta_messaging_event(channel, event)
        if normalized:
          cls.save_inbound_message(channel, normalized)

  @classmethod
  def parse_meta_messaging_event(cls, channel: Channel, event: dict) -> NormalizedMessage | None:
    message = event.get('message', {})
    if message.get('is_echo'):
      return None

    sender = event.get('sender', {})
    sender_id = sender.get('id', '')
    if not sender_id:
      return None

    external_id = message.get('mid', '') or message.get('id', '')
    msg_type = Message.MessageType.TEXT
    content = ''

    if 'text' in message:
      content = message['text'].get('body', '')
    elif 'attachments' in message:
      attachments = message.get('attachments') or []
      if attachments:
        att_type = attachments[0].get('type', 'file')
        type_map = {
          'image': Message.MessageType.IMAGE,
          'video': Message.MessageType.VIDEO,
          'audio': Message.MessageType.AUDIO,
          'file': Message.MessageType.DOCUMENT,
        }
        msg_type = type_map.get(att_type, Message.MessageType.OTHER)
        content = attachments[0].get('payload', {}).get('url', '') or att_type

    return NormalizedMessage(
      external_id=external_id,
      external_contact_id=sender_id,
      contact_name=sender_id,
      phone='',
      message_type=msg_type,
      content=content,
      raw_data=event,
    )

  @classmethod
  def _handle_meta_status(cls, status_data: dict):
    external_id = status_data.get('id', '')
    if not external_id:
      return
    status_map = {
      'sent': Message.DeliveryStatus.SENT,
      'delivered': Message.DeliveryStatus.DELIVERED,
      'read': Message.DeliveryStatus.READ,
      'failed': Message.DeliveryStatus.FAILED,
    }
    new_status = status_map.get(status_data.get('status', ''), Message.DeliveryStatus.SENT)
    Message.objects.filter(external_id=external_id).update(status=new_status)

  @classmethod
  def parse_evolution_message(cls, msg_data: dict) -> NormalizedMessage:
    key = msg_data.get('key', {})
    remote_jid = key.get('remoteJid', '')
    msg_id = key.get('id', '')
    external_id = f'{remote_jid}:{msg_id}' if msg_id else ''
    contact_jid, phone = _resolve_evolution_contact_ids(msg_data)
    msg_type = cls._parse_evolution_message_type(msg_data)
    content = cls._extract_evolution_content(msg_data, msg_type)
    return NormalizedMessage(
      external_id=external_id,
      external_contact_id=contact_jid or remote_jid,
      contact_name=msg_data.get('pushName', '') or phone or _extract_phone(remote_jid),
      phone=phone,
      message_type=msg_type,
      content=content,
      raw_data=msg_data,
      is_outbound_echo=bool(key.get('fromMe', False)),
    )

  @classmethod
  def parse_meta_message(cls, msg_data: dict, value: dict) -> NormalizedMessage:
    wa_id = msg_data.get('from', '')
    external_id = msg_data.get('id', '')
    msg_type = msg_data.get('type', Message.MessageType.TEXT)
    valid_types = {choice.value for choice in Message.MessageType}
    content = ''
    if msg_type == 'text':
      content = msg_data.get('text', {}).get('body', '')
    elif msg_type in ('image', 'video', 'document'):
      content = msg_data.get(msg_type, {}).get('caption', '')

    contacts = value.get('contacts', [])
    name = contacts[0].get('profile', {}).get('name', wa_id) if contacts else wa_id

    return NormalizedMessage(
      external_id=external_id,
      external_contact_id=wa_id,
      contact_name=name,
      phone=wa_id,
      message_type=msg_type if msg_type in valid_types else Message.MessageType.OTHER,
      content=content,
      raw_data=msg_data,
    )

  @classmethod
  @transaction.atomic
  def save_inbound_message(cls, channel: Channel, normalized: NormalizedMessage):
    if not normalized.external_contact_id:
      return
    if normalized.external_contact_id.endswith('@g.us'):
      return

    contact, _ = Contact.objects.update_or_create(
      channel=channel,
      external_id=normalized.external_contact_id,
      defaults={
        'phone': normalized.phone,
        'name': normalized.contact_name or normalized.phone,
      },
    )

    conversation, created = resolve_for_inbound(channel, contact)

    if normalized.external_id and Message.objects.filter(external_id=normalized.external_id).exists():
      return

    message = Message.objects.create(
      conversation=conversation,
      direction=Message.Direction.INBOUND,
      message_type=normalized.message_type,
      content=normalized.content,
      external_id=normalized.external_id,
      status=Message.DeliveryStatus.DELIVERED,
    )

    if channel.is_evolution:
      cls._save_evolution_media(message, normalized.raw_data, normalized.message_type)

    conversation.unread_count += 1
    conversation.last_message_at = timezone.now()
    conversation.last_message_preview = (normalized.content or normalized.message_type)[:255]
    conversation.save(update_fields=['unread_count', 'last_message_at', 'last_message_preview', 'updated_at'])

    conversation_id = conversation.id
    message_id = message.id
    created_new = created

    def process_bot():
      from apps.automation.tasks import dispatch_chatbot_processing

      dispatch_chatbot_processing(conversation_id, message_id, force_restart=created_new)

    transaction.on_commit(process_bot)

    _broadcast_message(message, conversation)

  @classmethod
  def _parse_evolution_message_type(cls, msg_data: dict) -> str:
    message = msg_data.get('message', {})
    if message.get('conversation') or message.get('extendedTextMessage'):
      return Message.MessageType.TEXT
    if message.get('imageMessage'):
      return Message.MessageType.IMAGE
    if message.get('audioMessage'):
      return Message.MessageType.AUDIO
    if message.get('videoMessage'):
      return Message.MessageType.VIDEO
    if message.get('documentMessage'):
      return Message.MessageType.DOCUMENT
    if message.get('stickerMessage'):
      return Message.MessageType.STICKER
    return Message.MessageType.OTHER

  @classmethod
  def _extract_evolution_content(cls, msg_data: dict, msg_type: str) -> str:
    message = msg_data.get('message', {})
    if msg_type == Message.MessageType.TEXT:
      ext = message.get('extendedTextMessage', {})
      return message.get('conversation') or ext.get('text', '')
    if msg_type == Message.MessageType.IMAGE:
      return message.get('imageMessage', {}).get('caption', '')
    if msg_type == Message.MessageType.VIDEO:
      return message.get('videoMessage', {}).get('caption', '')
    if msg_type == Message.MessageType.DOCUMENT:
      doc = message.get('documentMessage', {})
      return doc.get('caption') or doc.get('fileName', '')
    return ''

  @classmethod
  def _save_evolution_media(cls, message: Message, msg_data: dict, msg_type: str):
    message_obj = msg_data.get('message', {})
    media_key_map = {
      Message.MessageType.IMAGE: 'imageMessage',
      Message.MessageType.AUDIO: 'audioMessage',
      Message.MessageType.VIDEO: 'videoMessage',
      Message.MessageType.DOCUMENT: 'documentMessage',
      Message.MessageType.STICKER: 'stickerMessage',
    }
    key = media_key_map.get(msg_type)
    if not key:
      return
    media = message_obj.get(key, {})
    url = media.get('url', '')
    if url:
      message.media_url = url
      message.save(update_fields=['media_url'])
      return
    b64 = msg_data.get('base64') or media.get('base64')
    if b64:
      if ',' in b64:
        b64 = b64.split(',', 1)[1]
      ext = 'jpg' if msg_type == Message.MessageType.IMAGE else 'bin'
      filename = f'{message.id}_{datetime.now().timestamp()}.{ext}'
      message.media_file.save(filename, ContentFile(base64.b64decode(b64)), save=True)
