import logging

import httpx
from django.conf import settings
from django.utils import timezone

from .models import DeepSeekConfig

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str) -> str:
    """Mascara o token para exibição segura."""
    if not api_key:
        return ''
    if len(api_key) <= 8:
        return '••••••••'
    return f'{api_key[:3]}••••••••{api_key[-4:]}'


def get_deepseek_constants() -> dict:
    """Retorna constantes fixas da integração DeepSeek."""
    base_url = settings.DEEPSEEK_BASE_URL.rstrip('/')
    return {
        'base_url': base_url,
        'chat_model': settings.DEEPSEEK_MODEL,
        'reasoner_model': settings.DEEPSEEK_DASHBOARD_MODEL,
        'chat_endpoint': f'{base_url}/v1/chat/completions',
        'balance_endpoint': f'{base_url}/user/balance',
    }


def validate_deepseek_token(api_key: str) -> tuple[bool, str]:
    """
    Valida o token via GET /user/balance.
    Retorna (sucesso, mensagem_erro).
    """
    if not api_key or not api_key.strip():
        return False, 'Informe um API token válido.'

    base_url = settings.DEEPSEEK_BASE_URL.rstrip('/')
    url = f'{base_url}/user/balance'
    headers = {'Authorization': f'Bearer {api_key.strip()}'}
    timeout = settings.DEEPSEEK_TIMEOUT

    try:
        with httpx.Client(timeout=timeout) as client:
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


def build_config_response(config: DeepSeekConfig) -> dict:
    """Monta payload público da configuração (sem token completo)."""
    constants = get_deepseek_constants()
    return {
        **constants,
        'status': config.status,
        'api_key_set': bool(config.api_key),
        'api_key_masked': mask_api_key(config.api_key),
        'last_validated_at': config.last_validated_at,
        'last_error': config.last_error,
        'updated_at': config.updated_at,
    }


def save_deepseek_config(api_key: str) -> tuple[DeepSeekConfig, bool, str]:
    """
    Valida e persiste o token.
    Retorna (config, sucesso, mensagem_erro).
    """
    config = DeepSeekConfig.get_singleton()
    success, error_msg = validate_deepseek_token(api_key)

    config.api_key = api_key.strip()
    if success:
        config.status = DeepSeekConfig.Status.CONNECTED
        config.last_error = ''
        config.last_validated_at = timezone.now()
    else:
        config.status = DeepSeekConfig.Status.ERROR
        config.last_error = error_msg

    config.save()
    return config, success, error_msg
