# Canal vinculado à empresa

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_saas_multicompany'),
        ('whatsapp', '0003_default_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='company',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='channels',
                to='accounts.company',
            ),
        ),
        migrations.AlterField(
            model_name='channel',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name='channel',
            constraint=models.UniqueConstraint(fields=('company', 'name'), name='unique_channel_name_per_company'),
        ),
    ]
