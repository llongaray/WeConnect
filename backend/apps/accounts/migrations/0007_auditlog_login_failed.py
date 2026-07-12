from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_ensure_platform_superuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('create', 'Criação'),
                    ('update', 'Atualização'),
                    ('delete', 'Exclusão'),
                    ('status_change', 'Alteração de status'),
                    ('limit_change', 'Alteração de limites'),
                    ('login_failed', 'Falha de login'),
                    ('login_blocked', 'Login bloqueado'),
                ],
                max_length=30,
            ),
        ),
    ]
