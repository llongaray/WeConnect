import secrets
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    """Empresa tenant do SaaS WeConnect."""

    CODE_MIN_LENGTH = 6
    CODE_MAX_LENGTH = 8

    code = models.CharField(max_length=8, unique=True, editable=False)
    legal_name = models.CharField('razão social', max_length=255)
    trade_name = models.CharField('nome fantasia', max_length=255)
    cnpj = models.CharField(max_length=18, blank=True, default='')
    address = models.TextField('endereço', blank=True, default='')
    contact_email = models.EmailField('e-mail de contato', blank=True, default='')
    billing_email = models.EmailField('e-mail financeiro', blank=True, default='')
    contact_phone = models.CharField('telefone de contato', max_length=30, blank=True, default='')
    billing_phone = models.CharField('telefone financeiro', max_length=30, blank=True, default='')
    dpo_name = models.CharField('encarregado (DPO)', max_length=150, blank=True, default='')
    dpo_email = models.EmailField('e-mail do encarregado', blank=True, default='')
    data_retention_days = models.PositiveIntegerField(
        'retenção de dados (dias)',
        default=365,
        help_text='Prazo de retenção de mensagens e contatos inativos.',
    )
    is_active = models.BooleanField(default=True)
    max_supervisors = models.PositiveIntegerField(default=5)
    max_atendentes = models.PositiveIntegerField(default=20)
    max_teams = models.PositiveIntegerField(default=10)
    max_channels = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['trade_name']
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return f'{self.trade_name} ({self.code})'

    @classmethod
    def generate_unique_code(cls) -> str:
        """Gera código alfanumérico único para a empresa."""
        alphabet = string.ascii_uppercase + string.digits
        for length in range(cls.CODE_MIN_LENGTH, cls.CODE_MAX_LENGTH + 1):
            for _ in range(100):
                code = ''.join(secrets.choice(alphabet) for _ in range(length))
                if not cls.objects.filter(code=code).exists():
                    return code
        raise RuntimeError('Não foi possível gerar código único para a empresa.')

    def usage_summary(self) -> dict:
        """Contagem atual vs limites configurados."""
        users = User.objects.filter(company=self, is_superuser=False)
        return {
            'supervisors': users.filter(role=User.Role.SUPERVISOR).count(),
            'atendentes': users.filter(role=User.Role.ATENDENTE).count(),
            'gestores': users.filter(role=User.Role.GESTOR).count(),
            'teams': self.teams.filter(is_active=True).count(),
            'channels': self.channels.filter(is_active=True).count(),
            'limits': {
                'max_supervisors': self.max_supervisors,
                'max_atendentes': self.max_atendentes,
                'max_teams': self.max_teams,
                'max_channels': self.max_channels,
            },
        }


class User(AbstractUser):
    """Colaborador do sistema com perfil gestor, supervisor ou atendente."""

    class Role(models.TextChoices):
        GESTOR = 'gestor', 'Gestor'
        SUPERVISOR = 'supervisor', 'Supervisor'
        ATENDENTE = 'atendente', 'Atendente'

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATENDENTE,
    )
    cpf = models.CharField(max_length=14, blank=True, default='')
    phone = models.CharField('telefone', max_length=30, blank=True, default='')
    privacy_terms_accepted_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_gestor(self):
        return self.role == self.Role.GESTOR

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    @property
    def is_atendente(self):
        return self.role == self.Role.ATENDENTE

    @property
    def is_staff_member(self):
        return self.role in (self.Role.ATENDENTE, self.Role.SUPERVISOR)

    @property
    def is_admin(self):
        """Compatibilidade: gestor da empresa ou superuser da plataforma."""
        return self.is_superuser or self.is_gestor

    @property
    def can_manage_company(self):
        return self.is_superuser or self.is_gestor

    def __str__(self):
        return self.get_full_name() or self.username


class Team(models.Model):
    """Equipe de atendimento vinculada a uma empresa e a um ou mais canais."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='teams',
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    channels = models.ManyToManyField(
        'whatsapp.Channel',
        related_name='teams',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Equipe'
        verbose_name_plural = 'Equipes'
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name='unique_team_name_per_company'),
        ]

    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    """Membro de uma equipe com papel interno."""

    class MemberRole(models.TextChoices):
        SUPERVISOR = 'supervisor', 'Supervisor'
        ATENDENTE = 'atendente', 'Atendente'

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships',
    )
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.ATENDENTE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['team', 'user'], name='unique_team_member'),
        ]
        verbose_name = 'Membro da equipe'
        verbose_name_plural = 'Membros da equipe'

    def __str__(self):
        return f'{self.user} — {self.team} ({self.role})'


class AuditLog(models.Model):
    """Registro de auditoria para ações administrativas."""

    class Action(models.TextChoices):
        CREATE = 'create', 'Criação'
        UPDATE = 'update', 'Atualização'
        DELETE = 'delete', 'Exclusão'
        STATUS_CHANGE = 'status_change', 'Alteração de status'
        LIMIT_CHANGE = 'limit_change', 'Alteração de limites'
        LOGIN_FAILED = 'login_failed', 'Falha de login'
        LOGIN_BLOCKED = 'login_blocked', 'Login bloqueado'
        TOTP_ENABLED = 'totp_enabled', '2FA ativado'
        TOTP_DISABLED = 'totp_disabled', '2FA desativado'
        TOTP_FAILED = 'totp_failed', 'Falha 2FA'
        TOTP_SUCCESS = 'totp_success', '2FA validado'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=64, blank=True, default='')
    entity_label = models.CharField(max_length=255, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de auditoria'
        verbose_name_plural = 'Logs de auditoria'

    def __str__(self):
        return f'{self.action} {self.entity_type} #{self.entity_id}'


class SecurityEvent(models.Model):
    """Eventos de segurança para painel operacional."""

    class EventType(models.TextChoices):
        LOGIN_FAILED = 'login_failed', 'Falha de login'
        LOGIN_BLOCKED = 'login_blocked', 'Login bloqueado'
        WEBHOOK_REJECTED = 'webhook_rejected', 'Webhook rejeitado'
        RATE_LIMIT_HIT = 'rate_limit_hit', 'Rate limit excedido'
        TOTP_FAILED = 'totp_failed', 'Falha 2FA'
        TOTP_SUCCESS = 'totp_success', '2FA validado'
        IP_UNLOCKED = 'ip_unlocked', 'IP desbloqueado'
        IDOR_BLOCKED = 'idor_blocked', 'IDOR bloqueado'

    event_type = models.CharField(max_length=40, choices=EventType.choices)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=150, blank=True, default='')
    channel_id = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Evento de segurança'
        verbose_name_plural = 'Eventos de segurança'

    def __str__(self):
        return f'{self.event_type} — {self.ip_address or self.username}'


class UserSecurityProfile(models.Model):
    """Perfil de segurança do usuário (backup codes 2FA)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='security_profile',
    )
    backup_codes = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f'Segurança — {self.user.username}'


class TrustedDevice(models.Model):
    """Navegador/dispositivo confiável que pode pular 2FA até expirar."""

    device_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trusted_devices',
    )
    token_hash = models.CharField(max_length=128)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_used_at']
        verbose_name = 'Dispositivo confiável'
        verbose_name_plural = 'Dispositivos confiáveis'

    def __str__(self):
        return f'{self.user.username} — {self.device_uuid}'
