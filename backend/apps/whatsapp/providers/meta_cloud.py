import logging
from typing import Any

import httpx
from django.conf import settings

from .base import ChannelProvider

logger = logging.getLogger(__name__)


class MetaCloudProvider(ChannelProvider):
  """Provider Meta Cloud API (WhatsApp Business Platform)."""

  def _credentials(self) -> dict[str, str]:
    return self.channel.credentials or {}

  @property
  def phone_number_id(self) -> str:
    return self._credentials().get('phone_number_id', '')

  @property
  def access_token(self) -> str:
    return self._credentials().get('access_token', '')

  @property
  def graph_url(self) -> str:
    version = settings.META_GRAPH_API_VERSION
    return f'https://graph.facebook.com/{version}'

  def _headers(self) -> dict[str, str]:
    return {
      'Authorization': f'Bearer {self.access_token}',
      'Content-Type': 'application/json',
    }

  def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
    if not self.phone_number_id or not self.access_token:
      raise RuntimeError('Credenciais Meta incompletas (phone_number_id e access_token).')

    url = f'{self.graph_url}{path}'
    try:
      with httpx.Client(timeout=30.0) as client:
        response = client.request(method, url, headers=self._headers(), **kwargs)
        response.raise_for_status()
        if response.content:
          return response.json()
        return {}
    except httpx.HTTPError as exc:
      logger.exception('Erro na Meta Cloud API: %s %s', method, path)
      raise RuntimeError(f'Erro na Meta Cloud API: {exc}') from exc

  def create_remote_instance(self) -> dict[str, Any]:
    # Meta não cria instância remota — valida credenciais
    return self.get_status()

  def connect(self, force_reset: bool = False) -> dict[str, Any]:
    return self.get_status()

  def disconnect(self) -> dict[str, Any]:
    return {'status': 'close'}

  def get_status(self) -> dict[str, Any]:
    result = self._request('GET', f'/{self.phone_number_id}')
    display = result.get('display_phone_number', '')
    phone = ''.join(ch for ch in display if ch.isdigit())
    verified = result.get('verified_name', '')
    return {
      'state': 'open' if phone else 'close',
      'phone': phone,
      'verified_name': verified,
    }

  def send_text(self, number: str, text: str) -> dict[str, Any]:
    payload = {
      'messaging_product': 'whatsapp',
      'to': number,
      'type': 'text',
      'text': {'body': text},
    }
    return self._request('POST', f'/{self.phone_number_id}/messages', json=payload)

  def send_media(
    self,
    number: str,
    mediatype: str,
    media: str,
    caption: str = '',
    file_name: str = '',
  ) -> dict[str, Any]:
    # Suporte básico: mídia via link público (base64 exige upload prévio na fase 2)
    media_type = mediatype if mediatype in ('image', 'audio', 'video', 'document') else 'document'
    media_obj: dict[str, Any] = {'link': media}
    if caption and media_type in ('image', 'video', 'document'):
      media_obj['caption'] = caption
    if file_name and media_type == 'document':
      media_obj['filename'] = file_name

    payload = {
      'messaging_product': 'whatsapp',
      'to': number,
      'type': media_type,
      media_type: media_obj,
    }
    return self._request('POST', f'/{self.phone_number_id}/messages', json=payload)

  def delete_remote_instance(self) -> None:
    # Meta não remove instância via API nesta fase
    return None

  def webhook_url(self) -> str:
    base = settings.EVOLUTION_WEBHOOK_BASE_URL.rstrip('/')
    return f'{base}/meta/{self.channel.pk}/'
