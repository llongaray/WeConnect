# Status bot — conversa com chatbot ativo não aparece como aberta no inbox

from django.db import migrations, models
from django.db.models import Q


def mark_bot_conversations(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    ConversationBotState = apps.get_model('automation', 'ConversationBotState')

    bot_ids = ConversationBotState.objects.values_list('conversation_id', flat=True)
    Conversation.objects.filter(
        id__in=bot_ids,
        status='open',
        handoff_pending=False,
        assigned_to__isnull=True,
    ).update(status='bot')


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_conversation_lifecycle'),
        ('automation', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='conversation',
            name='unique_open_conversation',
        ),
        migrations.AlterField(
            model_name='conversation',
            name='status',
            field=models.CharField(
                choices=[
                    ('bot', 'Bot'),
                    ('open', 'Aberta'),
                    ('closed', 'Fechada'),
                ],
                default='open',
                max_length=20,
            ),
        ),
        migrations.RunPython(mark_bot_conversations, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.UniqueConstraint(
                condition=Q(status__in=['open', 'bot']),
                fields=('channel', 'contact'),
                name='unique_active_conversation',
            ),
        ),
    ]
