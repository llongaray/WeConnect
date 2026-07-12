from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_trusted_device'),
        ('chat', '0004_conversation_bot_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(default='#00A3FF', max_length=20)),
                ('funnel_order', models.PositiveIntegerField(default=0, help_text='0 = fora do funil; 1, 2, 3... definem a ordem das etapas.')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='accounts.company')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
                'ordering': ['funnel_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ContactTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_key', models.CharField(db_index=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_tags_created', to=settings.AUTH_USER_MODEL)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='chat.tag')),
            ],
            options={
                'verbose_name': 'Tag de contato',
                'verbose_name_plural': 'Tags de contato',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(fields=('company', 'name'), name='unique_tag_name_per_company'),
        ),
        migrations.AddConstraint(
            model_name='contacttag',
            constraint=models.UniqueConstraint(fields=('tag', 'contact_key'), name='unique_tag_per_contact_key'),
        ),
    ]
