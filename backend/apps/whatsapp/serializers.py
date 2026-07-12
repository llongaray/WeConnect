from rest_framework import serializers

from apps.accounts.models import Company
from apps.core.encryption import mask_secret

from .models import Channel

META_MESSAGING_CREDENTIAL_KEYS = (
  'app_id',
  'app_secret',
  'page_id',
  'page_access_token',
  'verify_token',
  'instagram_business_account_id',
  'page_name',
  'instagram_username',
)


class ChannelMetaCredentialsSerializer(serializers.Serializer):
    phone_number_id = serializers.CharField(required=False, allow_blank=True)
    access_token = serializers.SerializerMethodField()
    verify_token = serializers.SerializerMethodField()
    waba_id = serializers.CharField(required=False, allow_blank=True)

    def get_access_token(self, obj: dict) -> str:
        return mask_secret(obj.get('access_token', ''))

    def get_verify_token(self, obj: dict) -> str:
        return mask_secret(obj.get('verify_token', ''))


class ChannelMetaMessagingCredentialsSerializer(serializers.Serializer):
    app_id = serializers.CharField(required=False, allow_blank=True)
    app_secret = serializers.SerializerMethodField()
    page_id = serializers.CharField(required=False, allow_blank=True)
    page_access_token = serializers.SerializerMethodField()
    verify_token = serializers.SerializerMethodField()
    instagram_business_account_id = serializers.CharField(required=False, allow_blank=True)
    page_name = serializers.CharField(required=False, allow_blank=True)
    instagram_username = serializers.CharField(required=False, allow_blank=True)

    def get_app_secret(self, obj: dict) -> str:
        return mask_secret(obj.get('app_secret', ''))

    def get_page_access_token(self, obj: dict) -> str:
        return mask_secret(obj.get('page_access_token', ''))

    def get_verify_token(self, obj: dict) -> str:
        return mask_secret(obj.get('verify_token', ''))


class ChannelSerializer(serializers.ModelSerializer):
  channel_type_label = serializers.CharField(source='get_channel_type_display', read_only=True)
  webhook_url = serializers.SerializerMethodField()
  webhook_header = serializers.SerializerMethodField()
  meta_credentials = serializers.SerializerMethodField()
  meta_messaging_credentials = serializers.SerializerMethodField()

  class Meta:
    model = Channel
    fields = (
      'id', 'name', 'channel_type', 'channel_type_label', 'status', 'phone',
      'qrcode_base64', 'is_active', 'is_archived', 'company_id', 'webhook_url',
      'webhook_header', 'meta_credentials', 'meta_messaging_credentials',
      'created_at', 'updated_at',
    )
    read_only_fields = (
      'id', 'status', 'phone', 'qrcode_base64', 'webhook_url', 'webhook_header',
      'meta_credentials', 'meta_messaging_credentials', 'created_at', 'updated_at',
    )

  def get_webhook_header(self, obj: Channel) -> str | None:
    if obj.is_evolution:
      return 'X-Webhook-Secret'
    return None

  def get_meta_credentials(self, obj: Channel) -> dict | None:
    if not obj.is_meta_cloud or not obj.credentials:
      return None
    return ChannelMetaCredentialsSerializer(obj.credentials).data

  def get_meta_messaging_credentials(self, obj: Channel) -> dict | None:
    if not obj.is_meta_messaging or not obj.credentials:
      return None
    return ChannelMetaMessagingCredentialsSerializer(obj.credentials).data

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
  app_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
  app_secret = serializers.CharField(required=False, allow_blank=True, write_only=True)
  page_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
  page_access_token = serializers.CharField(required=False, allow_blank=True, write_only=True)
  instagram_business_account_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
  company_id = serializers.PrimaryKeyRelatedField(
    source='company',
    queryset=Company.objects.all(),
    required=False,
    allow_null=True,
  )

  class Meta:
    model = Channel
    fields = (
      'name', 'channel_type', 'company_id',
      'phone_number_id', 'access_token', 'verify_token', 'waba_id',
      'app_id', 'app_secret', 'page_id', 'page_access_token',
      'instagram_business_account_id',
    )

  def validate(self, attrs):
    channel_type = attrs.get('channel_type')
    if channel_type == Channel.ChannelType.META_CLOUD:
      if not attrs.get('phone_number_id') or not attrs.get('access_token'):
        raise serializers.ValidationError(
          'phone_number_id e access_token são obrigatórios para API Oficial Meta.'
        )
    if channel_type in (
      Channel.ChannelType.META_MESSENGER,
      Channel.ChannelType.META_INSTAGRAM,
    ):
      required = ('app_id', 'app_secret', 'page_id', 'page_access_token', 'verify_token')
      missing = [field for field in required if not attrs.get(field)]
      if missing:
        raise serializers.ValidationError(
          f'Campos obrigatórios para Meta Messaging: {", ".join(missing)}.'
        )
      if channel_type == Channel.ChannelType.META_INSTAGRAM:
        if not attrs.get('instagram_business_account_id'):
          raise serializers.ValidationError(
            'instagram_business_account_id é obrigatório para Instagram DM.'
          )
    return attrs

  def create(self, validated_data):
    meta_whatsapp_fields = {}
    for key in ('phone_number_id', 'access_token', 'verify_token', 'waba_id'):
      if key in validated_data:
        meta_whatsapp_fields[key] = validated_data.pop(key)

    meta_messaging_fields = {}
    for key in META_MESSAGING_CREDENTIAL_KEYS:
      if key in validated_data:
        meta_messaging_fields[key] = validated_data.pop(key)

    from apps.whatsapp.providers.evolution import slugify_channel_name

    channel = Channel.objects.create(**validated_data)
    channel.ensure_webhook_secret()

    if channel.is_meta_cloud:
      channel.credentials = meta_whatsapp_fields
      channel.status = Channel.Status.CLOSE
      channel.save(update_fields=['credentials', 'status', 'updated_at'])
    elif channel.is_meta_messaging:
      channel.credentials = meta_messaging_fields
      channel.status = Channel.Status.CLOSE
      channel.save(update_fields=['credentials', 'status', 'updated_at'])
    else:
      instance_name = slugify_channel_name(channel.name)
      channel.credentials = {'evolution_instance_name': instance_name}
      channel.save(update_fields=['credentials', 'updated_at'])

    return channel
