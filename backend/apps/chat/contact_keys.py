"""Chave estável de contato para tags persistentes por número/identificador."""

import re

from .models import Contact


def normalize_contact_key(value: str) -> str:
  """Normaliza telefone removendo caracteres não numéricos."""
  return re.sub(r'\D', '', value or '')


def resolve_contact_key(contact: Contact) -> str:
  """Define a chave usada para vincular tags ao contato."""
  phone_key = normalize_contact_key(contact.phone)
  if phone_key:
    return phone_key
  external = (contact.external_id or '').strip()
  if external:
    return external
  return str(contact.pk)
