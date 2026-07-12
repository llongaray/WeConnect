from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .media_views import MessageMediaView
from .tag_views import TagViewSet
from .views import ContactViewSet, ConversationViewSet

router = DefaultRouter()
router.register('contacts', ContactViewSet, basename='contact')
router.register('conversations', ConversationViewSet, basename='conversation')
router.register('tags', TagViewSet, basename='tag')

urlpatterns = [
    path('media/<int:message_id>/', MessageMediaView.as_view(), name='message-media'),
    path('', include(router.urls)),
]
