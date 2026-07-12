# SaaS multi-empresa — Company, AuditLog e campos de colaborador

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_teams_supervisor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(editable=False, max_length=8, unique=True)),
                ('legal_name', models.CharField(max_length=255, verbose_name='razão social')),
                ('trade_name', models.CharField(max_length=255, verbose_name='nome fantasia')),
                ('cnpj', models.CharField(blank=True, default='', max_length=18)),
                ('address', models.TextField(blank=True, default='', verbose_name='endereço')),
                ('contact_email', models.EmailField(blank=True, default='', max_length=254, verbose_name='e-mail de contato')),
                ('billing_email', models.EmailField(blank=True, default='', max_length=254, verbose_name='e-mail financeiro')),
                ('contact_phone', models.CharField(blank=True, default='', max_length=30, verbose_name='telefone de contato')),
                ('billing_phone', models.CharField(blank=True, default='', max_length=30, verbose_name='telefone financeiro')),
                ('is_active', models.BooleanField(default=True)),
                ('max_supervisors', models.PositiveIntegerField(default=5)),
                ('max_atendentes', models.PositiveIntegerField(default=20)),
                ('max_teams', models.PositiveIntegerField(default=10)),
                ('max_channels', models.PositiveIntegerField(default=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Empresa',
                'verbose_name_plural': 'Empresas',
                'ordering': ['trade_name'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[
                    ('create', 'Criação'),
                    ('update', 'Atualização'),
                    ('delete', 'Exclusão'),
                    ('status_change', 'Alteração de status'),
                    ('limit_change', 'Alteração de limites'),
                    ('login_blocked', 'Login bloqueado'),
                ], max_length=30)),
                ('entity_type', models.CharField(max_length=50)),
                ('entity_id', models.CharField(blank=True, default='', max_length=64)),
                ('entity_label', models.CharField(blank=True, default='', max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('company', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to='accounts.company',
                )),
            ],
            options={
                'verbose_name': 'Log de auditoria',
                'verbose_name_plural': 'Logs de auditoria',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='accounts.company',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='cpf',
            field=models.CharField(blank=True, default='', max_length=14),
        ),
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='telefone'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('gestor', 'Gestor'),
                    ('supervisor', 'Supervisor'),
                    ('atendente', 'Atendente'),
                ],
                default='atendente',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='team',
            name='company',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='teams',
                to='accounts.company',
            ),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name='team',
            constraint=models.UniqueConstraint(fields=('company', 'name'), name='unique_team_name_per_company'),
        ),
    ]
