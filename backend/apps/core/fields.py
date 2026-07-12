from django.db import models

from .encryption import decrypt_json, decrypt_text, encrypt_json, encrypt_text


class EncryptedJSONField(models.TextField):
    """Campo JSON criptografado em repouso via Fernet."""

    description = 'JSON criptografado'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return {}
        if isinstance(value, dict):
            return value
        return decrypt_json(value)

    def to_python(self, value):
        if value is None or value == '':
            return {}
        if isinstance(value, dict):
            return value
        return decrypt_json(value)

    def get_prep_value(self, value):
        if value is None:
            return ''
        if not isinstance(value, dict):
            return ''
        if not value:
            return ''
        return encrypt_json(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs


class EncryptedCharField(models.TextField):
    """Campo texto criptografado em repouso via Fernet."""

    description = 'Texto criptografado'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return ''
        return decrypt_text(value)

    def to_python(self, value):
        if value is None:
            return ''
        if isinstance(value, str) and value.startswith('gAAAA'):
            return decrypt_text(value)
        return value or ''

    def get_prep_value(self, value):
        if not value:
            return ''
        if isinstance(value, str) and value.startswith('gAAAA'):
            return value
        return encrypt_text(str(value))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
