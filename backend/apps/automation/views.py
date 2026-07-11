from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin

from .models import BotFlow
from .serializers import BotFlowCreateSerializer, BotFlowSerializer, BotFlowUpdateSerializer


class BotFlowViewSet(viewsets.ModelViewSet):
    queryset = BotFlow.objects.select_related('channel').all()
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ['channel', 'is_active']

    def get_serializer_class(self):
        if self.action == 'create':
            return BotFlowCreateSerializer
        if self.action in ('update', 'partial_update'):
            return BotFlowUpdateSerializer
        return BotFlowSerializer

    def perform_create(self, serializer):
        serializer.save()
