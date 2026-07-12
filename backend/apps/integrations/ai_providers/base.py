from abc import ABC, abstractmethod


class AIProviderError(Exception):
    """Erro genérico de provedor de IA."""


class AINotConnectedError(AIProviderError):
    """Provedor não configurado ou desconectado."""


class AIAPIError(AIProviderError):
    """Erro na chamada à API do provedor."""


class AIProviderAdapter(ABC):
    """Interface comum para DeepSeek, OpenAI, Anthropic e Gemini."""

    provider_type: str

    @abstractmethod
    def get_constants(self) -> dict:
        """Metadados públicos exibidos no frontend."""

    @abstractmethod
    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        """Valida credencial. Retorna (sucesso, mensagem_erro)."""

    @abstractmethod
    def chat_completion(
        self,
        messages: list[dict],
        api_key: str,
        *,
        response_format: dict | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Executa chat e retorna conteúdo textual da resposta."""
