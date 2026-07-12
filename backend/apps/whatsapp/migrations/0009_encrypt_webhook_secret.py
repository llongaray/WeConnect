from django.db import migrations

import apps.core.fields
from apps.core.encryption import encrypt_text


def encrypt_existing_webhook_secrets(apps, schema_editor):
    Channel = apps.get_model('whatsapp', 'Channel')
    for channel in Channel.objects.exclude(webhook_secret=''):
        raw = channel.webhook_secret or ''
        if raw and not raw.startswith('gAAAA'):
            channel.webhook_secret = encrypt_text(raw)
            channel.save(update_fields=['webhook_secret'])


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0008_encrypt_credentials'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='webhook_secret',
            field=apps.core.fields.EncryptedCharField(blank=True, default=''),
        ),
        migrations.RunPython(encrypt_existing_webhook_secrets, migrations.RunPython.noop),
    ]
