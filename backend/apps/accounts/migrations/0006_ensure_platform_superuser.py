from django.db import migrations


def ensure_platform_superuser(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(is_superuser=True).update(company_id=None)

    if User.objects.filter(is_superuser=True).exists():
        return

    admin = User.objects.filter(username='admin').first()
    if not admin:
        return

    admin.is_superuser = True
    admin.is_staff = True
    admin.company_id = None
    admin.role = 'gestor'
    admin.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_migrate_default_company'),
    ]

    operations = [
        migrations.RunPython(ensure_platform_superuser, migrations.RunPython.noop),
    ]
