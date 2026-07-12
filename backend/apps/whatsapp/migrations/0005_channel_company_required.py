# Torna company obrigatório no canal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_migrate_default_company'),
        ('whatsapp', '0004_channel_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='channels',
                to='accounts.company',
            ),
        ),
    ]
