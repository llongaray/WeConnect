from django.db import models


class DeepSeekConfig(models.Model):
    """Configuração global da integração DeepSeek (singleton)."""

    class Status(models.TextChoices):
        CONNECTED = 'connected', 'Conectado'
        DISCONNECTED = 'disconnected', 'Desconectado'
        ERROR = 'error', 'Erro'

    api_key = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISCONNECTED,
    )
    last_error = models.TextField(blank=True, default='')
    last_validated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração DeepSeek'
        verbose_name_plural = 'Configurações DeepSeek'

    def __str__(self):
        return f'DeepSeek ({self.get_status_display()})'

    @classmethod
    def get_singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
