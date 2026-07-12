# Migra dados existentes para empresa padrão

import secrets
import string

import django.db.models.deletion
from django.db import migrations, models


def generate_code(Company):
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(200):
        code = ''.join(secrets.choice(alphabet) for _ in range(6))
        if not Company.objects.filter(code=code).exists():
            return code
    raise RuntimeError('Não foi possível gerar código da empresa padrão.')


def forwards(apps, schema_editor):
    Company = apps.get_model('accounts', 'Company')
    User = apps.get_model('accounts', 'User')
    Team = apps.get_model('accounts', 'Team')
    Channel = apps.get_model('whatsapp', 'Channel')
    DeepSeekConfig = apps.get_model('integrations', 'DeepSeekConfig')

    if Company.objects.exists():
        company = Company.objects.first()
    else:
        company = Company.objects.create(
            code=generate_code(Company),
            legal_name='WeConnect Demo',
            trade_name='WeConnect Demo',
        )

    Team.objects.filter(company__isnull=True).update(company=company)
    Channel.objects.filter(company__isnull=True).update(company=company)

    User.objects.filter(is_superuser=True).update(company=None)
    User.objects.filter(role='admin').update(role='gestor')
    User.objects.filter(is_superuser=False, company__isnull=True).update(company=company)

    legacy = DeepSeekConfig.objects.filter(company__isnull=True).first()
    if legacy:
        DeepSeekConfig.objects.get_or_create(
            company=company,
            defaults={
                'api_key': legacy.api_key,
                'status': legacy.status,
                'last_error': legacy.last_error,
                'last_validated_at': legacy.last_validated_at,
            },
        )
        DeepSeekConfig.objects.filter(company__isnull=True).delete()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_saas_multicompany'),
        ('whatsapp', '0004_channel_company'),
        ('integrations', '0002_deepseek_company'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='team',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='teams',
                to='accounts.company',
            ),
        ),
    ]
