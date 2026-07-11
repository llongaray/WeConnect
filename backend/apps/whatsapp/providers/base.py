from abc import ABC, abstractmethod
from typing import Any

from apps.whatsapp.models import Channel


class ChannelProvider(ABC):
    """Interface comum para provedores de canal WhatsApp."""

    def __init__(self, channel: Channel):
        self.channel = channel

    @abstractmethod
    def create_remote_instance(self) -> dict[str, Any]:
        """Cria/configura a instância no provedor remoto."""

    @abstractmethod
    def connect(self, force_reset: bool = False) -> dict[str, Any]:
        """Inicia conexão (QR para Evolution, validação para Meta)."""

    @abstractmethod
    def disconnect(self) -> dict[str, Any]:
        """Desconecta o canal no provedor remoto."""

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Retorna status remoto do canal."""

    @abstractmethod
    def send_text(self, number: str, text: str) -> dict[str, Any]:
        """Envia mensagem de texto."""

    @abstractmethod
    def send_media(
        self,
        number: str,
        mediatype: str,
        media: str,
        caption: str = '',
        file_name: str = '',
    ) -> dict[str, Any]:
        """Envia mídia (base64 ou URL)."""

    @abstractmethod
    def delete_remote_instance(self) -> None:
        """Remove instância remota ao excluir canal."""
