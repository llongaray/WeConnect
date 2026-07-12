from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.mixins import CompanyScopedMixin
from apps.accounts.permissions import IsGestorOrSuperUser

from .models import BotFlow
from .serializers import BotFlowCreateSerializer, BotFlowSerializer, BotFlowUpdateSerializer


class BotFlowViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]
    company_field = 'channel__company'
    filterset_fields = ['channel', 'is_active']

    def get_queryset(self):
        qs = BotFlow.objects.select_related('channel', 'channel__company').all()
        return self.filter_queryset_by_company(qs)

    def get_serializer_class(self):
        if self.action == 'create':
            return BotFlowCreateSerializer
        if self.action in ('update', 'partial_update'):
            return BotFlowUpdateSerializer
        return BotFlowSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['company'] = self.get_company_scope()
        return context

    def perform_create(self, serializer):
        serializer.save()
