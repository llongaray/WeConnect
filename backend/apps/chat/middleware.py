from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User


@database_sync_to_async
def _get_user(user_id):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Autentica WebSocket via token JWT na query string (?token=)."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token_list = params.get('token', [])
        scope['user'] = AnonymousUser()

        if token_list:
            try:
                access = AccessToken(token_list[0])
                user_id = access['user_id']
                scope['user'] = await _get_user(user_id)
            except Exception:
                scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
