import re
from typing import Iterable

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services.capabilities import is_platform_operator
from apps.platform_chat.models import (
    PlatformMessage,
    PlatformReadState,
    PlatformRoom,
    PlatformRoomMember,
)

GENERAL_ROOM_SLUG = 'equipe-weconnect'
MENTION_PATTERN = re.compile(r'@([a-zA-Z0-9_]+)')


def platform_operators_queryset():
    return User.objects.filter(
        Q(is_superuser=True)
        | Q(is_staff=True, is_superuser=False, company__isnull=True),
        is_active=True,
    )


def list_platform_operators(exclude_user: User | None = None):
    qs = platform_operators_queryset().order_by('username')
    if exclude_user:
        qs = qs.exclude(pk=exclude_user.pk)
    return qs


def _direct_key(user_a: User, user_b: User) -> str:
    ids = sorted([user_a.id, user_b.id])
    return f'{ids[0]}_{ids[1]}'


def get_or_create_general_room() -> PlatformRoom:
    room, _ = PlatformRoom.objects.get_or_create(
        slug=GENERAL_ROOM_SLUG,
        defaults={
            'kind': PlatformRoom.Kind.GROUP,
            'name': 'Equipe WeConnect',
        },
    )
    return room


def ensure_general_room_membership(user: User) -> None:
    room = get_or_create_general_room()
    PlatformRoomMember.objects.get_or_create(room=room, user=user)


def get_or_create_direct_room(user_a: User, user_b: User) -> PlatformRoom:
    if user_a.id == user_b.id:
        raise ValueError('Não é possível abrir DM consigo mesmo.')
    key = _direct_key(user_a, user_b)
    room, created = PlatformRoom.objects.get_or_create(
        direct_key=key,
        defaults={
            'kind': PlatformRoom.Kind.DIRECT,
            'name': '',
        },
    )
    if created:
        PlatformRoomMember.objects.bulk_create([
            PlatformRoomMember(room=room, user=user_a),
            PlatformRoomMember(room=room, user=user_b),
        ])
    return room


def user_can_access_room(user: User, room: PlatformRoom) -> bool:
    if not is_platform_operator(user):
        return False
    if room.kind == PlatformRoom.Kind.GROUP and room.slug == GENERAL_ROOM_SLUG:
        return True
    return PlatformRoomMember.objects.filter(room=room, user=user).exists()


def parse_mentions(content: str) -> list[User]:
    if not content:
        return []
    usernames = set(MENTION_PATTERN.findall(content))
    if not usernames:
        return []
    return list(
        platform_operators_queryset().filter(username__in=usernames),
    )


def _room_group(room_id: int) -> str:
    return f'platform_room_{room_id}'


def _user_group(user_id: int) -> str:
    return f'platform_user_{user_id}'


def _broadcast_platform_event(event: str, data: dict, room_id: int | None = None, user_ids: Iterable[int] | None = None):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    payload = {'type': 'platform_chat_event', 'event': event, 'data': data}
    if room_id is not None:
        async_to_sync(channel_layer.group_send)(_room_group(room_id), payload)
    for user_id in user_ids or []:
        async_to_sync(channel_layer.group_send)(_user_group(user_id), payload)


def mark_room_read(user: User, room: PlatformRoom) -> None:
    PlatformReadState.objects.update_or_create(
        room=room,
        user=user,
        defaults={'last_read_at': timezone.now()},
    )
    _broadcast_platform_event(
        'read.updated',
        {'room_id': room.id, 'user_id': user.id},
        room_id=room.id,
        user_ids=[user.id],
    )


@transaction.atomic
def send_platform_message(
    *,
    room: PlatformRoom,
    sender: User,
    content: str = '',
    message_type: str = PlatformMessage.MessageType.TEXT,
    media_file=None,
) -> PlatformMessage:
    message = PlatformMessage.objects.create(
        room=room,
        sender=sender,
        content=content or '',
        message_type=message_type,
    )
    if media_file:
        message.media_file = media_file
        message.save(update_fields=['media_file'])

    mentioned_users = parse_mentions(content)
    if mentioned_users:
        message.mentions.set(mentioned_users)

    member_ids = list(
        PlatformRoomMember.objects.filter(room=room)
        .values_list('user_id', flat=True),
    )
    if room.kind == PlatformRoom.Kind.GROUP:
        member_ids = list(platform_operators_queryset().values_list('id', flat=True))

    from apps.platform_chat.serializers import PlatformMessageSerializer

    serializer = PlatformMessageSerializer(message)
    data = serializer.data

    notify_ids = set(member_ids) - {sender.id}
    _broadcast_platform_event('message.new', data, room_id=room.id, user_ids=notify_ids)

    for mentioned in mentioned_users:
        if mentioned.id != sender.id:
            _broadcast_platform_event(
                'mention.new',
                {'message': data, 'room_id': room.id},
                user_ids=[mentioned.id],
            )

    return message


def get_user_rooms(user: User) -> list[PlatformRoom]:
    ensure_general_room_membership(user)
    general = get_or_create_general_room()
    direct_ids = PlatformRoomMember.objects.filter(
        user=user,
        room__kind=PlatformRoom.Kind.DIRECT,
    ).values_list('room_id', flat=True)
    direct_rooms = PlatformRoom.objects.filter(id__in=direct_ids).order_by('-created_at')
    return [general, *direct_rooms]


def get_unread_summary(user: User) -> dict:
    ensure_general_room_membership(user)
    rooms = get_user_rooms(user)
    read_map = {
        state.room_id: state.last_read_at
        for state in PlatformReadState.objects.filter(user=user, room_id__in=[r.id for r in rooms])
    }

    unread_messages = 0
    unread_mentions = 0
    now = timezone.now()

    for room in rooms:
        last_read = read_map.get(room.id)
        qs = PlatformMessage.objects.filter(room=room).exclude(sender=user)
        if last_read:
            qs = qs.filter(created_at__gt=last_read)
        unread_messages += qs.count()
        unread_mentions += qs.filter(mentions=user).count()

    return {
        'unread_messages': unread_messages,
        'unread_mentions': unread_mentions,
        'total': unread_messages,
    }


def get_room_unread_count(user: User, room: PlatformRoom) -> int:
    state = PlatformReadState.objects.filter(room=room, user=user).first()
    qs = PlatformMessage.objects.filter(room=room).exclude(sender=user)
    if state:
        qs = qs.filter(created_at__gt=state.last_read_at)
    return qs.count()


def get_direct_display_name(room: PlatformRoom, current_user: User) -> str:
    other = (
        PlatformRoomMember.objects.filter(room=room)
        .exclude(user=current_user)
        .select_related('user')
        .first()
    )
    if not other:
        return 'Privado'
    user = other.user
    return user.first_name or user.username
