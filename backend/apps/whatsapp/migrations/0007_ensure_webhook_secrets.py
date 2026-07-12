import secrets

from django.db import migrations


def ensure_webhook_secrets(apps, schema_editor):
    """Garante secret em todos os canais existentes."""
    Channel = apps.get_model('whatsapp', 'Channel')
    for channel in Channel.objects.filter(webhook_secret=''):
        channel.webhook_secret = secrets.token_urlsafe(32)
        channel.save(update_fields=['webhook_secret'])


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0006_channel_is_archived'),
    ]

    operations = [
        migrations.RunPython(ensure_webhook_secrets, migrations.RunPython.noop),
    ]
