from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import UserPublicSerializer
from apps.platform_chat.media_urls import build_signed_platform_media_url
from apps.platform_chat.models import PlatformMessage, PlatformRoom
from apps.platform_chat.services import get_direct_display_name, get_room_unread_count


class PlatformOperatorSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'display_name')

    def get_display_name(self, obj):
        return obj.first_name or obj.username


class PlatformRoomSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    peer = serializers.SerializerMethodField()

    class Meta:
        model = PlatformRoom
        fields = (
            'id', 'kind', 'name', 'slug', 'display_name',
            'unread_count', 'last_message_at', 'peer', 'created_at',
        )

    def get_display_name(self, obj):
        request = self.context.get('request')
        if obj.kind == PlatformRoom.Kind.DIRECT and request:
            return get_direct_display_name(obj, request.user)
        return obj.name or 'Equipe WeConnect'

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return get_room_unread_count(request.user, obj)

    def get_last_message_at(self, obj):
        last = obj.messages.order_by('-created_at').values_list('created_at', flat=True).first()
        return last

    def get_peer(self, obj):
        if obj.kind != PlatformRoom.Kind.DIRECT:
            return None
        request = self.context.get('request')
        if not request:
            return None
        from apps.platform_chat.models import PlatformRoomMember

        member = (
            PlatformRoomMember.objects.filter(room=obj)
            .exclude(user=request.user)
            .select_related('user')
            .first()
        )
        if not member:
            return None
        user = member.user
        return {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }


class PlatformMessageSerializer(serializers.ModelSerializer):
    sender = UserPublicSerializer(read_only=True)
    media_file = serializers.SerializerMethodField()
    mentioned_usernames = serializers.SerializerMethodField()

    class Meta:
        model = PlatformMessage
        fields = (
            'id', 'room', 'sender', 'content', 'message_type',
            'media_file', 'mentioned_usernames', 'created_at',
        )

    def get_media_file(self, obj):
        if not obj.media_file:
            return None
        request = self.context.get('request')
        if request:
            return build_signed_platform_media_url(request, obj.id)
        return obj.media_file.url if obj.media_file else None

    def get_mentioned_usernames(self, obj):
        return list(obj.mentions.values_list('username', flat=True))


class PlatformMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, default='')
    message_type = serializers.ChoiceField(
        choices=PlatformMessage.MessageType.choices,
        required=False,
        default=PlatformMessage.MessageType.TEXT,
    )
    media = serializers.FileField(required=False)

    def validate(self, attrs):
        media = attrs.get('media')
        content = attrs.get('content', '')
        if not media and not content.strip():
            raise serializers.ValidationError('Informe texto ou anexo.')
        return attrs


class PlatformDirectCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
