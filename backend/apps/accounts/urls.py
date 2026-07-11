from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .team_views import TeamViewSet
from .views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('teams', TeamViewSet, basename='team')

urlpatterns = [
    path('', include(router.urls)),
]
