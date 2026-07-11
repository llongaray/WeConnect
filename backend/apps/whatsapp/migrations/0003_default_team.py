# Gerado manualmente — equipe padrão por canal

import django.db.models.deletion
from django.db import migrations, models


def create_default_teams(apps, schema_editor):
    Channel = apps.get_model('whatsapp', 'Channel')
    Team = apps.get_model('accounts', 'Team')

    for channel in Channel.objects.all():
        team_name = f'Equipe {channel.name}'
        team, created = Team.objects.get_or_create(
            name=team_name,
            defaults={'is_active': True},
        )
        team.channels.add(channel)
        channel.default_team_id = team.id
        channel.save(update_fields=['default_team_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0002_channel'),
        ('accounts', '0003_teams_supervisor'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='default_team',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='default_for_channels',
                to='accounts.team',
            ),
        ),
        migrations.RunPython(create_default_teams, migrations.RunPython.noop),
    ]
