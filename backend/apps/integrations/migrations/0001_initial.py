from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DeepSeekConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_key', models.CharField(blank=True, default='', max_length=255)),
                ('status', models.CharField(
                    choices=[('connected', 'Conectado'), ('disconnected', 'Desconectado'), ('error', 'Erro')],
                    default='disconnected',
                    max_length=20,
                )),
                ('last_error', models.TextField(blank=True, default='')),
                ('last_validated_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração DeepSeek',
                'verbose_name_plural': 'Configurações DeepSeek',
            },
        ),
    ]
