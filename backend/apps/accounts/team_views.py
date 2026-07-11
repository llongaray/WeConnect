from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Team, TeamMembership, User
from apps.accounts.permissions import IsAdmin
from apps.accounts.team_serializers import TeamMemberUpsertSerializer, TeamSerializer
from apps.whatsapp.models import Channel


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.prefetch_related('channels', 'memberships__user').order_by('name')
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=True, methods=['post', 'patch'], url_path='members')
    def members(self, request, pk=None):
        team = self.get_object()
        serializer = TeamMemberUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        role = serializer.validated_data['role']

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

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
            channel = Channel.objects.get(pk=channel_id)
        except Channel.DoesNotExist:
            return Response({'detail': 'Canal não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if not team.channels.filter(pk=channel_id).exists():
            return Response({'detail': 'Canal não pertence à equipe.'}, status=status.HTTP_400_BAD_REQUEST)
        channel.default_team = team
        channel.save(update_fields=['default_team', 'updated_at'])
        return Response(TeamSerializer(team).data)
