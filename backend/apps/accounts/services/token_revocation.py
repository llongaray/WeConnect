"""Revogação de tokens JWT (blacklist) ao desativar usuário ou empresa."""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def revoke_user_tokens(user_id: int) -> int:
    """Coloca na blacklist todos os refresh tokens pendentes do usuário."""
    try:
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
    except ImportError:
        logger.warning('token_blacklist indisponível — revogação ignorada')
        return 0

    count = 0
    for outstanding in OutstandingToken.objects.filter(user_id=user_id):
        _, created = BlacklistedToken.objects.get_or_create(token=outstanding)
        if created:
            count += 1
    return count


def revoke_company_user_tokens(company_id: int) -> int:
    """Revoga sessões de todos os usuários da empresa."""
    total = 0
    for user_id in User.objects.filter(company_id=company_id).values_list('id', flat=True):
        total += revoke_user_tokens(user_id)
    return total
