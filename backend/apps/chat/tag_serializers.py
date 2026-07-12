from rest_framework import serializers

from .models import Tag


class TagSerializer(serializers.ModelSerializer):
  contacts_count = serializers.SerializerMethodField()

  class Meta:
    model = Tag
    fields = (
      'id', 'name', 'color', 'funnel_order', 'is_active',
      'contacts_count', 'created_at', 'updated_at',
    )
    read_only_fields = ('id', 'contacts_count', 'created_at', 'updated_at')

  def get_contacts_count(self, obj: Tag) -> int:
    return obj.assignments.count()


class TagCreateUpdateSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('name', 'color', 'funnel_order', 'is_active')

  def validate_name(self, value: str) -> str:
    name = value.strip()
    if not name:
      raise serializers.ValidationError('Nome da tag é obrigatório.')
    return name


class ContactTagSerializer(serializers.Serializer):
  id = serializers.IntegerField()
  name = serializers.CharField()
  color = serializers.CharField()


class ConversationTagAssignSerializer(serializers.Serializer):
  tag_id = serializers.IntegerField()
