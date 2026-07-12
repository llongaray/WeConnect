# DeepSeek por empresa

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_saas_multicompany'),
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='deepseekconfig',
            name='company',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='deepseek_config',
                to='accounts.company',
            ),
        ),
    ]
