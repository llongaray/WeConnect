from rest_framework import serializers

from .models import Channel


class ChannelSerializer(serializers.ModelSerializer):
  channel_type_label = serializers.CharField(source='get_channel_type_display', read_only=True)
  webhook_url = serializers.SerializerMethodField()

  class Meta:
    model = Channel
    fields = (
      'id', 'name', 'channel_type', 'channel_type_label', 'status', 'phone',
      'qrcode_base64', 'is_active', 'webhook_url', 'created_at', 'updated_at',
    )
    read_only_fields = (
      'id', 'status', 'phone', 'qrcode_base64', 'webhook_url',
      'created_at', 'updated_at',
    )

  def get_webhook_url(self, obj: Channel) -> str:
    from apps.whatsapp.providers.factory import get_provider
    try:
      return get_provider(obj).webhook_url()
    except (ValueError, AttributeError):
      return ''


class ChannelCreateSerializer(serializers.ModelSerializer):
  phone_number_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
  access_token = serializers.CharField(required=False, allow_blank=True, write_only=True)
  verify_token = serializers.CharField(required=False, allow_blank=True, write_only=True)
  waba_id = serializers.CharField(required=False, allow_blank=True, write_only=True)

  class Meta:
    model = Channel
    fields = (
      'name', 'channel_type',
      'phone_number_id', 'access_token', 'verify_token', 'waba_id',
    )

  def validate(self, attrs):
    channel_type = attrs.get('channel_type')
    if channel_type == Channel.ChannelType.META_CLOUD:
      if not attrs.get('phone_number_id') or not attrs.get('access_token'):
        raise serializers.ValidationError(
          'phone_number_id e access_token são obrigatórios para API Oficial Meta.'
        )
    return attrs

  def create(self, validated_data):
    meta_fields = {}
    for key in ('phone_number_id', 'access_token', 'verify_token', 'waba_id'):
      if key in validated_data:
        meta_fields[key] = validated_data.pop(key)

    from apps.whatsapp.providers.evolution import slugify_channel_name

    channel = Channel.objects.create(**validated_data)
    channel.ensure_webhook_secret()

    if channel.is_meta_cloud:
      channel.credentials = meta_fields
      channel.status = Channel.Status.CLOSE
      channel.save(update_fields=['credentials', 'status', 'updated_at'])
    else:
      instance_name = slugify_channel_name(channel.name)
      channel.credentials = {'evolution_instance_name': instance_name}
      channel.save(update_fields=['credentials', 'updated_at'])

    return channel
