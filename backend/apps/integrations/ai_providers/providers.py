import logging

import httpx
from django.conf import settings

from .base import AIAPIError, AIProviderAdapter

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIProviderAdapter):
    provider_type = 'deepseek'

    def get_constants(self) -> dict:
        base_url = settings.DEEPSEEK_BASE_URL.rstrip('/')
        return {
            'label': 'DeepSeek',
            'base_url': base_url,
            'chat_model': settings.DEEPSEEK_MODEL,
            'reasoner_model': settings.DEEPSEEK_DASHBOARD_MODEL,
            'chat_endpoint': f'{base_url}/v1/chat/completions',
            'balance_endpoint': f'{base_url}/user/balance',
        }

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        if not api_key or not api_key.strip():
            return False, 'Informe um API token válido.'

        url = f'{settings.DEEPSEEK_BASE_URL.rstrip("/")}/user/balance'
        headers = {'Authorization': f'Bearer {api_key.strip()}'}
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT) as client:
                response = client.get(url, headers=headers)
            if response.status_code in (401, 403):
                return False, 'Token inválido ou sem permissão.'
            if response.status_code != 200:
                return False, f'Erro na API DeepSeek (HTTP {response.status_code}).'
            data = response.json()
            if data.get('is_available'):
                return True, ''
            return False, 'Conta DeepSeek sem saldo ou indisponível.'
        except httpx.TimeoutException:
            return False, 'Timeout ao conectar com a API DeepSeek.'
        except httpx.RequestError as exc:
            logger.exception('Erro de rede DeepSeek: %s', exc)
            return False, f'Falha de conexão: {exc}'
        except Exception as exc:
            logger.exception('Erro ao validar DeepSeek: %s', exc)
            return False, str(exc)

    def chat_completion(
        self,
        messages: list[dict],
        api_key: str,
        *,
        response_format: dict | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        url = f'{settings.DEEPSEEK_BASE_URL.rstrip("/")}/v1/chat/completions'
        payload = {
            'model': settings.DEEPSEEK_MODEL,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': False,
        }
        if response_format:
            payload['response_format'] = response_format
        return _openai_style_chat(url, api_key, payload)


class OpenAIProvider(AIProviderAdapter):
    provider_type = 'openai'

    def get_constants(self) -> dict:
        base_url = settings.OPENAI_BASE_URL.rstrip('/')
        return {
            'label': 'ChatGPT',
            'base_url': base_url,
            'chat_model': settings.OPENAI_MODEL,
            'reasoner_model': settings.OPENAI_MODEL,
            'chat_endpoint': f'{base_url}/v1/chat/completions',
            'balance_endpoint': f'{base_url}/v1/models',
        }

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        if not api_key or not api_key.strip():
            return False, 'Informe um API token válido.'
        url = f'{settings.OPENAI_BASE_URL.rstrip("/")}/v1/models'
        headers = {'Authorization': f'Bearer {api_key.strip()}'}
        return _validate_get(url, headers, 'OpenAI')

    def chat_completion(
        self,
        messages: list[dict],
        api_key: str,
        *,
        response_format: dict | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        url = f'{settings.OPENAI_BASE_URL.rstrip("/")}/v1/chat/completions'
        payload = {
            'model': settings.OPENAI_MODEL,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': False,
        }
        if response_format:
            payload['response_format'] = response_format
        return _openai_style_chat(url, api_key, payload)


class AnthropicProvider(AIProviderAdapter):
    provider_type = 'anthropic'

    def get_constants(self) -> dict:
        base_url = settings.ANTHROPIC_BASE_URL.rstrip('/')
        return {
            'label': 'Claude',
            'base_url': base_url,
            'chat_model': settings.ANTHROPIC_MODEL,
            'reasoner_model': settings.ANTHROPIC_MODEL,
            'chat_endpoint': f'{base_url}/v1/messages',
            'balance_endpoint': f'{base_url}/v1/models',
        }

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        if not api_key or not api_key.strip():
            return False, 'Informe um API token válido.'
        url = f'{settings.ANTHROPIC_BASE_URL.rstrip("/")}/v1/models'
        headers = {
            'x-api-key': api_key.strip(),
            'anthropic-version': settings.ANTHROPIC_API_VERSION,
        }
        return _validate_get(url, headers, 'Anthropic')

    def chat_completion(
        self,
        messages: list[dict],
        api_key: str,
        *,
        response_format: dict | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        system_parts = [m['content'] for m in messages if m.get('role') == 'system']
        chat_messages = [
            {'role': m['role'], 'content': m['content']}
            for m in messages
            if m.get('role') in ('user', 'assistant')
        ]
        payload = {
            'model': settings.ANTHROPIC_MODEL,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': chat_messages,
        }
        if system_parts:
            payload['system'] = '\n\n'.join(system_parts)
        if response_format and response_format.get('type') == 'json_object':
            payload['system'] = (
                (payload.get('system', '') + '\n\n' if payload.get('system') else '')
                + 'Responda somente com JSON válido, sem markdown.'
            ).strip()

        url = f'{settings.ANTHROPIC_BASE_URL.rstrip("/")}/v1/messages'
        headers = {
            'x-api-key': api_key,
            'anthropic-version': settings.ANTHROPIC_API_VERSION,
            'Content-Type': 'application/json',
        }
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code in (401, 403):
                raise AIAPIError('Token Anthropic inválido ou expirado.')
            if response.status_code != 200:
                raise AIAPIError(f'Erro na API Anthropic (HTTP {response.status_code}).')
            data = response.json()
            blocks = data.get('content', [])
            text = ''.join(block.get('text', '') for block in blocks if block.get('type') == 'text')
            if not text:
                raise AIAPIError('Conteúdo vazio na resposta Anthropic.')
            return text
        except httpx.TimeoutException as exc:
            raise AIAPIError('Timeout ao chamar a API Anthropic.') from exc
        except httpx.RequestError as exc:
            raise AIAPIError(f'Falha de conexão: {exc}') from exc


class GeminiProvider(AIProviderAdapter):
    provider_type = 'gemini'

    def get_constants(self) -> dict:
        base_url = settings.GEMINI_BASE_URL.rstrip('/')
        model = settings.GEMINI_MODEL
        return {
            'label': 'Gemini',
            'base_url': base_url,
            'chat_model': model,
            'reasoner_model': model,
            'chat_endpoint': f'{base_url}/v1beta/models/{model}:generateContent',
            'balance_endpoint': f'{base_url}/v1beta/models',
        }

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        if not api_key or not api_key.strip():
            return False, 'Informe um API token válido.'
        url = f'{settings.GEMINI_BASE_URL.rstrip("/")}/v1beta/models'
        params = {'key': api_key.strip()}
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT) as client:
                response = client.get(url, params=params)
            if response.status_code in (401, 403):
                return False, 'Token inválido ou sem permissão.'
            if response.status_code != 200:
                return False, f'Erro na API Gemini (HTTP {response.status_code}).'
            return True, ''
        except httpx.TimeoutException:
            return False, 'Timeout ao conectar com a API Gemini.'
        except httpx.RequestError as exc:
            return False, f'Falha de conexão: {exc}'
        except Exception as exc:
            return False, str(exc)

    def chat_completion(
        self,
        messages: list[dict],
        api_key: str,
        *,
        response_format: dict | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        contents = []
        for msg in messages:
            role = msg.get('role')
            if role == 'system':
                contents.append({
                    'role': 'user',
                    'parts': [{'text': f'[Sistema]\n{msg.get("content", "")}'}],
                })
                contents.append({'role': 'model', 'parts': [{'text': 'Entendido.'}]})
            elif role == 'user':
                contents.append({'role': 'user', 'parts': [{'text': msg.get('content', '')}]})
            elif role == 'assistant':
                contents.append({'role': 'model', 'parts': [{'text': msg.get('content', '')}]})

        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': max_tokens,
            },
        }
        if response_format and response_format.get('type') == 'json_object':
            payload['generationConfig']['responseMimeType'] = 'application/json'

        model = settings.GEMINI_MODEL
        url = f'{settings.GEMINI_BASE_URL.rstrip("/")}/v1beta/models/{model}:generateContent'
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT) as client:
                response = client.post(url, params={'key': api_key}, json=payload)
            if response.status_code in (401, 403):
                raise AIAPIError('Token Gemini inválido ou expirado.')
            if response.status_code != 200:
                raise AIAPIError(f'Erro na API Gemini (HTTP {response.status_code}).')
            data = response.json()
            candidates = data.get('candidates', [])
            if not candidates:
                raise AIAPIError('Resposta vazia da API Gemini.')
            parts = candidates[0].get('content', {}).get('parts', [])
            text = ''.join(part.get('text', '') for part in parts)
            if not text:
                raise AIAPIError('Conteúdo vazio na resposta Gemini.')
            return text
        except httpx.TimeoutException as exc:
            raise AIAPIError('Timeout ao chamar a API Gemini.') from exc
        except httpx.RequestError as exc:
            raise AIAPIError(f'Falha de conexão: {exc}') from exc


def _validate_get(url: str, headers: dict, label: str) -> tuple[bool, str]:
    try:
        with httpx.Client(timeout=settings.AI_TIMEOUT) as client:
            response = client.get(url, headers=headers)
        if response.status_code in (401, 403):
            return False, 'Token inválido ou sem permissão.'
        if response.status_code != 200:
            return False, f'Erro na API {label} (HTTP {response.status_code}).'
        return True, ''
    except httpx.TimeoutException:
        return False, f'Timeout ao conectar com a API {label}.'
    except httpx.RequestError as exc:
        return False, f'Falha de conexão: {exc}'
    except Exception as exc:
        return False, str(exc)


def _openai_style_chat(url: str, api_key: str, payload: dict) -> str:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    try:
        with httpx.Client(timeout=settings.AI_TIMEOUT) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code in (401, 403):
            raise AIAPIError('Token inválido ou expirado.')
        if response.status_code != 200:
            raise AIAPIError(f'Erro na API (HTTP {response.status_code}).')
        data = response.json()
        choices = data.get('choices', [])
        if not choices:
            raise AIAPIError('Resposta vazia da API.')
        content = choices[0].get('message', {}).get('content', '')
        if not content:
            raise AIAPIError('Conteúdo vazio na resposta.')
        return content
    except httpx.TimeoutException as exc:
        raise AIAPIError('Timeout ao chamar a API.') from exc
    except httpx.RequestError as exc:
        raise AIAPIError(f'Falha de conexão: {exc}') from exc
