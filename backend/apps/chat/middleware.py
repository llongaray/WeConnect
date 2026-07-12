from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


class JWTAuthMiddleware(BaseMiddleware):
    """WebSocket: autenticação ocorre no primeiro frame JSON do consumer."""

    async def __call__(self, scope, receive, send):
        scope['user'] = AnonymousUser()
        return await super().__call__(scope, receive, send)
