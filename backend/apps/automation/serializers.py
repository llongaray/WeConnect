from rest_framework import serializers

from apps.accounts.services.tenant_scope import validate_channel_for_company
from apps.whatsapp.models import Channel

from .flow_validation import validate_flow_definition
from .models import BotFlow


class BotFlowSerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(source='channel.name', read_only=True)

    class Meta:
        model = BotFlow
        fields = [
            'id',
            'channel',
            'channel_name',
            'name',
            'is_active',
            'definition',
            'start_node_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class BotFlowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotFlow
        fields = ['channel', 'name', 'is_active', 'definition', 'start_node_id']

    def validate_channel(self, channel: Channel):
        company = self.context.get('company')
        if company is not None:
            validate_channel_for_company(channel, company)
        if BotFlow.objects.filter(channel=channel).exists():
            raise serializers.ValidationError('Este canal já possui um fluxo de chatbot.')
        return channel

    def validate_definition(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('definition deve ser um objeto JSON.')
        nodes = value.get('nodes', [])
        if not isinstance(nodes, list):
            raise serializers.ValidationError('definition.nodes deve ser uma lista.')
        return value


class BotFlowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotFlow
        fields = ['name', 'is_active', 'definition', 'start_node_id']

    def validate(self, attrs):
        definition = attrs.get('definition', self.instance.definition if self.instance else {})
        start_node_id = attrs.get('start_node_id', getattr(self.instance, 'start_node_id', ''))

        if attrs.get('is_active') and definition:
            error = validate_flow_definition(definition, start_node_id)
            if error:
                raise serializers.ValidationError({'definition': error})
        return attrs
