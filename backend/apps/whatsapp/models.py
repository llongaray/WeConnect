import secrets

from django.db import models


class Channel(models.Model):
    """Canal WhatsApp — Evolution (normal/business) ou Meta Cloud API."""

    class ChannelType(models.TextChoices):
        EVOLUTION_NORMAL = 'evolution_normal', 'WhatsApp Normal'
        EVOLUTION_BUSINESS = 'evolution_business', 'WhatsApp Business'
        META_CLOUD = 'meta_cloud', 'API Oficial Meta'

    class Status(models.TextChoices):
        CONNECTING = 'connecting', 'Conectando'
        OPEN = 'open', 'Conectado'
        CLOSE = 'close', 'Desconectado'

    name = models.CharField(max_length=100, unique=True)
    channel_type = models.CharField(max_length=30, choices=ChannelType.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CLOSE,
    )
    phone = models.CharField(max_length=30, blank=True, default='')
    qrcode_base64 = models.TextField(blank=True, default='')
    credentials = models.JSONField(default=dict, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    default_team = models.ForeignKey(
        'accounts.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_channels',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Canal'
        verbose_name_plural = 'Canais'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_channel_type_display()})'

    @property
    def is_evolution(self) -> bool:
        return self.channel_type in (
            self.ChannelType.EVOLUTION_NORMAL,
            self.ChannelType.EVOLUTION_BUSINESS,
        )

    @property
    def is_meta_cloud(self) -> bool:
        return self.channel_type == self.ChannelType.META_CLOUD

    @property
    def evolution_instance_name(self) -> str:
        return self.credentials.get('evolution_instance_name', f'channel-{self.pk}')

    def ensure_webhook_secret(self) -> str:
        if not self.webhook_secret:
            self.webhook_secret = secrets.token_urlsafe(32)
            self.save(update_fields=['webhook_secret', 'updated_at'])
        return self.webhook_secret
