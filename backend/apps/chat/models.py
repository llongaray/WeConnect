from django.conf import settings
from django.db import models
from django.db.models import Q


class Contact(models.Model):
    """Contato WhatsApp vinculado a um canal."""

    channel = models.ForeignKey(
        'whatsapp.Channel',
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    external_id = models.CharField(max_length=100, db_index=True)
    phone = models.CharField(max_length=30, blank=True, default='')
    name = models.CharField(max_length=255, blank=True, default='')
    profile_pic_url = models.URLField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'phone']
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'external_id'],
                name='unique_contact_per_channel',
            ),
        ]

    def __str__(self):
        return self.name or self.phone or self.external_id


class Conversation(models.Model):
    """Conversa com um contato em um canal específico."""

    class Status(models.TextChoices):
        BOT = 'bot', 'Bot'
        OPEN = 'open', 'Aberta'
        CLOSED = 'closed', 'Fechada'

    channel = models.ForeignKey(
        'whatsapp.Channel',
        on_delete=models.CASCADE,
        related_name='conversations',
    )
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='conversations')
    team = models.ForeignKey(
        'accounts.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_conversations',
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    handoff_pending = models.BooleanField(
        default=False,
        help_text='Bot encaminhou para fila humana; impede reinício automático do chatbot.',
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_conversations',
    )
    unread_count = models.PositiveIntegerField(default=0)
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at', '-updated_at']
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'contact'],
                condition=Q(status__in=['open', 'bot']),
                name='unique_active_conversation',
            ),
        ]

    def __str__(self):
        return f'Conversa #{self.pk} — {self.contact}'


class ConversationEvent(models.Model):
    """Trilha de auditoria do ciclo de vida da conversa."""

    class EventType(models.TextChoices):
        ASSUMED = 'assumed', 'Assumida'
        TRANSFERRED = 'transferred', 'Transferida'
        RELEASED = 'released', 'Devolvida à fila'
        CLOSED = 'closed', 'Encerrada'
        REOPENED = 'reopened', 'Reaberta'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='events',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conversation_events',
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_events_from',
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_events_to',
    )
    note = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Evento de conversa'
        verbose_name_plural = 'Eventos de conversa'

    def __str__(self):
        return f'{self.event_type} — conversa #{self.conversation_id}'


class Message(models.Model):
    """Mensagem de uma conversa."""

    class Direction(models.TextChoices):
        INBOUND = 'in', 'Recebida'
        OUTBOUND = 'out', 'Enviada'

    class MessageType(models.TextChoices):
        TEXT = 'text', 'Texto'
        IMAGE = 'image', 'Imagem'
        AUDIO = 'audio', 'Áudio'
        VIDEO = 'video', 'Vídeo'
        DOCUMENT = 'document', 'Documento'
        STICKER = 'sticker', 'Sticker'
        OTHER = 'other', 'Outro'

    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        SENT = 'sent', 'Enviada'
        DELIVERED = 'delivered', 'Entregue'
        READ = 'read', 'Lida'
        FAILED = 'failed', 'Falhou'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    direction = models.CharField(max_length=10, choices=Direction.choices)
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    content = models.TextField(blank=True, default='')
    media_file = models.FileField(upload_to='messages/', blank=True, null=True)
    media_url = models.URLField(blank=True, default='')
    external_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.SENT,
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(
                fields=['conversation', 'created_at'],
                name='chat_messag_convers_abc123_idx',
            ),
        ]
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'

    def __str__(self):
        preview = (self.content or self.message_type)[:50]
        return f'{self.direction}: {preview}'


class Tag(models.Model):
    """Tag de funil vinculada à empresa."""

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='tags',
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='#00A3FF')
    funnel_order = models.PositiveIntegerField(
        default=0,
        help_text='0 = fora do funil; 1, 2, 3... definem a ordem das etapas.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['funnel_order', 'name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_tag_name_per_company',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.company_id})'


class ContactTag(models.Model):
    """Vínculo de tag com contato identificado por telefone/ID externo."""

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    contact_key = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_tags_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tag de contato'
        verbose_name_plural = 'Tags de contato'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'contact_key'],
                name='unique_tag_per_contact_key',
            ),
        ]

    def __str__(self):
        return f'{self.tag.name} → {self.contact_key}'
