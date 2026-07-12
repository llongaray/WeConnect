import secrets

from django.db import models

from apps.core.fields import EncryptedJSONField, EncryptedCharField


class Channel(models.Model):
    """Canal omnichannel — WhatsApp, Messenger ou Instagram."""

    class ChannelType(models.TextChoices):
        EVOLUTION_NORMAL = 'evolution_normal', 'WhatsApp Normal'
        EVOLUTION_BUSINESS = 'evolution_business', 'WhatsApp Business'
        META_CLOUD = 'meta_cloud', 'API Oficial Meta'
        META_MESSENGER = 'meta_messenger', 'Facebook Messenger'
        META_INSTAGRAM = 'meta_instagram', 'Instagram DM'

    class Status(models.TextChoices):
        CONNECTING = 'connecting', 'Conectando'
        OPEN = 'open', 'Conectado'
        CLOSE = 'close', 'Desconectado'

    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=30, choices=ChannelType.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CLOSE,
    )
    phone = models.CharField(max_length=30, blank=True, default='')
    qrcode_base64 = models.TextField(blank=True, default='')
    credentials = EncryptedJSONField(blank=True, default='')
    webhook_secret = EncryptedCharField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='channels',
    )
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
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name='unique_channel_name_per_company'),
        ]

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
    def is_meta_messenger(self) -> bool:
        return self.channel_type == self.ChannelType.META_MESSENGER

    @property
    def is_meta_instagram(self) -> bool:
        return self.channel_type == self.ChannelType.META_INSTAGRAM

    @property
    def is_meta_messaging(self) -> bool:
        return self.channel_type in (
            self.ChannelType.META_MESSENGER,
            self.ChannelType.META_INSTAGRAM,
        )

    @property
    def is_meta_manual(self) -> bool:
        """Canais Meta configurados manualmente (BYOA)."""
        return self.is_meta_cloud or self.is_meta_messaging

    @property
    def evolution_instance_name(self) -> str:
        return self.credentials.get('evolution_instance_name', f'channel-{self.pk}')

    def ensure_webhook_secret(self) -> str:
        if not self.webhook_secret:
            self.webhook_secret = secrets.token_urlsafe(32)
            self.save(update_fields=['webhook_secret', 'updated_at'])
        return self.webhook_secret
