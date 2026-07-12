"""Reautenticação step-up (senha ou TOTP) para operações sensíveis."""

from django.contrib.auth.hashers import check_password

from apps.accounts.models import User
from apps.accounts.totp_service import verify_totp_code


def verify_step_up(user: User, *, password: str = '', totp_code: str = '') -> bool:
    """Valida senha atual ou código TOTP antes de revelar segredos."""
    if password and check_password(password, user.password):
        return True
    if totp_code and verify_totp_code(user, totp_code):
        return True
    return False
