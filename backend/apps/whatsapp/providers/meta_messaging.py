import logging
from typing import Any

import httpx
from django.conf import settings

from .base import ChannelProvider

logger = logging.getLogger(__name__)


class MetaMessagingProvider(ChannelProvider):
  """Provider base para Messenger e Instagram via Graph API (BYOA)."""

  def _credentials(self) -> dict[str, str]:
    return self.channel.credentials or {}

  @property
  def page_id(self) -> str:
    return self._credentials().get('page_id', '')

  @property
  def page_access_token(self) -> str:
    return self._credentials().get('page_access_token', '')

  @property
  def instagram_business_account_id(self) -> str:
    return self._credentials().get('instagram_business_account_id', '')

  @property
  def graph_url(self) -> str:
    version = settings.META_GRAPH_API_VERSION
    return f'https://graph.facebook.com/{version}'

  def _headers(self) -> dict[str, str]:
    return {
      'Authorization': f'Bearer {self.page_access_token}',
      'Content-Type': 'application/json',
    }

  def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
    if not self.page_id or not self.page_access_token:
      raise RuntimeError('Credenciais Meta incompletas (page_id e page_access_token).')

    url = f'{self.graph_url}{path}'
    try:
      with httpx.Client(timeout=30.0) as client:
        response = client.request(method, url, headers=self._headers(), **kwargs)
        response.raise_for_status()
        if response.content:
          return response.json()
        return {}
    except httpx.HTTPError as exc:
      logger.exception('Erro na Meta Messaging API: %s %s', method, path)
      raise RuntimeError(f'Erro na Meta Messaging API: {exc}') from exc

  def create_remote_instance(self) -> dict[str, Any]:
    return self.get_status()

  def connect(self, force_reset: bool = False) -> dict[str, Any]:
    return self.get_status()

  def disconnect(self) -> dict[str, Any]:
    return {'status': 'close'}

  def get_status(self) -> dict[str, Any]:
    page = self._request('GET', f'/{self.page_id}', params={'fields': 'name,id'})
    page_name = page.get('name', '')
    display = page_name

    creds = dict(self.channel.credentials or {})
    creds['page_name'] = page_name

    if self.channel.is_meta_instagram:
      if not self.instagram_business_account_id:
        raise RuntimeError('instagram_business_account_id é obrigatório para Instagram.')
      ig = self._request(
        'GET',
        f'/{self.instagram_business_account_id}',
        params={'fields': 'username,id'},
      )
      username = ig.get('username', '')
      creds['instagram_username'] = username
      display = f'@{username}' if username else page_name

      linked = self._request(
        'GET',
        f'/{self.page_id}',
        params={'fields': 'instagram_business_account'},
      )
      linked_id = (linked.get('instagram_business_account') or {}).get('id', '')
      if linked_id and linked_id != self.instagram_business_account_id:
        raise RuntimeError('Conta Instagram não está vinculada à Facebook Page informada.')

    self.channel.credentials = creds
    self.channel.save(update_fields=['credentials', 'updated_at'])

    return {
      'state': 'open' if page_name else 'close',
      'phone': display,
      'page_name': page_name,
      'instagram_username': creds.get('instagram_username', ''),
    }

  def _build_text_payload(self, recipient: str, text: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
      'recipient': {'id': recipient},
      'message': {'text': text},
    }
    if self.channel.is_meta_instagram:
      payload['messaging_type'] = 'RESPONSE'
    return payload

  def send_text(self, number: str, text: str) -> dict[str, Any]:
    payload = self._build_text_payload(number, text)
    return self._request('POST', f'/{self.page_id}/messages', json=payload)

  def send_media(
    self,
    number: str,
    mediatype: str,
    media: str,
    caption: str = '',
    file_name: str = '',
  ) -> dict[str, Any]:
    attachment_type = mediatype if mediatype in ('image', 'audio', 'video', 'file') else 'file'
    if attachment_type == 'document':
      attachment_type = 'file'

    message: dict[str, Any] = {
      'attachment': {
        'type': attachment_type,
        'payload': {'url': media, 'is_reusable': True},
      },
    }
    if caption:
      message['text'] = caption

    payload: dict[str, Any] = {
      'recipient': {'id': number},
      'message': message,
    }
    if self.channel.is_meta_instagram:
      payload['messaging_type'] = 'RESPONSE'

    return self._request('POST', f'/{self.page_id}/messages', json=payload)

  def delete_remote_instance(self) -> None:
    return None

  def webhook_url(self) -> str:
    base = settings.EVOLUTION_WEBHOOK_BASE_URL.rstrip('/')
    return f'{base}/meta-messaging/{self.channel.pk}/'
