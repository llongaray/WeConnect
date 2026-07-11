import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remote_jid', models.CharField(db_index=True, max_length=100, unique=True)),
                ('phone', models.CharField(blank=True, default='', max_length=30)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('profile_pic_url', models.URLField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Contato',
                'verbose_name_plural': 'Contatos',
                'ordering': ['name', 'phone'],
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('open', 'Aberta'), ('closed', 'Fechada')], default='open', max_length=20)),
                ('unread_count', models.PositiveIntegerField(default=0)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('last_message_preview', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_conversations', to=settings.AUTH_USER_MODEL)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='chat.contact')),
            ],
            options={
                'verbose_name': 'Conversa',
                'verbose_name_plural': 'Conversas',
                'ordering': ['-last_message_at', '-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(choices=[('in', 'Recebida'), ('out', 'Enviada')], max_length=10)),
                ('message_type', models.CharField(choices=[('text', 'Texto'), ('image', 'Imagem'), ('audio', 'Áudio'), ('video', 'Vídeo'), ('document', 'Documento'), ('sticker', 'Sticker'), ('other', 'Outro')], default='text', max_length=20)),
                ('content', models.TextField(blank=True, default='')),
                ('media_file', models.FileField(blank=True, null=True, upload_to='messages/')),
                ('media_url', models.URLField(blank=True, default='')),
                ('evolution_id', models.CharField(blank=True, db_index=True, default='', max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('sent', 'Enviada'), ('delivered', 'Entregue'), ('read', 'Lida'), ('failed', 'Falhou')], default='sent', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.conversation')),
                ('sent_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mensagem',
                'verbose_name_plural': 'Mensagens',
                'ordering': ['created_at'],
                'indexes': [models.Index(fields=['conversation', 'created_at'], name='chat_messag_convers_abc123_idx')],
            },
        ),
    ]
