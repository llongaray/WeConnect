from rest_framework.exceptions import ValidationError

from apps.accounts.models import Company, User


def assert_company_can_add(company: Company, resource: str) -> None:
    """Valida se a empresa ainda pode adicionar o recurso solicitado."""
    usage = company.usage_summary()
    limits = usage['limits']

    checks = {
        'supervisor': (
            usage['supervisors'],
            limits['max_supervisors'],
            'supervisores',
        ),
        'atendente': (
            usage['atendentes'],
            limits['max_atendentes'],
            'atendentes',
        ),
        'team': (
            usage['teams'],
            limits['max_teams'],
            'equipes',
        ),
        'channel': (
            usage['channels'],
            limits['max_channels'],
            'canais',
        ),
    }

    if resource not in checks:
        raise ValidationError({'detail': f'Recurso inválido: {resource}'})

    current, maximum, label = checks[resource]
    if current >= maximum:
        raise ValidationError({
            'detail': f'Limite de {label} atingido ({current}/{maximum}).',
        })


def assert_can_create_user_role(company: Company, role: str) -> None:
    """Valida limite antes de criar colaborador com o papel informado."""
    if role == User.Role.SUPERVISOR:
        assert_company_can_add(company, 'supervisor')
    elif role == User.Role.ATENDENTE:
        assert_company_can_add(company, 'atendente')
