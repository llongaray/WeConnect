from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_security_fase3'),
    ]

    operations = [
        migrations.AddField(
            model_name='securityevent',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='security_events',
                to='accounts.company',
            ),
        ),
    ]
