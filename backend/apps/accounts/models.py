from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário do sistema com perfil admin, supervisor ou atendente."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        SUPERVISOR = 'supervisor', 'Supervisor'
        ATENDENTE = 'atendente', 'Atendente'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATENDENTE,
    )

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    @property
    def is_atendente(self):
        return self.role == self.Role.ATENDENTE

    @property
    def is_staff_member(self):
        return self.role in (self.Role.ATENDENTE, self.Role.SUPERVISOR)

    def __str__(self):
        return self.get_full_name() or self.username


class Team(models.Model):
    """Equipe de atendimento vinculada a um ou mais canais."""

    name = models.CharField(max_length=100, unique=True)
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
