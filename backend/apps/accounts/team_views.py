from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.mixins import CompanyScopedMixin
from apps.accounts.models import AuditLog, Team, TeamMembership, User
from apps.accounts.permissions import IsGestorOrSuperUser
from apps.accounts.services.audit import log_audit
from apps.accounts.services.limits import assert_company_can_add
from apps.accounts.team_serializers import TeamMemberUpsertSerializer, TeamSerializer
from apps.whatsapp.models import Channel


class TeamViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]
    company_field = 'company'

    def get_queryset(self):
        qs = Team.objects.prefetch_related('channels', 'memberships__user').order_by('name')
        return self.filter_queryset_by_company(qs)

    def perform_create(self, serializer):
        user = self.request.user
        company = user.company if user.is_gestor else serializer.validated_data.get('company')
        if user.is_superuser:
            company = serializer.validated_data.get('company') or self.get_company_scope()
        if not company:
            raise ValidationError({'detail': 'Informe a empresa da equipe.'})
        assert_company_can_add(company, 'team')
        team = serializer.save(company=company)
        log_audit(
            action=AuditLog.Action.CREATE,
            entity_type='team',
            entity_id=team.id,
            entity_label=team.name,
            actor=user,
            company=company,
            request=self.request,
        )

    def perform_update(self, serializer):
        team = serializer.save()
        log_audit(
            action=AuditLog.Action.UPDATE,
            entity_type='team',
            entity_id=team.id,
            entity_label=team.name,
            actor=self.request.user,
            company=team.company,
            request=self.request,
        )

    def perform_destroy(self, instance):
        log_audit(
            action=AuditLog.Action.DELETE,
            entity_type='team',
            entity_id=instance.id,
            entity_label=instance.name,
            actor=self.request.user,
            company=instance.company,
            request=self.request,
        )
        instance.delete()

    @action(detail=True, methods=['post', 'patch'], url_path='members')
    def members(self, request, pk=None):
        team = self.get_object()
        serializer = TeamMemberUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        role = serializer.validated_data['role']

        try:
            user = User.objects.get(pk=user_id, company=team.company)
        except User.DoesNotExist:
            return Response({'detail': 'Usuário não encontrado nesta empresa.'}, status=status.HTTP_404_NOT_FOUND)

        membership, created = TeamMembership.objects.update_or_create(
            team=team,
            user=user,
            defaults={'role': role},
        )
        return Response(
            TeamSerializer(team).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        team = self.get_object()
        deleted, _ = TeamMembership.objects.filter(team=team, user_id=user_id).delete()
        if not deleted:
            return Response({'detail': 'Membro não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TeamSerializer(team).data)

    @action(detail=True, methods=['patch'], url_path='set-default-channel')
    def set_default_channel(self, request, pk=None):
        team = self.get_object()
        channel_id = request.data.get('channel_id')
        if not channel_id:
            return Response({'detail': 'Informe channel_id.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            channel = Channel.objects.get(pk=channel_id, company=team.company)
        except Channel.DoesNotExist:
            return Response({'detail': 'Canal não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if not team.channels.filter(pk=channel_id).exists():
            return Response({'detail': 'Canal não pertence à equipe.'}, status=status.HTTP_400_BAD_REQUEST)
        channel.default_team = team
        channel.save(update_fields=['default_team', 'updated_at'])
        return Response(TeamSerializer(team).data)
