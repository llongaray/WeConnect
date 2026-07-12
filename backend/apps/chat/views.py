from django.db.models import Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User

from apps.accounts.permissions import CanManageLgpd, CanViewContacts, IsGestorOrSuperUser
from apps.accounts.services.capabilities import is_platform_operator

from .conversation_lifecycle import (
    assume,
    close,
    get_supervised_team_ids,
    get_user_team_ids,
    release,
    reopen,
    transfer,
    user_can_access_conversation,
)
from .message_service import send_outbound_message
from .categories import category_filter_q
from .tag_serializers import ConversationTagAssignSerializer
from .tag_services import assign_tag_to_contact, remove_tag_from_contact
from .models import Contact, Conversation, ConversationEvent, Message, Tag
from .permissions import CanSendMessage, IsConversationAccessible
from .serializers import (
    CloseSerializer,
    ContactSerializer,
    ConversationEventSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    TransferSerializer,
)
from .services import broadcast_conversation_updated


class MessageCursorPagination(CursorPagination):
    page_size = 50
    ordering = '-created_at'


class ContactViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, CanViewContacts]
    search_fields = ['name', 'phone', 'external_id']

    def get_queryset(self):
        user = self.request.user
        qs = Contact.objects.select_related('channel__company')
        if is_platform_operator(user):
            company_id = self.request.query_params.get('company_id')
            if company_id:
                return qs.filter(channel__company_id=company_id)
            return qs.none()
        if user.company_id:
            return qs.filter(channel__company_id=user.company_id)
        return qs.none()

    @action(detail=True, methods=['get'], url_path='export-data')
    def export_data(self, request, pk=None):
        """Exportação de dados do titular (LGPD Art. 18 V)."""
        contact = self.get_object()
        from apps.chat.services.lgpd import export_contact_data
        return Response(export_contact_data(contact))

    @action(detail=True, methods=['post'], url_path='erase', permission_classes=[IsAuthenticated, CanManageLgpd])
    def erase(self, request, pk=None):
        """Exclusão de dados do titular (LGPD Art. 18 VI)."""
        contact = self.get_object()
        from apps.chat.services.lgpd import erase_contact_data
        erase_contact_data(contact, actor=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, IsConversationAccessible]
    filterset_fields = ['status', 'assigned_to', 'team']
    search_fields = ['contact__name', 'contact__phone']
    http_method_names = ['get', 'head', 'options', 'patch', 'post']

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.select_related(
            'contact', 'assigned_to', 'channel', 'team', 'closed_by',
        ).prefetch_related(
            Prefetch(
                'events',
                queryset=ConversationEvent.objects.select_related(
                    'actor', 'from_user', 'to_user',
                )[:5],
                to_attr='_prefetched_events',
            ),
        )

        channel_ids = self.request.query_params.getlist('channel')
        if channel_ids:
          try:
            ids = [int(cid) for cid in channel_ids if str(cid).strip()]
          except ValueError:
            ids = []
          if ids:
            qs = qs.filter(channel_id__in=ids)

        status_filter = self.request.query_params.get('status')
        filtro = self.request.query_params.get('filter')
        category = self.request.query_params.get('category')

        if category:
          qs = qs.filter(category_filter_q(category))
        elif status_filter:
          qs = qs.filter(status=status_filter)
        elif filtro == 'closed':
          qs = qs.filter(status=Conversation.Status.CLOSED)
        elif filtro == 'all':
          pass
        else:
          qs = qs.filter(status__in=[Conversation.Status.OPEN, Conversation.Status.BOT])

        if filtro == 'mine':
          qs = qs.filter(assigned_to=user)
        elif filtro == 'unassigned':
          qs = qs.filter(assigned_to__isnull=True, status=Conversation.Status.OPEN)
        elif filtro == 'closed':
          qs = qs.filter(status=Conversation.Status.CLOSED)
        elif filtro == 'handoff':
          qs = qs.filter(handoff_pending=True, status=Conversation.Status.OPEN)

        if user.is_gestor and user.company_id:
            qs = qs.filter(channel__company_id=user.company_id)
        elif is_platform_operator(user):
            company_id = self.request.query_params.get('company_id')
            if company_id:
                qs = qs.filter(channel__company_id=company_id)
            else:
                return qs.none()

        if not user.is_admin:
            team_ids = get_user_team_ids(user)
            if user.is_supervisor:
                supervised = get_supervised_team_ids(user)
                qs = qs.filter(
                    Q(team_id__in=team_ids)
                    | Q(assigned_to=user)
                    | Q(assigned_to__isnull=True, team_id__in=supervised),
                )
            else:
                qs = qs.filter(
                    Q(team_id__in=team_ids)
                    & (Q(assigned_to=user) | Q(assigned_to__isnull=True)),
                )

        return qs

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy', 'create'):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=['patch'])
    def assume(self, request, pk=None):
        conversation = self.get_object()
        try:
            conversation = assume(conversation, request.user)
        except (PermissionDenied, ValidationError) as exc:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionDenied) else status.HTTP_400_BAD_REQUEST
            detail = exc.detail if hasattr(exc, 'detail') else str(exc)
            return Response({'detail': detail}, status=status_code)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['patch'])
    def release(self, request, pk=None):
        conversation = self.get_object()
        try:
            conversation = release(conversation, request.user)
        except (PermissionDenied, ValidationError) as exc:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionDenied) else status.HTTP_400_BAD_REQUEST
            return Response({'detail': exc.detail if hasattr(exc, 'detail') else str(exc)}, status=status_code)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['patch'])
    def transfer(self, request, pk=None):
        conversation = self.get_object()
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            to_user = User.objects.get(pk=serializer.validated_data['assigned_to_id'])
        except User.DoesNotExist:
            return Response({'detail': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            conversation = transfer(
                conversation,
                request.user,
                to_user,
                note=serializer.validated_data.get('note', ''),
            )
        except (PermissionDenied, ValidationError) as exc:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionDenied) else status.HTTP_400_BAD_REQUEST
            return Response({'detail': exc.detail if hasattr(exc, 'detail') else str(exc)}, status=status_code)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['patch'])
    def close(self, request, pk=None):
        conversation = self.get_object()
        serializer = CloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            conversation = close(
                conversation,
                request.user,
                farewell_message=serializer.validated_data.get('farewell_message', ''),
            )
        except (PermissionDenied, ValidationError) as exc:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionDenied) else status.HTTP_400_BAD_REQUEST
            return Response({'detail': exc.detail if hasattr(exc, 'detail') else str(exc)}, status=status_code)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['patch'])
    def reopen(self, request, pk=None):
        conversation = self.get_object()
        try:
            conversation = reopen(conversation, request.user)
        except (PermissionDenied, ValidationError) as exc:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionDenied) else status.HTTP_400_BAD_REQUEST
            return Response({'detail': exc.detail if hasattr(exc, 'detail') else str(exc)}, status=status_code)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['patch'], url_path='assign')
    def assign_legacy(self, request, pk=None):
        """Alias legado — redireciona para assume ou transfer."""
        assigned_to_id = request.data.get('assigned_to_id')
        if assigned_to_id is None:
            return self.assume(request, pk=pk)
        serializer = TransferSerializer(data={
            'assigned_to_id': assigned_to_id,
            'note': request.data.get('note', ''),
        })
        serializer.is_valid(raise_exception=True)
        conversation = self.get_object()
        try:
            to_user = User.objects.get(pk=serializer.validated_data['assigned_to_id'])
        except User.DoesNotExist:
            return Response({'detail': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            conversation = transfer(conversation, request.user, to_user, note=serializer.validated_data.get('note', ''))
        except (PermissionDenied, ValidationError) as exc:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionDenied) else status.HTTP_400_BAD_REQUEST
            return Response({'detail': exc.detail if hasattr(exc, 'detail') else str(exc)}, status=status_code)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['get'], url_path='team-members')
    def team_members(self, request, pk=None):
        """Lista membros da equipe para transferência."""
        from apps.accounts.models import TeamMembership

        conversation = self.get_object()
        if not conversation.team_id:
            return Response([])
        memberships = TeamMembership.objects.filter(
            team_id=conversation.team_id,
        ).select_related('user')
        return Response([
            {
                'id': m.user.id,
                'username': m.user.username,
                'first_name': m.user.first_name,
                'last_name': m.user.last_name,
                'role': m.user.role,
                'team_role': m.role,
            }
            for m in memberships
        ])

    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        conversation.unread_count = 0
        conversation.save(update_fields=['unread_count', 'updated_at'])
        broadcast_conversation_updated(conversation)
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        conversation = self.get_object()
        events = conversation.events.select_related('actor', 'from_user', 'to_user')[:50]
        return Response(ConversationEventSerializer(events, many=True).data)

    @action(detail=True, methods=['post'], url_path='tags')
    def assign_tag(self, request, pk=None):
        conversation = self.get_object()
        serializer = ConversationTagAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tag = Tag.objects.get(
                pk=serializer.validated_data['tag_id'],
                company_id=conversation.channel.company_id,
                is_active=True,
            )
        except Tag.DoesNotExist:
            return Response({'detail': 'Tag não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            assign_tag_to_contact(conversation.contact, tag, request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        conversation.refresh_from_db()
        return Response(ConversationSerializer(conversation, context={'request': request}).data)

    @action(detail=True, methods=['delete'], url_path='tags/(?P<tag_id>[^/.]+)')
    def remove_tag(self, request, pk=None, tag_id=None):
        conversation = self.get_object()
        try:
            tag = Tag.objects.get(
                pk=tag_id,
                company_id=conversation.channel.company_id,
            )
        except Tag.DoesNotExist:
            return Response({'detail': 'Tag não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        remove_tag_from_contact(conversation.contact, tag)
        conversation.refresh_from_db()
        return Response(ConversationSerializer(conversation, context={'request': request}).data)

    @action(
        detail=True,
        methods=['get', 'post'],
        permission_classes=[IsAuthenticated, CanSendMessage],
        parser_classes=[JSONParser, MultiPartParser, FormParser],
    )
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if not user_can_access_conversation(request.user, conversation):
            raise PermissionDenied()

        if request.method == 'GET':
            qs = conversation.messages.select_related('sent_by').order_by('-created_at')
            paginator = MessageCursorPagination()
            page = paginator.paginate_queryset(qs, request)
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        if request.FILES.get('media'):
            validated['media'] = request.FILES['media']
        message = send_outbound_message(request.user, conversation, validated)
        from .services import _broadcast_message
        _broadcast_message(message, conversation)
        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
