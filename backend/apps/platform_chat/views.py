from django.http import FileResponse
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.accounts.models import User
from apps.platform_chat.media_urls import verify_platform_media_signature
from apps.platform_chat.media_validation import validate_platform_chat_media
from apps.platform_chat.models import PlatformMessage, PlatformRoom
from apps.platform_chat.permissions import IsPlatformChatOperator
from apps.platform_chat.serializers import (
    PlatformDirectCreateSerializer,
    PlatformMessageCreateSerializer,
    PlatformMessageSerializer,
    PlatformOperatorSerializer,
    PlatformRoomSerializer,
)
from apps.platform_chat.services import (
    ensure_general_room_membership,
    get_or_create_direct_room,
    get_user_rooms,
    get_unread_summary,
    list_platform_operators,
    mark_room_read,
    platform_operators_queryset,
    send_platform_message,
    user_can_access_room,
)


class PlatformRoomViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsPlatformChatOperator]
    serializer_class = PlatformRoomSerializer

    def get_queryset(self):
        ensure_general_room_membership(self.request.user)
        room_ids = [room.id for room in get_user_rooms(self.request.user)]
        return PlatformRoom.objects.filter(id__in=room_ids)


class PlatformOperatorListView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformChatOperator]

    def get(self, request):
        operators = list_platform_operators(exclude_user=request.user)
        data = PlatformOperatorSerializer(operators, many=True).data
        return Response(data)


class PlatformUnreadView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformChatOperator]

    def get(self, request):
        return Response(get_unread_summary(request.user))


class PlatformDirectCreateView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformChatOperator]

    def post(self, request):
        serializer = PlatformDirectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username'].strip().lstrip('@')
        try:
            peer = platform_operators_queryset().get(username=username)
        except User.DoesNotExist as exc:
            raise ValidationError({'username': 'Operador não encontrado.'}) from exc
        if peer.id == request.user.id:
            raise ValidationError({'username': 'Não é possível abrir DM consigo mesmo.'})
        room = get_or_create_direct_room(request.user, peer)
        return Response(
            PlatformRoomSerializer(room, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class PlatformRoomMessagesView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformChatOperator]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_room(self, room_id: int) -> PlatformRoom:
        try:
            room = PlatformRoom.objects.get(pk=room_id)
        except PlatformRoom.DoesNotExist as exc:
            raise NotFound('Sala não encontrada.') from exc
        if not user_can_access_room(self.request.user, room):
            raise PermissionDenied('Sem acesso a esta sala.')
        return room

    def get(self, request, room_id: int):
        room = self.get_room(room_id)
        cursor = request.query_params.get('cursor')
        limit = min(int(request.query_params.get('limit', 50)), 100)
        qs = PlatformMessage.objects.filter(room=room).select_related('sender').prefetch_related('mentions')
        if cursor:
            try:
                cursor_id = int(cursor)
                qs = qs.filter(id__lt=cursor_id)
            except (TypeError, ValueError):
                pass
        messages = list(qs.order_by('-created_at')[:limit])
        messages.reverse()
        serializer = PlatformMessageSerializer(messages, many=True, context={'request': request})
        next_cursor = messages[0].id if messages else None
        return Response({
            'results': serializer.data,
            'next_cursor': next_cursor if len(messages) == limit else None,
        })

    def post(self, request, room_id: int):
        room = self.get_room(room_id)
        serializer = PlatformMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        media = data.get('media')
        message_type = data.get('message_type', PlatformMessage.MessageType.TEXT)
        content = data.get('content', '')

        if media:
            message_type = validate_platform_chat_media(media)

        message = send_platform_message(
            room=room,
            sender=request.user,
            content=content,
            message_type=message_type,
            media_file=media,
        )
        return Response(
            PlatformMessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PlatformRoomReadView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformChatOperator]

    def post(self, request, room_id: int):
        try:
            room = PlatformRoom.objects.get(pk=room_id)
        except PlatformRoom.DoesNotExist as exc:
            raise NotFound('Sala não encontrada.') from exc
        if not user_can_access_room(request.user, room):
            raise PermissionDenied('Sem acesso a esta sala.')
        mark_room_read(request.user, room)
        return Response({'detail': 'Marcado como lido.'})


class PlatformMessageMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id: int):
        try:
            message = PlatformMessage.objects.select_related('room').get(pk=message_id)
        except PlatformMessage.DoesNotExist as exc:
            raise NotFound('Mídia não encontrada.') from exc

        exp = request.query_params.get('exp', '')
        sig = request.query_params.get('sig', '')
        uid = request.query_params.get('uid', '')
        signed_ok = verify_platform_media_signature(message_id, exp, sig, uid)

        if signed_ok:
            pass
        elif request.user.is_authenticated and user_can_access_room(request.user, message.room):
            pass
        else:
            raise PermissionDenied('Acesso negado.')

        if not message.media_file:
            raise NotFound('Arquivo não encontrado.')

        return FileResponse(
            message.media_file.open('rb'),
            as_attachment=True,
            filename=message.media_file.name.split('/')[-1],
        )
