import django.db.models.deletion
from django.db import migrations, models


def migrate_to_multi_channel(apps, schema_editor):
  Channel = apps.get_model('whatsapp', 'Channel')
  Contact = apps.get_model('chat', 'Contact')
  Conversation = apps.get_model('chat', 'Conversation')

  default_channel = Channel.objects.first()
  if not default_channel:
    default_channel = Channel.objects.create(
      name='Canal Padrão',
      channel_type='evolution_normal',
      status='close',
      credentials={'evolution_instance_name': 'channel-default'},
      webhook_secret='migrated',
    )

  for contact in Contact.objects.all():
    contact.channel_id = default_channel.id
    contact.external_id = contact.remote_jid
    contact.save(update_fields=['channel_id', 'external_id'])

  for conversation in Conversation.objects.select_related('contact').all():
    conversation.channel_id = conversation.contact.channel_id
    conversation.save(update_fields=['channel_id'])


class Migration(migrations.Migration):

  dependencies = [
    ('whatsapp', '0002_channel'),
    ('chat', '0001_initial'),
  ]

  operations = [
    migrations.RenameField(
      model_name='message',
      old_name='evolution_id',
      new_name='external_id',
    ),
    migrations.AddField(
      model_name='contact',
      name='channel',
      field=models.ForeignKey(
        null=True,
        on_delete=django.db.models.deletion.CASCADE,
        related_name='contacts',
        to='whatsapp.channel',
      ),
    ),
    migrations.AddField(
      model_name='contact',
      name='external_id',
      field=models.CharField(blank=True, db_index=True, default='', max_length=100),
    ),
    migrations.AddField(
      model_name='conversation',
      name='channel',
      field=models.ForeignKey(
        null=True,
        on_delete=django.db.models.deletion.CASCADE,
        related_name='conversations',
        to='whatsapp.channel',
      ),
    ),
    migrations.RunPython(migrate_to_multi_channel, migrations.RunPython.noop),
    migrations.RemoveField(
      model_name='contact',
      name='remote_jid',
    ),
    migrations.AlterField(
      model_name='contact',
      name='channel',
      field=models.ForeignKey(
        on_delete=django.db.models.deletion.CASCADE,
        related_name='contacts',
        to='whatsapp.channel',
      ),
    ),
    migrations.AlterField(
      model_name='contact',
      name='external_id',
      field=models.CharField(db_index=True, max_length=100),
    ),
    migrations.AlterField(
      model_name='conversation',
      name='channel',
      field=models.ForeignKey(
        on_delete=django.db.models.deletion.CASCADE,
        related_name='conversations',
        to='whatsapp.channel',
      ),
    ),
    migrations.AddConstraint(
      model_name='contact',
      constraint=models.UniqueConstraint(
        fields=('channel', 'external_id'),
        name='unique_contact_per_channel',
      ),
    ),
    migrations.AddConstraint(
      model_name='conversation',
      constraint=models.UniqueConstraint(
        fields=('channel', 'contact'),
        name='unique_conversation_per_channel_contact',
      ),
    ),
  ]
