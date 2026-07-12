from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PlatformDirectCreateView,
    PlatformMessageMediaView,
    PlatformOperatorListView,
    PlatformRoomMessagesView,
    PlatformRoomReadView,
    PlatformRoomViewSet,
    PlatformUnreadView,
)

router = DefaultRouter()
router.register('rooms', PlatformRoomViewSet, basename='platform-chat-room')

urlpatterns = [
    path('platform-chat/operators/', PlatformOperatorListView.as_view(), name='platform-chat-operators'),
    path('platform-chat/unread/', PlatformUnreadView.as_view(), name='platform-chat-unread'),
    path('platform-chat/direct/', PlatformDirectCreateView.as_view(), name='platform-chat-direct'),
    path('platform-chat/rooms/<int:room_id>/messages/', PlatformRoomMessagesView.as_view(), name='platform-chat-messages'),
    path('platform-chat/rooms/<int:room_id>/read/', PlatformRoomReadView.as_view(), name='platform-chat-read'),
    path('platform-chat/media/<int:message_id>/', PlatformMessageMediaView.as_view(), name='platform-chat-media'),
    path('', include(router.urls)),
]
