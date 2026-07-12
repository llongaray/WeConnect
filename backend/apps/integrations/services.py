import logging

import httpx
from django.conf import settings
from django.utils import timezone

from .ai_providers.factory import get_provider_adapter, list_provider_types
from .models import AIProviderConfig

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str) -> str:
    """Mascara o token para exibição segura."""
    if not api_key:
        return ''
    if len(api_key) <= 8:
        return '••••••••'
    return f'{api_key[:3]}••••••••{api_key[-4:]}'


def build_provider_response(config: AIProviderConfig) -> dict:
    """Monta payload público de um canal de IA."""
    adapter = get_provider_adapter(config.provider_type)
    constants = adapter.get_constants()
    plain_key = config.get_api_key_plain()
    return {
        'provider_type': config.provider_type,
        'label': constants['label'],
        **constants,
        'company_id': config.company_id,
        'status': config.status,
        'is_default': config.is_default,
        'api_key_set': bool(plain_key),
        'api_key_masked': mask_api_key(plain_key),
        'last_validated_at': config.last_validated_at,
        'last_error': config.last_error,
        'updated_at': config.updated_at,
        'configured': bool(plain_key) or config.status != AIProviderConfig.Status.DISCONNECTED,
    }


def build_catalog_response(company) -> list[dict]:
    """Lista todos os tipos de IA com estado atual da empresa."""
    existing = {
        item.provider_type: item
        for item in AIProviderConfig.objects.filter(company=company)
    }
    payload = []
    for provider_type in list_provider_types():
        config = existing.get(provider_type)
        if config:
            payload.append(build_provider_response(config))
        else:
            adapter = get_provider_adapter(provider_type)
            constants = adapter.get_constants()
            payload.append({
                'provider_type': provider_type,
                'label': constants['label'],
                **constants,
                'company_id': company.id,
                'status': AIProviderConfig.Status.DISCONNECTED,
                'is_default': False,
                'api_key_set': False,
                'api_key_masked': '',
                'last_validated_at': None,
                'last_error': '',
                'updated_at': None,
                'configured': False,
            })
    return payload


def save_provider_config(
    company,
    provider_type: str,
    api_key: str,
    *,
    is_default: bool | None = None,
) -> tuple[AIProviderConfig, bool, str]:
    """Valida e persiste credencial do canal de IA."""
    adapter = get_provider_adapter(provider_type)
    config = AIProviderConfig.get_for_company(company, provider_type)
    success, error_msg = adapter.validate_api_key(api_key)

    if success:
        config.set_api_key_plain(api_key)
        config.status = AIProviderConfig.Status.CONNECTED
        config.last_error = ''
        config.last_validated_at = timezone.now()
    else:
        if api_key and api_key.strip():
            config.set_api_key_plain(api_key)
        config.status = AIProviderConfig.Status.ERROR
        config.last_error = error_msg

    if is_default is True and success:
        AIProviderConfig.objects.filter(company=company, is_default=True).update(is_default=False)
        config.is_default = True
    elif is_default is False:
        config.is_default = False

    if success and not AIProviderConfig.objects.filter(company=company, is_default=True).exists():
        config.is_default = True

    config.save()
    return config, success, error_msg


def disconnect_provider(company, provider_type: str) -> AIProviderConfig:
    """Remove credencial e marca canal como desconectado."""
    config = AIProviderConfig.get_for_company(company, provider_type)
    config.api_key = ''
    config.status = AIProviderConfig.Status.DISCONNECTED
    config.last_error = ''
    config.last_validated_at = None
    if config.is_default:
        config.is_default = False
        config.save()
        fallback = (
            AIProviderConfig.objects.filter(company=company)
            .exclude(provider_type=provider_type)
            .exclude(api_key='')
            .filter(status=AIProviderConfig.Status.CONNECTED)
            .first()
        )
        if fallback:
            fallback.is_default = True
            fallback.save()
    else:
        config.save()
    return config


def resolve_default_provider(company, provider_type: str | None = None) -> AIProviderConfig:
    """Retorna canal conectado para geração de fluxos."""
    if provider_type:
        config = AIProviderConfig.objects.filter(
            company=company,
            provider_type=provider_type,
        ).first()
        if not config:
            config = AIProviderConfig.get_for_company(company, provider_type)
    else:
        config = AIProviderConfig.objects.filter(
            company=company,
            is_default=True,
            status=AIProviderConfig.Status.CONNECTED,
        ).first()
        if not config:
            config = (
                AIProviderConfig.objects.filter(
                    company=company,
                    status=AIProviderConfig.Status.CONNECTED,
                )
                .exclude(api_key='')
                .first()
            )
    if not config or config.status != AIProviderConfig.Status.CONNECTED:
        label = provider_type or 'IA'
        raise AINotConnectedError(
            f'Nenhum canal de IA conectado ({label}). Configure em Inteligência Artificial.',
        )
    plain = config.get_api_key_plain()
    if not plain:
        raise AINotConnectedError(
            'Canal de IA sem token válido. Configure em Inteligência Artificial.',
        )
    return config


def chat_completion_for_company(
    messages: list[dict],
    company,
    *,
    provider_type: str | None = None,
    response_format: dict | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    config = resolve_default_provider(company, provider_type)
    adapter = get_provider_adapter(config.provider_type)
    return adapter.chat_completion(
        messages,
        config.get_api_key_plain(),
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=temperature,
    )


class AINotConnectedError(Exception):
    """Canal de IA não configurado."""


class AIAPIError(Exception):
    """Erro na API de IA."""


# Compatibilidade com código legado DeepSeek
def get_deepseek_constants() -> dict:
    return get_provider_adapter('deepseek').get_constants()


def validate_deepseek_token(api_key: str) -> tuple[bool, str]:
    return get_provider_adapter('deepseek').validate_api_key(api_key)


def build_config_response(config) -> dict:
    if isinstance(config, AIProviderConfig):
        return build_provider_response(config)
    return build_provider_response(
        AIProviderConfig.get_for_company(config.company, 'deepseek'),
    )


def save_deepseek_config(company, api_key: str):
    return save_provider_config(company, 'deepseek', api_key)
