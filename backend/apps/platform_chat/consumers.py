import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.accounts.services.capabilities import is_platform_operator
from apps.accounts.totp_service import user_requires_totp_setup
from apps.platform_chat.services import ensure_general_room_membership, get_user_rooms


@database_sync_to_async
def _get_user_from_token(token: str):
    try:
        access = AccessToken(token)
        user_id = access['user_id']
        return User.objects.get(pk=user_id, is_active=True)
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


@database_sync_to_async
def _get_user_room_ids(user: User) -> list[int]:
    ensure_general_room_membership(user)
    return [room.id for room in get_user_rooms(user)]


def _user_group(user_id: int) -> str:
    return f'platform_user_{user_id}'


def _room_group(room_id: int) -> str:
    return f'platform_room_{room_id}'


class PlatformChatConsumer(AsyncWebsocketConsumer):
    """WebSocket do chat interno da equipe WeConnect."""

    async def connect(self):
        self.authenticated = False
        self.joined_groups: list[str] = []
        await self.accept()

        cookie_token = None
        headers = dict(self.scope.get('headers', []))
        cookie_header = headers.get(b'cookie', b'').decode('utf-8')
        access_name = settings.JWT_ACCESS_COOKIE_NAME
        for part in cookie_header.split(';'):
            part = part.strip()
            if part.startswith(f'{access_name}='):
                cookie_token = part.split('=', 1)[1]
                break

        if cookie_token:
            user = await _get_user_from_token(cookie_token)
            if user.is_authenticated:
                await self._authenticate(user)

    async def disconnect(self, close_code):
        if getattr(self, 'authenticated', False):
            for group in self.joined_groups:
                await self.channel_layer.group_discard(group, self.channel_name)

    async def _authenticate(self, user):
        if not is_platform_operator(user):
            await self.close()
            return
        if user_requires_totp_setup(user):
            await self.close()
            return
        if not user.is_active:
            await self.close()
            return

        self.scope['user'] = user
        self.authenticated = True

        user_group = _user_group(user.id)
        await self.channel_layer.group_add(user_group, self.channel_name)
        self.joined_groups.append(user_group)

        room_ids = await _get_user_room_ids(user)
        for room_id in room_ids:
            group = _room_group(room_id)
            await self.channel_layer.group_add(group, self.channel_name)
            self.joined_groups.append(group)

        await self.send(text_data=json.dumps({
            'event': 'auth.ok',
            'data': {'room_ids': room_ids},
        }))

    async def receive(self, text_data=None, bytes_data=None):
        if self.authenticated:
            return
        if not text_data:
            await self.close()
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.close()
            return
        if payload.get('type') != 'auth':
            await self.close()
            return
        token = payload.get('token')
        if not token:
            await self.close()
            return
        user = await _get_user_from_token(token)
        if user.is_authenticated:
            await self._authenticate(user)
        else:
            await self.close()

    async def platform_chat_event(self, event):
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'data': event.get('data', {}),
        }))
