from django.db import migrations
from django.db.models import Q


GENERAL_ROOM_SLUG = 'equipe-weconnect'


def seed_general_room(apps, schema_editor):
    PlatformRoom = apps.get_model('platform_chat', 'PlatformRoom')
    PlatformRoomMember = apps.get_model('platform_chat', 'PlatformRoomMember')
    User = apps.get_model('accounts', 'User')

    room, _ = PlatformRoom.objects.get_or_create(
        slug=GENERAL_ROOM_SLUG,
        defaults={
            'kind': 'group',
            'name': 'Equipe WeConnect',
        },
    )

    operators = User.objects.filter(
        Q(is_superuser=True)
        | Q(is_staff=True, is_superuser=False, company__isnull=True),
        is_active=True,
    )
    for user in operators:
        PlatformRoomMember.objects.get_or_create(room=room, user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('platform_chat', '0001_initial'),
        ('accounts', '0011_trusted_device'),
    ]

    operations = [
        migrations.RunPython(seed_general_room, migrations.RunPython.noop),
    ]
