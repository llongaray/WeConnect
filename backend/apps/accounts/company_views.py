from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.company_serializers import (
    AuditLogSerializer,
    CompanyCreateSerializer,
    CompanySerializer,
    CompanyUpdateSerializer,
    GestorCreateSerializer,
    UserPublicSerializer,
)
from apps.accounts.models import AuditLog, Company, User
from apps.accounts.permissions import CanManageCompanies, IsSuperUser
from apps.accounts.services.audit import log_audit, sanitize_metadata
from apps.accounts.services.cnpj_lookup import lookup_cnpj
from apps.accounts.services.token_revocation import revoke_company_user_tokens
from apps.accounts.throttles import CnpjLookupRateThrottle


class CompanyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageCompanies]
    queryset = Company.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyCreateSerializer
        if self.action in ('update', 'partial_update'):
            return CompanyUpdateSerializer
        return CompanySerializer

    def perform_create(self, serializer):
        company = serializer.save()
        log_audit(
            action=AuditLog.Action.CREATE,
            entity_type='company',
            entity_id=company.id,
            entity_label=company.trade_name,
            actor=self.request.user,
            company=company,
            metadata={'code': company.code},
            request=self.request,
        )

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        company = serializer.save()
        if was_active and not company.is_active:
            revoke_company_user_tokens(company.id)
        log_audit(
            action=AuditLog.Action.UPDATE,
            entity_type='company',
            entity_id=company.id,
            entity_label=company.trade_name,
            actor=self.request.user,
            company=company,
            metadata=sanitize_metadata(dict(serializer.validated_data)),
            request=self.request,
        )

    @action(detail=True, methods=['post'], url_path='gestor')
    def create_gestor(self, request, pk=None):
        company = self.get_object()
        if User.objects.filter(company=company, role=User.Role.GESTOR, is_active=True).exists():
            return Response(
                {'detail': 'Esta empresa já possui um gestor ativo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GestorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if User.objects.filter(username=data['username']).exists():
            return Response({'detail': 'Nome de usuário já existe.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email', ''),
            cpf=data.get('cpf', ''),
            phone=data.get('phone', ''),
            role=User.Role.GESTOR,
            company=company,
        )

        log_audit(
            action=AuditLog.Action.CREATE,
            entity_type='user',
            entity_id=user.id,
            entity_label=user.username,
            actor=request.user,
            company=company,
            metadata={'role': user.role},
            request=request,
        )

        return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        url_path='lookup-cnpj',
        throttle_classes=[CnpjLookupRateThrottle],
    )
    def lookup_cnpj_action(self, request):
        """Consulta razão social, nome fantasia e endereço pelo CNPJ."""
        cnpj = request.query_params.get('cnpj', '')
        return Response(lookup_cnpj(cnpj))


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser:
            return AuditLog.objects.none()
        qs = AuditLog.objects.select_related('actor', 'company').order_by('-created_at')
        company_id = self.request.query_params.get('company_id')
        if company_id:
            qs = qs.filter(company_id=company_id)
        action_filter = self.request.query_params.get('action')
        if action_filter:
            qs = qs.filter(action=action_filter)
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        return qs
