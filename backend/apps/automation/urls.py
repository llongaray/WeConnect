from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BotFlowViewSet

router = DefaultRouter()
router.register('bot-flows', BotFlowViewSet, basename='bot-flow')

urlpatterns = [
    path('', include(router.urls)),
]
