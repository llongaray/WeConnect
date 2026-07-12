import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('group', 'Grupo'), ('direct', 'Privado')], max_length=10)),
                ('name', models.CharField(blank=True, default='', max_length=120)),
                ('slug', models.SlugField(blank=True, max_length=80, null=True, unique=True)),
                ('direct_key', models.CharField(blank=True, max_length=40, null=True, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PlatformRoomMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='platform_chat.platformroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='platform_chat_memberships', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PlatformMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default='')),
                ('message_type', models.CharField(choices=[('text', 'Texto'), ('image', 'Imagem'), ('audio', 'Áudio'), ('file', 'Arquivo')], default='text', max_length=10)),
                ('media_file', models.FileField(blank=True, upload_to='platform_chat/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='platform_chat.platformroom')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='platform_chat_messages', to=settings.AUTH_USER_MODEL)),
                ('mentions', models.ManyToManyField(blank=True, related_name='platform_chat_mentioned_in', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='PlatformReadState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_read_at', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_states', to='platform_chat.platformroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='platform_chat_read_states', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='platformroommember',
            constraint=models.UniqueConstraint(fields=('room', 'user'), name='uniq_platform_room_member'),
        ),
        migrations.AddConstraint(
            model_name='platformreadstate',
            constraint=models.UniqueConstraint(fields=('room', 'user'), name='uniq_platform_read_state'),
        ),
    ]
