import logging
import re
import time
from typing import Any

import httpx
from django.conf import settings

from apps.whatsapp.models import Channel

from .base import ChannelProvider

logger = logging.getLogger(__name__)


def slugify_channel_name(name: str) -> str:
  slug = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower()).strip('-')
  return slug[:80] or 'canal'


class EvolutionProvider(ChannelProvider):
  """Provider Evolution API para WhatsApp Normal e Business."""

  WEBHOOK_EVENTS = [
    'QRCODE_UPDATED',
    'MESSAGES_UPSERT',
    'MESSAGES_UPDATE',
    'SEND_MESSAGE',
    'CONNECTION_UPDATE',
  ]

  @property
  def base_url(self) -> str:
    return settings.EVOLUTION_API_URL.rstrip('/')

  @property
  def api_key(self) -> str:
    return settings.EVOLUTION_API_KEY

  @property
  def instance_name(self) -> str:
    return self.channel.evolution_instance_name

  def webhook_url(self) -> str:
    base = settings.EVOLUTION_WEBHOOK_BASE_URL.rstrip('/')
    secret = self.channel.ensure_webhook_secret()
    return f'{base}/evolution/{self.channel.pk}/?secret={secret}'

  def _integration(self) -> str:
    # Normal e Business conectam via QR Code (Baileys / app no celular)
    return 'WHATSAPP-BAILEYS'

  def _headers(self) -> dict[str, str]:
    return {
      'apikey': self.api_key,
      'Content-Type': 'application/json',
    }

  def _request(
    self,
    method: str,
    path: str,
    timeout: float = 30.0,
    allow_not_found: bool = False,
    **kwargs,
  ) -> dict[str, Any]:
    url = f'{self.base_url}{path}'
    try:
      with httpx.Client(timeout=timeout) as client:
        response = client.request(method, url, headers=self._headers(), **kwargs)
        response.raise_for_status()
        if response.content:
          return response.json()
        return {}
    except httpx.HTTPStatusError as exc:
      if allow_not_found and exc.response.status_code == 404:
        return {}
      detail = exc.response.text.strip()
      logger.warning('Erro na Evolution API: %s %s — %s', method, path, detail[:500])
      raise RuntimeError(
        f'Erro na Evolution API ({exc.response.status_code}): {detail or exc}'
      ) from exc
    except httpx.HTTPError as exc:
      logger.warning('Erro na Evolution API: %s %s — %s', method, path, exc)
      raise RuntimeError(
        f'Não foi possível conectar à Evolution API em {self.base_url}. '
        'Verifique se o Docker está rodando.'
      ) from exc

  def configure_webhook(self) -> None:
    """Garante webhook com secret na Evolution (headers do /instance/create não persistem)."""
    payload: dict[str, Any] = {
      'webhook': {
        'enabled': True,
        'url': self.webhook_url(),
        'webhookByEvents': False,
        'webhookBase64': True,
        'events': self.WEBHOOK_EVENTS,
        'headers': {
          'X-Webhook-Secret': self.channel.webhook_secret,
        },
      },
    }
    self._request('POST', f'/webhook/set/{self.instance_name}', json=payload)

  def create_remote_instance(self) -> dict[str, Any]:
    payload: dict[str, Any] = {
      'instanceName': self.instance_name,
      'integration': self._integration(),
      'qrcode': True,
    }
    result = self._request('POST', '/instance/create', json=payload)
    self.configure_webhook()
    return result

  def connect(self, force_reset: bool = False) -> dict[str, Any]:
    if force_reset or not self._instance_exists():
      self.delete_remote_instance()
      time.sleep(1)
      result = self.create_remote_instance()
    else:
      self.configure_webhook()
      result = self._connect_and_wait_qrcode()
    return result

  def _connect_and_wait_qrcode(self, attempts: int = 12, wait_seconds: float = 4.0) -> dict[str, Any]:
    self._request(
      'POST',
      f'/instance/restart/{self.instance_name}',
      allow_not_found=True,
      timeout=60.0,
    )
    time.sleep(2)
    last_result: dict[str, Any] = {}
    for attempt in range(attempts):
      last_result = self._request(
        'GET',
        f'/instance/connect/{self.instance_name}',
        timeout=90.0,
      )
      if extract_qrcode_base64(last_result):
        return last_result
      if attempt < attempts - 1:
        time.sleep(wait_seconds)
    return last_result

  def disconnect(self) -> dict[str, Any]:
    return self._request(
      'DELETE',
      f'/instance/logout/{self.instance_name}',
      allow_not_found=True,
    )

  def get_status(self) -> dict[str, Any]:
    result = self._request(
      'GET',
      f'/instance/connectionState/{self.instance_name}',
      allow_not_found=True,
    )
    if not result:
      return {'instance': {'state': 'close'}}
    return result

  def _instance_exists(self) -> bool:
    result = self._request('GET', '/instance/fetchInstances')
    instances = result if isinstance(result, list) else result.get('instances', [])
    for item in instances:
      if item.get('name') == self.instance_name:
        return True
      nested = item.get('instance', {})
      if isinstance(nested, dict) and nested.get('instanceName') == self.instance_name:
        return True
    return False

  def send_text(self, number: str, text: str) -> dict[str, Any]:
    payload = {'number': number, 'text': text}
    return self._request('POST', f'/message/sendText/{self.instance_name}', json=payload)

  def send_media(
    self,
    number: str,
    mediatype: str,
    media: str,
    caption: str = '',
    file_name: str = '',
  ) -> dict[str, Any]:
    payload = {'number': number, 'mediatype': mediatype, 'media': media}
    if caption:
      payload['caption'] = caption
    if file_name:
      payload['fileName'] = file_name
    return self._request('POST', f'/message/sendMedia/{self.instance_name}', json=payload)

  def delete_remote_instance(self) -> None:
    self._request(
      'DELETE',
      f'/instance/logout/{self.instance_name}',
      allow_not_found=True,
    )
    self._request(
      'DELETE',
      f'/instance/delete/{self.instance_name}',
      allow_not_found=True,
    )


def normalize_qrcode_base64(value: str) -> str:
  """Garante prefixo data URI para exibição em <img>."""
  if not value or not isinstance(value, str):
    return ''
  value = value.strip()
  if value.startswith('data:image'):
    return value
  return f'data:image/png;base64,{value}'


def extract_qrcode_base64(result: dict) -> str:
  """Extrai base64 do QR Code em diferentes formatos da Evolution API v2."""
  if not isinstance(result, dict):
    return ''

  base64 = result.get('base64', '')
  if base64:
    return normalize_qrcode_base64(base64)

  qrcode = result.get('qrcode', result)
  if isinstance(qrcode, dict):
    base64 = qrcode.get('base64', '')
    if base64:
      return normalize_qrcode_base64(base64)

  instance_data = result.get('instance', {})
  if isinstance(instance_data, dict):
    nested = instance_data.get('qrcode', {})
    if isinstance(nested, dict):
      return normalize_qrcode_base64(nested.get('base64', ''))

  return ''


def extract_remote_state(state: dict) -> str:
  connection = state.get('instance', state)
  return connection.get('state', connection.get('status', ''))
