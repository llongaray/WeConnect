# Generated manually — Fase 3 segurança

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auditlog_login_failed'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('login_failed', 'Falha de login'), ('login_blocked', 'Login bloqueado'), ('webhook_rejected', 'Webhook rejeitado'), ('rate_limit_hit', 'Rate limit excedido'), ('totp_failed', 'Falha 2FA'), ('totp_success', '2FA validado'), ('ip_unlocked', 'IP desbloqueado')], max_length=40)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('username', models.CharField(blank=True, default='', max_length=150)),
                ('channel_id', models.PositiveIntegerField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Evento de segurança',
                'verbose_name_plural': 'Eventos de segurança',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserSecurityProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backup_codes', models.JSONField(blank=True, default=list)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='security_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(choices=[('create', 'Criação'), ('update', 'Atualização'), ('delete', 'Exclusão'), ('status_change', 'Alteração de status'), ('limit_change', 'Alteração de limites'), ('login_failed', 'Falha de login'), ('login_blocked', 'Login bloqueado'), ('totp_enabled', '2FA ativado'), ('totp_disabled', '2FA desativado'), ('totp_failed', 'Falha 2FA'), ('totp_success', '2FA validado')], max_length=30),
        ),
    ]
