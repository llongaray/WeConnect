from django.urls import re_path

from .consumers import PlatformChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/platform-chat/$', PlatformChatConsumer.as_asgi()),
]
