import logging

import httpx
from django.conf import settings

from .models import DeepSeekConfig

logger = logging.getLogger(__name__)


class DeepSeekNotConnectedError(Exception):
    """DeepSeek não configurado ou desconectado."""


class DeepSeekAPIError(Exception):
    """Erro na chamada à API DeepSeek."""


def _get_api_key() -> str:
    config = DeepSeekConfig.get_singleton()
    if config.status != DeepSeekConfig.Status.CONNECTED or not config.api_key:
        raise DeepSeekNotConnectedError(
            'DeepSeek não está conectado. Configure o token em Inteligência Artificial → DeepSeek.',
        )
    return config.api_key


def chat_completion(
    messages: list[dict],
    model: str | None = None,
    response_format: dict | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Chama POST /v1/chat/completions e retorna o conteúdo da resposta."""
    api_key = _get_api_key()
    base_url = settings.DEEPSEEK_BASE_URL.rstrip('/')
    url = f'{base_url}/v1/chat/completions'
    model = model or settings.DEEPSEEK_MODEL

    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stream': False,
    }
    if response_format:
        payload['response_format'] = response_format

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        with httpx.Client(timeout=settings.DEEPSEEK_TIMEOUT) as client:
            response = client.post(url, headers=headers, json=payload)

        if response.status_code in (401, 403):
            raise DeepSeekAPIError('Token DeepSeek inválido ou expirado.')

        if response.status_code != 200:
            logger.error('DeepSeek API error %s: %s', response.status_code, response.text[:500])
            raise DeepSeekAPIError(f'Erro na API DeepSeek (HTTP {response.status_code}).')

        data = response.json()
        choices = data.get('choices', [])
        if not choices:
            raise DeepSeekAPIError('Resposta vazia da API DeepSeek.')

        content = choices[0].get('message', {}).get('content', '')
        if not content:
            raise DeepSeekAPIError('Conteúdo vazio na resposta DeepSeek.')

        return content

    except httpx.TimeoutException as exc:
        raise DeepSeekAPIError('Timeout ao chamar a API DeepSeek.') from exc
    except httpx.RequestError as exc:
        logger.exception('Erro de rede DeepSeek: %s', exc)
        raise DeepSeekAPIError(f'Falha de conexão: {exc}') from exc
