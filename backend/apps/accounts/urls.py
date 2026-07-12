from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .company_views import AuditLogViewSet, CompanyViewSet
from .profile_views import ProfileView
from .security_views import SecurityEventViewSet
from .team_views import TeamViewSet
from .views import UserViewSet

router = DefaultRouter()
router.register('companies', CompanyViewSet, basename='company')
router.register('audit-logs', AuditLogViewSet, basename='audit-log')
router.register('security-events', SecurityEventViewSet, basename='security-event')
router.register('users', UserViewSet, basename='user')
router.register('teams', TeamViewSet, basename='team')

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', include(router.urls)),
]
