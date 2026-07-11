from django.db import models


class BotFlow(models.Model):
    """Fluxo do chatbot vinculado a um canal WhatsApp."""

    channel = models.OneToOneField(
        'whatsapp.Channel',
        on_delete=models.CASCADE,
        related_name='bot_flow',
    )
    name = models.CharField(max_length=255, default='Fluxo principal')
    is_active = models.BooleanField(default=False)
    definition = models.JSONField(default=dict, blank=True)
    start_node_id = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fluxo do chatbot'
        verbose_name_plural = 'Fluxos do chatbot'

    def __str__(self):
        return f'{self.name} — {self.channel.name}'


class ConversationBotState(models.Model):
    """Estado do chatbot em uma conversa."""

    class WaitingFor(models.TextChoices):
        NONE = 'none', 'Nenhum'
        YES_NO = 'yes_no', 'Sim ou Não'
        MENU = 'menu', 'Menu de opções'

    conversation = models.OneToOneField(
        'chat.Conversation',
        on_delete=models.CASCADE,
        related_name='bot_state',
    )
    flow = models.ForeignKey(
        BotFlow,
        on_delete=models.CASCADE,
        related_name='conversation_states',
    )
    current_node_id = models.CharField(max_length=64)
    waiting_for = models.CharField(
        max_length=20,
        choices=WaitingFor.choices,
        default=WaitingFor.NONE,
    )
    invalid_attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado do chatbot'
        verbose_name_plural = 'Estados do chatbot'

    def __str__(self):
        return f'BotState conv={self.conversation_id} node={self.current_node_id}'
