import json
import os

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.core.exceptions import ImproperlyConfigured


def _build_fernet_suite() -> MultiFernet:
    primary = os.getenv('FIELD_ENCRYPTION_KEY', '')
    if not primary:
        raise ImproperlyConfigured('FIELD_ENCRYPTION_KEY não configurada.')
    keys = [Fernet(primary.encode() if isinstance(primary, str) else primary)]
    old = os.getenv('FIELD_ENCRYPTION_KEY_OLD', '')
    if old:
        keys.append(Fernet(old.encode() if isinstance(old, str) else old))
    return MultiFernet(keys)


def generate_encryption_key() -> str:
    """Gera chave Fernet para uso em FIELD_ENCRYPTION_KEY."""
    return Fernet.generate_key().decode()


def encrypt_json(data: dict) -> str:
    if not data:
        return ''
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
    return _build_fernet_suite().encrypt(payload).decode('utf-8')


def decrypt_json(value: str) -> dict:
    if not value:
        return {}
    try:
        raw = _build_fernet_suite().decrypt(value.encode('utf-8'))
        return json.loads(raw.decode('utf-8'))
    except (InvalidToken, json.JSONDecodeError, TypeError):
        return {}


def mask_secret(value: str, visible: int = 4) -> str:
    if not value:
        return ''
    if len(value) <= visible:
        return '*' * len(value)
    return '*' * (len(value) - visible) + value[-visible:]


def encrypt_text(value: str) -> str:
    if not value:
        return ''
    payload = value.encode('utf-8')
    return _build_fernet_suite().encrypt(payload).decode('utf-8')


def decrypt_text(value: str) -> str:
    if not value:
        return ''
    try:
        raw = _build_fernet_suite().decrypt(value.encode('utf-8'))
        return raw.decode('utf-8')
    except (InvalidToken, TypeError):
        return value
