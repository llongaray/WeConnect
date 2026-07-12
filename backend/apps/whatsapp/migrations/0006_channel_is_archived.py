from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0005_channel_company_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
