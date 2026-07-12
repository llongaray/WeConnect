from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


def validate_user_password(password: str) -> None:
    """Valida senha com mínimo de 10 caracteres e regras do Django."""
    if len(password) < 10:
        raise serializers.ValidationError('Senha deve ter no mínimo 10 caracteres.')
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
