from rest_framework import serializers

from .ai_providers.factory import list_provider_types


class AIProviderUpdateSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=255, trim_whitespace=True, required=False, allow_blank=True)
    is_default = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs.get('api_key') and attrs.get('is_default') is None:
            raise serializers.ValidationError('Informe api_key ou is_default.')
        if attrs.get('api_key') is not None and not str(attrs.get('api_key', '')).strip():
            if attrs.get('is_default') is None:
                raise serializers.ValidationError({'api_key': 'Informe o API token.'})
        return attrs


class DeepSeekConfigUpdateSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=255, trim_whitespace=True)

    def validate_api_key(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Informe o API token.')
        return value.strip()


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'assistant'])
    content = serializers.CharField(max_length=8000, trim_whitespace=True)


class GenerateFlowSerializer(serializers.Serializer):
    messages = ChatMessageSerializer(many=True)
    current_flow = serializers.DictField(required=False, allow_null=True)
    provider = serializers.ChoiceField(
        choices=[(p, p) for p in list_provider_types()],
        required=False,
        allow_null=True,
    )

    def validate_messages(self, value):
        if not value:
            raise serializers.ValidationError('Informe pelo menos uma mensagem.')
        if value[-1]['role'] != 'user':
            raise serializers.ValidationError('A última mensagem deve ser do usuário.')
        return value
