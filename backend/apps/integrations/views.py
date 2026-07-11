from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin

from .deepseek_client import DeepSeekAPIError, DeepSeekNotConnectedError
from .flow_generator import generate_bot_flow
from .models import DeepSeekConfig
from .serializers import DeepSeekConfigUpdateSerializer, GenerateFlowSerializer
from .services import build_config_response, save_deepseek_config


class DeepSeekConfigView(APIView):
    """GET/PATCH da configuração global DeepSeek (singleton)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        config = DeepSeekConfig.get_singleton()
        return Response(build_config_response(config))

    def patch(self, request):
        serializer = DeepSeekConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        config, success, error_msg = save_deepseek_config(serializer.validated_data['api_key'])
        data = build_config_response(config)

        if not success:
            return Response(
                {**data, 'detail': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(data)

    def put(self, request):
        return self.patch(request)


class GenerateFlowView(APIView):
    """Gera fluxo de chatbot via DeepSeek a partir de conversa."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = GenerateFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = generate_bot_flow(
                messages=serializer.validated_data['messages'],
                current_flow=serializer.validated_data.get('current_flow'),
            )
            return Response(result)
        except DeepSeekNotConnectedError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except DeepSeekAPIError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
