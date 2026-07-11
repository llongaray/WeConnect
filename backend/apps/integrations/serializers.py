from rest_framework import serializers


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

    def validate_messages(self, value):
        if not value:
            raise serializers.ValidationError('Informe pelo menos uma mensagem.')
        if value[-1]['role'] != 'user':
            raise serializers.ValidationError('A última mensagem deve ser do usuário.')
        return value
