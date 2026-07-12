import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import Company, User
from apps.accounts.services.capabilities import is_platform_operator, is_weconnect_support
from apps.accounts.totp_service import user_requires_totp_setup


@database_sync_to_async
def _get_user_from_token(token: str):
    try:
        access = AccessToken(token)
        user_id = access['user_id']
        return User.objects.get(pk=user_id, is_active=True)
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


@database_sync_to_async
def _company_exists(company_id: int) -> bool:
    return Company.objects.filter(pk=company_id, is_active=True).exists()


def _company_group(company_id: int) -> str:
    return f'chat_company_{company_id}'


def _parse_company_id(scope) -> int | None:
    query = scope.get('query_string', b'').decode()
    if not query:
        return None
    values = parse_qs(query).get('company_id', [])
    if not values:
        return None
    try:
        return int(values[0])
    except (TypeError, ValueError):
        return None


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket de eventos de chat em tempo real (escopo por empresa)."""

    async def connect(self):
        self.authenticated = False
        self.joined_groups: list[str] = []
        self.pending_company_id = _parse_company_id(self.scope)
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
            if user.is_authenticated and not user.is_superuser and not is_weconnect_support(user):
                await self._authenticate(user)
                return

    async def disconnect(self, close_code):
        if getattr(self, 'authenticated', False):
            for group in self.joined_groups:
                await self.channel_layer.group_discard(group, self.channel_name)

    async def _authenticate(self, user, company_id: int | None = None):
        if user_requires_totp_setup(user):
            await self.close()
            return

        if not user.is_active:
            await self.close()
            return

        if user.company_id:
            company = user.company
            if not company.is_active:
                await self.close()
                return

        if is_platform_operator(user):
            target_company_id = company_id or self.pending_company_id
            if not target_company_id:
                await self.close()
                return
            if not await _company_exists(target_company_id):
                await self.close()
                return
        elif not user.company_id:
            await self.close()
            return
        else:
            target_company_id = user.company_id

        self.scope['user'] = user
        self.authenticated = True
        group = _company_group(target_company_id)
        await self.channel_layer.group_add(group, self.channel_name)
        self.joined_groups.append(group)

        await self.send(text_data=json.dumps({'event': 'auth.ok', 'data': {'company_id': target_company_id}}))

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

        token = payload.get('token', '')
        company_id = payload.get('company_id')
        if company_id is not None:
            try:
                company_id = int(company_id)
            except (TypeError, ValueError):
                await self.close()
                return

        user = None
        if token:
            user = await _get_user_from_token(token)
        else:
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

        if not user or not user.is_authenticated:
            await self.close()
            return

        await self._authenticate(user, company_id=company_id)

    async def chat_event(self, event):
        if not self.authenticated:
            return
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'data': event['data'],
        }))
