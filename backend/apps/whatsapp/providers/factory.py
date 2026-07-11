from apps.whatsapp.models import Channel

from .base import ChannelProvider
from .evolution import EvolutionProvider
from .meta_cloud import MetaCloudProvider


def get_provider(channel: Channel) -> ChannelProvider:
  """Retorna o provider adequado para o tipo de canal."""
  if channel.is_meta_cloud:
    return MetaCloudProvider(channel)
  if channel.is_evolution:
    return EvolutionProvider(channel)
  raise ValueError(f'Tipo de canal não suportado: {channel.channel_type}')
