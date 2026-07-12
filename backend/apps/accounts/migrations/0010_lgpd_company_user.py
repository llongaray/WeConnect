from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_securityevent_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='data_retention_days',
            field=models.PositiveIntegerField(
                default=365,
                help_text='Prazo de retenção de mensagens e contatos inativos.',
                verbose_name='retenção de dados (dias)',
            ),
        ),
        migrations.AddField(
            model_name='company',
            name='dpo_email',
            field=models.EmailField(blank=True, default='', verbose_name='e-mail do encarregado'),
        ),
        migrations.AddField(
            model_name='company',
            name='dpo_name',
            field=models.CharField(blank=True, default='', max_length=150, verbose_name='encarregado (DPO)'),
        ),
        migrations.AddField(
            model_name='user',
            name='privacy_terms_accepted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
