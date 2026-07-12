# Canais de IA por empresa

import django.db.models.deletion
from django.db import migrations, models


def migrate_deepseek_configs(apps, schema_editor):
    DeepSeekConfig = apps.get_model('integrations', 'DeepSeekConfig')
    AIProviderConfig = apps.get_model('integrations', 'AIProviderConfig')
    for old in DeepSeekConfig.objects.exclude(company_id=None):
        AIProviderConfig.objects.get_or_create(
            company_id=old.company_id,
            provider_type='deepseek',
            defaults={
                'api_key': old.api_key,
                'status': old.status,
                'last_error': old.last_error,
                'last_validated_at': old.last_validated_at,
                'is_default': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_saas_multicompany'),
        ('integrations', '0002_deepseek_company'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIProviderConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_type', models.CharField(
                    choices=[
                        ('deepseek', 'DeepSeek'),
                        ('openai', 'ChatGPT'),
                        ('anthropic', 'Claude'),
                        ('gemini', 'Gemini'),
                    ],
                    max_length=20,
                )),
                ('api_key', models.CharField(blank=True, default='', max_length=255)),
                ('status', models.CharField(
                    choices=[
                        ('connected', 'Conectado'),
                        ('disconnected', 'Desconectado'),
                        ('error', 'Erro'),
                    ],
                    default='disconnected',
                    max_length=20,
                )),
                ('is_default', models.BooleanField(default=False)),
                ('last_error', models.TextField(blank=True, default='')),
                ('last_validated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_providers',
                    to='accounts.company',
                )),
            ],
            options={
                'verbose_name': 'Canal de IA',
                'verbose_name_plural': 'Canais de IA',
            },
        ),
        migrations.AddConstraint(
            model_name='aiproviderconfig',
            constraint=models.UniqueConstraint(
                fields=('company', 'provider_type'),
                name='uniq_ai_provider_per_company',
            ),
        ),
        migrations.RunPython(migrate_deepseek_configs, migrations.RunPython.noop),
    ]
