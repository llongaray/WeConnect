import secrets

from django.db import migrations, models


def migrate_whatsapp_instance_to_channel(apps, schema_editor):
  WhatsAppInstance = apps.get_model('whatsapp', 'WhatsAppInstance')
  Channel = apps.get_model('whatsapp', 'Channel')
  for instance in WhatsAppInstance.objects.all():
    Channel.objects.create(
      name=instance.name,
      channel_type='evolution_normal',
      status=instance.status,
      phone=instance.phone,
      qrcode_base64=instance.qrcode_base64,
      credentials={'evolution_instance_name': instance.name},
      webhook_secret=secrets.token_urlsafe(32),
      is_active=True,
      created_at=instance.created_at,
      updated_at=instance.updated_at,
    )


class Migration(migrations.Migration):

  dependencies = [
    ('whatsapp', '0001_initial'),
  ]

  operations = [
    migrations.CreateModel(
      name='Channel',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('name', models.CharField(max_length=100, unique=True)),
        ('channel_type', models.CharField(choices=[('evolution_normal', 'WhatsApp Normal'), ('evolution_business', 'WhatsApp Business'), ('meta_cloud', 'API Oficial Meta')], max_length=30)),
        ('status', models.CharField(choices=[('connecting', 'Conectando'), ('open', 'Conectado'), ('close', 'Desconectado')], default='close', max_length=20)),
        ('phone', models.CharField(blank=True, default='', max_length=30)),
        ('qrcode_base64', models.TextField(blank=True, default='')),
        ('credentials', models.JSONField(blank=True, default=dict)),
        ('webhook_secret', models.CharField(blank=True, default='', max_length=255)),
        ('is_active', models.BooleanField(default=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('updated_at', models.DateTimeField(auto_now=True)),
      ],
      options={
        'verbose_name': 'Canal',
        'verbose_name_plural': 'Canais',
        'ordering': ['name'],
      },
    ),
    migrations.RunPython(migrate_whatsapp_instance_to_channel, migrations.RunPython.noop),
    migrations.DeleteModel(
      name='WhatsAppInstance',
    ),
  ]
