import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket global para eventos de chat em tempo real."""

    async def connect(self):
        user = self.scope.get('user')
        if user is None or not user.is_authenticated:
            await self.close()
            return
        await self.channel_layer.group_add('chat_global', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('chat_global', self.channel_name)

    async def chat_event(self, event):
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'data': event['data'],
        }))
