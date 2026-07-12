from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import AuditLog, SecurityEvent
from apps.accounts.permissions import IsSuperUser
from apps.accounts.serializers import SecurityEventSerializer
from apps.accounts.services.audit import log_audit
from apps.accounts.services.login_security import unlock_ip, unlock_username
from apps.accounts.services.security_events import log_security_event


class SecurityEventFilter(filters.FilterSet):
    event_type = filters.CharFilter(field_name='event_type')
    ip_address = filters.CharFilter(field_name='ip_address', lookup_expr='icontains')
    username = filters.CharFilter(field_name='username', lookup_expr='icontains')

    class Meta:
        model = SecurityEvent
        fields = ['event_type', 'ip_address', 'username']


class SecurityEventViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [IsSuperUser]
    filterset_class = SecurityEventFilter

    @action(detail=False, methods=['post'], url_path='unlock-ip')
    def unlock_ip_action(self, request):
        ip = request.data.get('ip_address', '').strip()
        username = request.data.get('username', '').strip()
        if not ip and not username:
            return Response(
                {'detail': 'Informe ip_address ou username.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ip:
            unlock_ip(ip)
        if username:
            unlock_username(username)
        log_security_event(
            SecurityEvent.EventType.IP_UNLOCKED,
            ip_address=ip or None,
            username=username,
            metadata={'unlocked_by': request.user.username},
        )
        log_audit(
            action=AuditLog.Action.STATUS_CHANGE,
            entity_type='security',
            entity_label=ip or username,
            actor=request.user,
            metadata={'action': 'unlock_ip', 'ip': ip, 'username': username},
            request=request,
        )
        return Response({'ok': True})
