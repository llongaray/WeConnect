from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Company
from apps.accounts.permissions import IsGestorOrSuperUser
from apps.accounts.throttles import DeepSeekRateThrottle

from .flow_generator import generate_bot_flow
from .serializers import (
    AIProviderUpdateSerializer,
    DeepSeekConfigUpdateSerializer,
    GenerateFlowSerializer,
)
from .services import (
    AIAPIError,
    AINotConnectedError,
    build_catalog_response,
    build_provider_response,
    disconnect_provider,
    save_deepseek_config,
    save_provider_config,
)


def resolve_company(request) -> Company | None:
    user = request.user
    if user.is_superuser:
        company_id = request.query_params.get('company_id') or request.data.get('company_id')
        if company_id:
            return Company.objects.filter(pk=company_id).first()
        return None
    return user.company


class AIProviderListView(APIView):
    """Lista canais de IA disponíveis e configurados por empresa."""

    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]

    def get(self, request):
        company = resolve_company(request)
        if not company:
            return Response({'detail': 'Informe company_id.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(build_catalog_response(company))


class AIProviderDetailView(APIView):
    """Configura um canal de IA específico."""

    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]

    def patch(self, request, provider_type):
        company = resolve_company(request)
        if not company:
            return Response({'detail': 'Informe company_id.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AIProviderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'api_key' in data and data['api_key']:
            config, success, error_msg = save_provider_config(
                company,
                provider_type,
                data['api_key'],
                is_default=data.get('is_default'),
            )
            payload = build_provider_response(config)
            if not success:
                return Response({**payload, 'detail': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response(payload)

        if data.get('is_default') is True:
            from .models import AIProviderConfig
            config = AIProviderConfig.get_for_company(company, provider_type)
            if config.status != AIProviderConfig.Status.CONNECTED or not config.get_api_key_plain():
                return Response(
                    {'detail': 'Conecte o canal antes de defini-lo como padrão.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            AIProviderConfig.objects.filter(company=company, is_default=True).update(is_default=False)
            config.is_default = True
            config.save()
            return Response(build_provider_response(config))

        return Response({'detail': 'Informe api_key válido.'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, provider_type):
        return self.patch(request, provider_type)

    def delete(self, request, provider_type):
        company = resolve_company(request)
        if not company:
            return Response({'detail': 'Informe company_id.'}, status=status.HTTP_400_BAD_REQUEST)
        config = disconnect_provider(company, provider_type)
        return Response(build_provider_response(config))


class DeepSeekConfigView(APIView):
    """Compatibilidade legada com endpoint DeepSeek."""

    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]

    def get(self, request):
        company = resolve_company(request)
        if not company:
            return Response({'detail': 'Informe company_id.'}, status=status.HTTP_400_BAD_REQUEST)
        from .models import AIProviderConfig
        config = AIProviderConfig.get_for_company(company, 'deepseek')
        return Response(build_provider_response(config))

    def patch(self, request):
        company = resolve_company(request)
        if not company:
            return Response({'detail': 'Informe company_id.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DeepSeekConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        config, success, error_msg = save_deepseek_config(
            company,
            serializer.validated_data['api_key'],
        )
        data = build_provider_response(config)

        if not success:
            return Response({**data, 'detail': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def put(self, request):
        return self.patch(request)


class GenerateFlowView(APIView):
    """Gera fluxo de chatbot via canal de IA configurado."""

    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]
    throttle_classes = [DeepSeekRateThrottle]

    def post(self, request):
        serializer = GenerateFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        company = resolve_company(request)
        if not company:
            return Response({'detail': 'Informe company_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = generate_bot_flow(
                messages=serializer.validated_data['messages'],
                current_flow=serializer.validated_data.get('current_flow'),
                company=company,
                provider_type=serializer.validated_data.get('provider'),
            )
            return Response(result)
        except AINotConnectedError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIAPIError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
