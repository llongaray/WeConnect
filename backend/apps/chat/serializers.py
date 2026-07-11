from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer
from apps.whatsapp.serializers import ChannelSerializer

from .models import Contact, Conversation, ConversationEvent, Message


class ContactSerializer(serializers.ModelSerializer):
  class Meta:
    model = Contact
    fields = ('id', 'external_id', 'phone', 'name', 'profile_pic_url', 'created_at', 'updated_at')
    read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
  sent_by = UserPublicSerializer(read_only=True)
  media_file = serializers.SerializerMethodField()

  class Meta:
    model = Message
    fields = (
      'id', 'conversation', 'direction', 'message_type', 'content',
      'media_file', 'media_url', 'external_id', 'status', 'sent_by', 'created_at',
    )
    read_only_fields = (
      'id', 'conversation', 'direction', 'external_id', 'status', 'sent_by', 'created_at',
    )

  def get_media_file(self, obj):
    if obj.media_file:
      request = self.context.get('request')
      if request:
        return request.build_absolute_uri(obj.media_file.url)
      return obj.media_file.url
    return None


class MessageCreateSerializer(serializers.Serializer):
  content = serializers.CharField(required=False, allow_blank=True, default='')
  message_type = serializers.ChoiceField(
    choices=Message.MessageType.choices,
    default=Message.MessageType.TEXT,
  )
  media = serializers.FileField(required=False, allow_null=True)


class ConversationEventSerializer(serializers.ModelSerializer):
  actor = UserPublicSerializer(read_only=True)
  from_user = UserPublicSerializer(read_only=True)
  to_user = UserPublicSerializer(read_only=True)

  class Meta:
    model = ConversationEvent
    fields = (
      'id', 'event_type', 'actor', 'from_user', 'to_user', 'note', 'created_at',
    )
    read_only_fields = fields


class TeamMinimalSerializer(serializers.Serializer):
  id = serializers.IntegerField()
  name = serializers.CharField()


class ConversationSerializer(serializers.ModelSerializer):
  contact = ContactSerializer(read_only=True)
  channel = ChannelSerializer(read_only=True)
  assigned_to = UserPublicSerializer(read_only=True)
  closed_by = UserPublicSerializer(read_only=True)
  team = serializers.SerializerMethodField()
  recent_events = serializers.SerializerMethodField()

  class Meta:
    model = Conversation
    fields = (
      'id', 'channel', 'contact', 'team', 'assigned_to', 'assigned_at', 'status',
      'handoff_pending', 'closed_at', 'closed_by', 'unread_count',
      'last_message_at', 'last_message_preview', 'recent_events',
      'created_at', 'updated_at',
    )
    read_only_fields = fields

  def get_team(self, obj):
    if not obj.team_id:
      return None
    return {'id': obj.team_id, 'name': obj.team.name}

  def get_recent_events(self, obj):
    events = getattr(obj, '_prefetched_events', None)
    if events is None:
      events = obj.events.select_related('actor', 'from_user', 'to_user')[:5]
    return ConversationEventSerializer(events, many=True).data


class TransferSerializer(serializers.Serializer):
  assigned_to_id = serializers.IntegerField()
  note = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)


class CloseSerializer(serializers.Serializer):
  farewell_message = serializers.CharField(required=False, allow_blank=True, default='', max_length=2000)
