import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0002_multi_channel'),
        ('whatsapp', '0002_channel'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotFlow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Fluxo principal', max_length=255)),
                ('is_active', models.BooleanField(default=False)),
                ('definition', models.JSONField(blank=True, default=dict)),
                ('start_node_id', models.CharField(blank=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('channel', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bot_flow', to='whatsapp.channel')),
            ],
            options={
                'verbose_name': 'Fluxo do chatbot',
                'verbose_name_plural': 'Fluxos do chatbot',
            },
        ),
        migrations.CreateModel(
            name='ConversationBotState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_node_id', models.CharField(max_length=64)),
                ('waiting_for', models.CharField(choices=[('none', 'Nenhum'), ('yes_no', 'Sim ou Não')], default='none', max_length=20)),
                ('invalid_attempts', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('conversation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bot_state', to='chat.conversation')),
                ('flow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversation_states', to='automation.botflow')),
            ],
            options={
                'verbose_name': 'Estado do chatbot',
                'verbose_name_plural': 'Estados do chatbot',
            },
        ),
    ]
