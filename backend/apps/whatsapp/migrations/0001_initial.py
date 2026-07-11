from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='WhatsAppInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('connecting', 'Conectando'), ('open', 'Conectado'), ('close', 'Desconectado')], default='connecting', max_length=20)),
                ('phone', models.CharField(blank=True, default='', max_length=30)),
                ('qrcode_base64', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Instância WhatsApp',
                'verbose_name_plural': 'Instâncias WhatsApp',
            },
        ),
    ]
