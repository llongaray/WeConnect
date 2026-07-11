import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.chat.services import ChatWebhookService

from .models import Channel
from .providers.evolution import normalize_qrcode_base64

logger = logging.getLogger(__name__)


def _broadcast(event_type: str, data: dict):
  channel_layer = get_channel_layer()
  if not channel_layer:
    return
  try:
    async_to_sync(channel_layer.group_send)(
      'chat_global',
      {'type': 'chat.event', 'event': event_type, 'data': data},
    )
  except Exception:
    logger.exception('Falha ao enviar evento WebSocket: %s', event_type)


def _normalize_event(event: str) -> str:
  return event.upper().replace('.', '_').replace('-', '_')


def _check_webhook_secret(channel: Channel, request) -> bool:
  if not channel.webhook_secret:
    return True
  received = (
    request.headers.get('X-Webhook-Secret', '')
    or request.GET.get('secret', '')
  )
  return received == channel.webhook_secret


@csrf_exempt
@require_http_methods(['POST'])
def evolution_webhook(request, channel_id: int):
  """Recebe eventos da Evolution API para um canal específico."""
  channel = get_object_or_404(Channel, pk=channel_id, is_active=True)
  if not channel.is_evolution:
    return JsonResponse({'error': 'Canal não é Evolution'}, status=400)

  if not _check_webhook_secret(channel, request):
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  try:
    payload = json.loads(request.body)
  except json.JSONDecodeError:
    return JsonResponse({'error': 'JSON inválido'}, status=400)

  event = payload.get('event', '')
  normalized = _normalize_event(event)
  data = payload.get('data', payload)

  logger.info('Webhook Evolution canal %s: %s', channel_id, event)

  try:
    if normalized == 'QRCODE_UPDATED':
      _handle_qrcode(channel, data)
    elif normalized == 'CONNECTION_UPDATE':
      _handle_connection(channel, data)
      if data.get('qrcode') or data.get('base64'):
        _handle_qrcode(channel, data)
    elif normalized == 'MESSAGES_UPSERT':
      ChatWebhookService.handle_evolution_messages_upsert(channel, data)
    elif normalized == 'SEND_MESSAGE':
      ChatWebhookService.handle_evolution_send_message(data)
    elif normalized == 'MESSAGES_UPDATE':
      ChatWebhookService.handle_evolution_messages_update(data)
  except Exception:
    logger.exception('Erro ao processar webhook %s', event)
    return JsonResponse({'error': 'Erro interno'}, status=500)

  return JsonResponse({'ok': True})


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def meta_webhook(request, channel_id: int):
  """Webhook Meta Cloud API — verificação GET e mensagens POST."""
  channel = get_object_or_404(Channel, pk=channel_id, is_active=True)
  if not channel.is_meta_cloud:
    return JsonResponse({'error': 'Canal não é Meta Cloud'}, status=400)

  if request.method == 'GET':
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    verify_token = channel.credentials.get('verify_token', '')
    if mode == 'subscribe' and token == verify_token:
      return HttpResponse(challenge, content_type='text/plain')
    return HttpResponse('Forbidden', status=403)

  if not _check_webhook_secret(channel, request):
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  try:
    payload = json.loads(request.body)
  except json.JSONDecodeError:
    return JsonResponse({'error': 'JSON inválido'}, status=400)

  logger.info('Webhook Meta canal %s', channel_id)

  try:
    ChatWebhookService.handle_meta_webhook(channel, payload)
  except Exception:
    logger.exception('Erro ao processar webhook Meta')
    return JsonResponse({'error': 'Erro interno'}, status=500)

  return JsonResponse({'ok': True})


def _handle_qrcode(channel: Channel, data: dict):
  qrcode = data.get('qrcode', data)
  base64 = ''
  if isinstance(qrcode, dict):
    base64 = qrcode.get('base64', '')
  elif isinstance(data, dict):
    base64 = data.get('base64', '')
  base64 = normalize_qrcode_base64(base64)
  if not base64:
    return
  channel.qrcode_base64 = base64
  channel.status = Channel.Status.CONNECTING
  channel.save(update_fields=['qrcode_base64', 'status', 'updated_at'])
  _broadcast('qrcode.updated', {
    'channel_id': channel.id,
    'qrcode_base64': base64,
  })


def _handle_connection(channel: Channel, data: dict):
  state = data.get('state', data.get('status', ''))
  if state == 'open':
    channel.status = Channel.Status.OPEN
    channel.qrcode_base64 = ''
  elif state in ('close', 'closed'):
    channel.status = Channel.Status.CLOSE
  else:
    channel.status = Channel.Status.CONNECTING

  phone = data.get('wuid', '') or data.get('phone', '')
  if phone and '@' in phone:
    phone = phone.split('@')[0]
  if phone:
    channel.phone = phone

  channel.save()
  _broadcast('connection.updated', {
    'channel_id': channel.id,
    'status': channel.status,
    'phone': channel.phone,
  })
