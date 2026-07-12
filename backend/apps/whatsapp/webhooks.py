import json
import logging
import secrets

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.chat.services import ChatWebhookService

from .models import Channel
from .providers.evolution import normalize_qrcode_base64
from django.conf import settings

from .webhook_security import (
    check_webhook_rate_limit,
    log_webhook_auth_failure,
    reject_query_secret_in_production,
    validate_meta_hub_signature,
)

logger = logging.getLogger(__name__)


def _broadcast(event_type: str, data: dict, company_id: int):
  channel_layer = get_channel_layer()
  if not channel_layer:
    return
  payload = {'type': 'chat.event', 'event': event_type, 'data': data}
  try:
    async_to_sync(channel_layer.group_send)(f'chat_company_{company_id}', payload)
  except Exception:
    logger.exception('Falha ao enviar evento WebSocket: %s', event_type)


def _normalize_event(event: str) -> str:
  return event.upper().replace('.', '_').replace('-', '_')


def _validate_webhook_request(request, channel: Channel, *, require_header_secret: bool = False) -> JsonResponse | None:
  """Valida rate limit e secret. Retorna JsonResponse de erro ou None se ok."""
  if not check_webhook_rate_limit(request, channel.id):
    log_webhook_auth_failure(request, channel.id, 'rate_limit', company_id=channel.company_id)
    return JsonResponse({'error': 'Limite de requisições excedido'}, status=429)

  if reject_query_secret_in_production(request):
    log_webhook_auth_failure(request, channel.id, 'secret_query_proibido', company_id=channel.company_id)
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  if not channel.webhook_secret:
    log_webhook_auth_failure(request, channel.id, 'secret_nao_configurado', company_id=channel.company_id)
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  received = request.headers.get('X-Webhook-Secret', '')
  if not received and not require_header_secret:
    received = request.GET.get('secret', '')

  if require_header_secret and not request.headers.get('X-Webhook-Secret', ''):
    log_webhook_auth_failure(request, channel.id, 'secret_header_obrigatorio', company_id=channel.company_id)
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  if not secrets.compare_digest(received, channel.webhook_secret):
    log_webhook_auth_failure(request, channel.id, 'secret_invalido', company_id=channel.company_id)
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  return None


def _validate_meta_post_request(request, channel: Channel) -> JsonResponse | None:
  """Valida assinatura Meta e rate limit para POST."""
  if not check_webhook_rate_limit(request, channel.id):
    log_webhook_auth_failure(request, channel.id, 'rate_limit', company_id=channel.company_id)
    return JsonResponse({'error': 'Limite de requisições excedido'}, status=429)

  if reject_query_secret_in_production(request):
    log_webhook_auth_failure(request, channel.id, 'secret_query_proibido', company_id=channel.company_id)
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  app_secret = channel.credentials.get('app_secret') or settings.META_APP_SECRET
  if not validate_meta_hub_signature(request, app_secret):
    log_webhook_auth_failure(request, channel.id, 'meta_assinatura_invalida', company_id=channel.company_id)
    return JsonResponse({'error': 'Não autorizado'}, status=401)

  return None


@csrf_exempt
@require_http_methods(['POST'])
def evolution_webhook(request, channel_id: int):
  """Recebe eventos da Evolution API para um canal específico."""
  channel = get_object_or_404(Channel, pk=channel_id, is_active=True)
  if not channel.is_evolution:
    return JsonResponse({'error': 'Canal não é Evolution'}, status=400)

  auth_error = _validate_webhook_request(request, channel, require_header_secret=not settings.DEBUG)
  if auth_error:
    return auth_error

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
      ChatWebhookService.handle_evolution_send_message(channel, data)
    elif normalized == 'MESSAGES_UPDATE':
      ChatWebhookService.handle_evolution_messages_update(channel, data)
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
    if not check_webhook_rate_limit(request, channel.id):
      log_webhook_auth_failure(request, channel.id, 'rate_limit', company_id=channel.company_id)
      return JsonResponse({'error': 'Limite de requisições excedido'}, status=429)
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token', '')
    challenge = request.GET.get('hub.challenge')
    verify_token = channel.credentials.get('verify_token', '')
    if mode == 'subscribe' and secrets.compare_digest(token, verify_token):
      return HttpResponse(challenge, content_type='text/plain')
    log_webhook_auth_failure(request, channel.id, 'meta_verify_invalido', company_id=channel.company_id)
    return HttpResponse('Forbidden', status=403)

  auth_error = _validate_meta_post_request(request, channel)
  if auth_error:
    return auth_error

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


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def meta_messaging_webhook(request, channel_id: int):
  """Webhook Messenger/Instagram — verificação GET e mensagens POST."""
  channel = get_object_or_404(Channel, pk=channel_id, is_active=True)
  if not channel.is_meta_messaging:
    return JsonResponse({'error': 'Canal não é Meta Messaging'}, status=400)

  if request.method == 'GET':
    if not check_webhook_rate_limit(request, channel.id):
      log_webhook_auth_failure(request, channel.id, 'rate_limit', company_id=channel.company_id)
      return JsonResponse({'error': 'Limite de requisições excedido'}, status=429)
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token', '')
    challenge = request.GET.get('hub.challenge')
    verify_token = channel.credentials.get('verify_token', '')
    if mode == 'subscribe' and secrets.compare_digest(token, verify_token):
      return HttpResponse(challenge, content_type='text/plain')
    log_webhook_auth_failure(request, channel.id, 'meta_verify_invalido', company_id=channel.company_id)
    return HttpResponse('Forbidden', status=403)

  auth_error = _validate_meta_post_request(request, channel)
  if auth_error:
    return auth_error

  try:
    payload = json.loads(request.body)
  except json.JSONDecodeError:
    return JsonResponse({'error': 'JSON inválido'}, status=400)

  expected_object = 'instagram' if channel.is_meta_instagram else 'page'
  payload_object = payload.get('object', '')
  if payload_object and payload_object != expected_object:
    logger.warning(
      'Webhook Meta Messaging canal %s: object=%s esperado=%s',
      channel_id,
      payload_object,
      expected_object,
    )

  logger.info('Webhook Meta Messaging canal %s', channel_id)

  try:
    ChatWebhookService.handle_meta_messaging_webhook(channel, payload)
  except Exception:
    logger.exception('Erro ao processar webhook Meta Messaging')
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
  }, channel.company_id)


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
  }, channel.company_id)
