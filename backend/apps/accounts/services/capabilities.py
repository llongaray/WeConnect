"""Matriz central de capabilities RBAC por papel."""

from __future__ import annotations

from apps.accounts.models import User

CAPABILITY_KEYS = (
    'manage_companies',
    'view_audit',
    'view_security',
    'manage_tenant',
    'manage_users',
    'manage_teams',
    'manage_channels',
    'manage_automation',
    'use_ai',
    'view_contacts',
    'manage_lgpd',
    'access_inbox',
    'transfer_conversations',
    'reopen_conversations',
)


def is_platform_admin(user: User | None) -> bool:
    return bool(user and user.is_authenticated and user.is_superuser)


def is_weconnect_support(user: User | None) -> bool:
    """Suporte técnico WeConnect: staff sem superuser."""
    return bool(user and user.is_authenticated and user.is_staff and not user.is_superuser)


def is_platform_operator(user: User | None) -> bool:
    """Superuser ou suporte técnico WeConnect."""
    return is_platform_admin(user) or is_weconnect_support(user)


def _empty_capabilities() -> dict[str, bool]:
    return {key: False for key in CAPABILITY_KEYS}


def get_user_capabilities(user: User | None) -> dict[str, bool]:
    """Retorna mapa de permissões efetivas do usuário."""
    caps = _empty_capabilities()
    if not user or not user.is_authenticated:
        return caps

    if is_platform_admin(user):
        return {key: True for key in CAPABILITY_KEYS}

    if is_weconnect_support(user):
        caps.update({
            'manage_companies': True,
            'view_audit': False,
            'view_security': False,
            'manage_tenant': True,
            'manage_users': True,
            'manage_teams': True,
            'manage_channels': True,
            'manage_automation': True,
            'use_ai': True,
            'view_contacts': True,
            'manage_lgpd': True,
            'access_inbox': True,
            'transfer_conversations': True,
            'reopen_conversations': True,
        })
        return caps

    if user.is_gestor and user.company_id:
        caps.update({
            'manage_tenant': True,
            'manage_users': True,
            'manage_teams': True,
            'manage_channels': True,
            'manage_automation': True,
            'use_ai': True,
            'view_contacts': True,
            'manage_lgpd': True,
            'access_inbox': True,
            'transfer_conversations': True,
            'reopen_conversations': True,
        })
        return caps

    if user.is_supervisor:
        caps.update({
            'view_contacts': True,
            'access_inbox': True,
            'transfer_conversations': True,
            'reopen_conversations': True,
        })
        return caps

    if user.is_atendente:
        caps.update({
            'access_inbox': True,
        })
        return caps

    return caps


def user_has_capability(user: User | None, capability: str) -> bool:
    return get_user_capabilities(user).get(capability, False)
