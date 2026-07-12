from .services import AIAPIError, AINotConnectedError, chat_completion_for_company

# Compatibilidade legada
DeepSeekNotConnectedError = AINotConnectedError
DeepSeekAPIError = AIAPIError


def chat_completion(
    messages: list[dict],
    company,
    model: str | None = None,
    response_format: dict | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    provider_type: str | None = None,
) -> str:
    """Chama o canal de IA configurado e retorna o conteúdo da resposta."""
    return chat_completion_for_company(
        messages,
        company,
        provider_type=provider_type,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=temperature,
    )
