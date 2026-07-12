from django.db import models


class DeepSeekConfig(models.Model):
    """Configuração DeepSeek por empresa."""

    class Status(models.TextChoices):
        CONNECTED = 'connected', 'Conectado'
        DISCONNECTED = 'disconnected', 'Desconectado'
        ERROR = 'error', 'Erro'

    company = models.OneToOneField(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='deepseek_config',
    )
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
        return f'DeepSeek — {self.company.trade_name} ({self.get_status_display()})'

    @classmethod
    def get_for_company(cls, company):
        obj, _ = cls.objects.get_or_create(company=company)
        return obj

    def get_api_key_plain(self) -> str:
        """Retorna token descriptografado (suporta legado em texto plano)."""
        from apps.core.encryption import decrypt_text

        raw = self.api_key or ''
        if not raw:
            return ''
        if raw.startswith('enc:'):
            return decrypt_text(raw[4:])
        return raw

    def set_api_key_plain(self, value: str) -> None:
        """Persiste token criptografado."""
        from apps.core.encryption import encrypt_text

        if not value or not value.strip():
            self.api_key = ''
            return
        self.api_key = f'enc:{encrypt_text(value.strip())}'


class AIProviderConfig(models.Model):
    """Canal de IA configurável por empresa (DeepSeek, OpenAI, Claude, Gemini)."""

    class ProviderType(models.TextChoices):
        DEEPSEEK = 'deepseek', 'DeepSeek'
        OPENAI = 'openai', 'ChatGPT'
        ANTHROPIC = 'anthropic', 'Claude'
        GEMINI = 'gemini', 'Gemini'

    class Status(models.TextChoices):
        CONNECTED = 'connected', 'Conectado'
        DISCONNECTED = 'disconnected', 'Desconectado'
        ERROR = 'error', 'Erro'

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='ai_providers',
    )
    provider_type = models.CharField(max_length=20, choices=ProviderType.choices)
    api_key = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISCONNECTED,
    )
    is_default = models.BooleanField(default=False)
    last_error = models.TextField(blank=True, default='')
    last_validated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Canal de IA'
        verbose_name_plural = 'Canais de IA'
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'provider_type'],
                name='uniq_ai_provider_per_company',
            ),
        ]

    def __str__(self):
        return f'{self.get_provider_type_display()} — {self.company.trade_name}'

    @classmethod
    def get_for_company(cls, company, provider_type: str):
        obj, _ = cls.objects.get_or_create(
            company=company,
            provider_type=provider_type,
        )
        return obj

    def get_api_key_plain(self) -> str:
        from apps.core.encryption import decrypt_text

        raw = self.api_key or ''
        if not raw:
            return ''
        if raw.startswith('enc:'):
            return decrypt_text(raw[4:])
        return raw

    def set_api_key_plain(self, value: str) -> None:
        from apps.core.encryption import encrypt_text

        if not value or not value.strip():
            self.api_key = ''
            return
        self.api_key = f'enc:{encrypt_text(value.strip())}'
