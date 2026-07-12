import json

from django.db import migrations, models


def encrypt_existing_credentials(apps, schema_editor):
    Channel = apps.get_model('whatsapp', 'Channel')
    try:
        from apps.core.encryption import encrypt_json
    except Exception:
        return
    for channel in Channel.objects.all():
        raw = channel.credentials
        if not raw:
            channel.credentials_enc = ''
            channel.save(update_fields=['credentials_enc'])
            continue
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {}
        else:
            data = raw
        channel.credentials_enc = encrypt_json(data) if data else ''
        channel.save(update_fields=['credentials_enc'])


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0007_ensure_webhook_secrets'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='credentials_enc',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.RunPython(encrypt_existing_credentials, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='channel',
            name='credentials',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='credentials_enc',
            new_name='credentials',
        ),
    ]
