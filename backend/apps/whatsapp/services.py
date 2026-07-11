"""Compatibilidade — use apps.whatsapp.providers.factory.get_provider."""

from apps.whatsapp.providers.evolution import EvolutionProvider
from apps.whatsapp.providers.factory import get_provider

__all__ = ['EvolutionProvider', 'get_provider']
