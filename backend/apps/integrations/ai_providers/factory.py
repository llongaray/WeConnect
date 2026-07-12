from .base import AINotConnectedError, AIProviderAdapter
from .providers import AnthropicProvider, DeepSeekProvider, GeminiProvider, OpenAIProvider

PROVIDER_TYPES = ('deepseek', 'openai', 'anthropic', 'gemini')

_ADAPTERS: dict[str, AIProviderAdapter] = {
    'deepseek': DeepSeekProvider(),
    'openai': OpenAIProvider(),
    'anthropic': AnthropicProvider(),
    'gemini': GeminiProvider(),
}


def get_provider_adapter(provider_type: str) -> AIProviderAdapter:
    adapter = _ADAPTERS.get(provider_type)
    if not adapter:
        raise ValueError(f'Provedor de IA desconhecido: {provider_type}')
    return adapter


def list_provider_types() -> list[str]:
    return list(PROVIDER_TYPES)
