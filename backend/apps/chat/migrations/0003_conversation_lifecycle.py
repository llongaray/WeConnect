# Gerado manualmente — ciclo de vida das conversas

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def assign_teams_to_conversations(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    Channel = apps.get_model('whatsapp', 'Channel')

    for conversation in Conversation.objects.select_related('channel').iterator():
        channel = Channel.objects.filter(pk=conversation.channel_id).first()
        if channel and channel.default_team_id:
            conversation.team_id = channel.default_team_id
            conversation.save(update_fields=['team_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_multi_channel'),
        ('accounts', '0003_teams_supervisor'),
        ('whatsapp', '0003_default_team'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='conversation',
            name='unique_conversation_per_channel_contact',
        ),
        migrations.AddField(
            model_name='conversation',
            name='assigned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='closed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='closed_conversations',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='handoff_pending',
            field=models.BooleanField(
                default=False,
                help_text='Bot encaminhou para fila humana; impede reinício automático do chatbot.',
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='team',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='conversations',
                to='accounts.team',
            ),
        ),
        migrations.RunPython(assign_teams_to_conversations, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.UniqueConstraint(
                condition=Q(status='open'),
                fields=('channel', 'contact'),
                name='unique_open_conversation',
            ),
        ),
        migrations.CreateModel(
            name='ConversationEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(
                    choices=[
                        ('assumed', 'Assumida'),
                        ('transferred', 'Transferida'),
                        ('released', 'Devolvida à fila'),
                        ('closed', 'Encerrada'),
                        ('reopened', 'Reaberta'),
                    ],
                    max_length=20,
                )),
                ('note', models.CharField(blank=True, default='', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='conversation_events',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('conversation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='events',
                    to='chat.conversation',
                )),
                ('from_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='conversation_events_from',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('to_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='conversation_events_to',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Evento de conversa',
                'verbose_name_plural': 'Eventos de conversa',
                'ordering': ['-created_at'],
            },
        ),
    ]
