from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.mixins import CompanyScopedMixin
from apps.accounts.models import AuditLog, User
from apps.accounts.permissions import IsGestorOrSuperUser
from apps.accounts.services.capabilities import is_platform_admin, is_platform_operator
from apps.accounts.serializers import UserPublicSerializer, UserSerializer
from apps.accounts.services.audit import log_audit, sanitize_metadata
from apps.accounts.services.limits import assert_can_create_user_role
from apps.accounts.services.token_revocation import revoke_user_tokens
from apps.accounts.services.trusted_device import revoke_all_trusted_devices


class UserViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsGestorOrSuperUser]
    company_field = 'company'
    superuser_requires_company = False

    def get_queryset(self):
        if self.request.query_params.get('scope') == 'platform' and is_platform_admin(self.request.user):
            qs = User.objects.filter(
                Q(is_superuser=True)
                | Q(is_staff=True, is_superuser=False, company__isnull=True),
            ).select_related('company').order_by('username')
            search = self.request.query_params.get('search')
            if search:
                qs = qs.filter(
                    Q(username__icontains=search)
                    | Q(first_name__icontains=search)
                    | Q(last_name__icontains=search)
                    | Q(email__icontains=search)
                )
            return qs

        if is_platform_operator(self.request.user) and not self.request.query_params.get('company_id'):
            raise ValidationError({'company_id': 'Informe company_id para listar usuários da empresa.'})

        qs = User.objects.filter(is_superuser=False).select_related('company').order_by('username')
        qs = self.filter_queryset_by_company(qs)

        company_id = self.request.query_params.get('company_id')
        if company_id and is_platform_operator(self.request.user):
            qs = qs.filter(company_id=company_id)

        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )
        return qs

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserPublicSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        user = self.request.user
        company = serializer.validated_data.get('company')
        is_platform_user = serializer.validated_data.get('is_superuser', False)
        platform_type = self.request.data.get('platform_type')

        if platform_type == 'support':
            if not is_platform_admin(user):
                raise ValidationError({'platform_type': 'Apenas superuser pode criar suporte técnico.'})
            instance = serializer.save(
                company=None,
                is_superuser=False,
                is_staff=True,
                role=User.Role.GESTOR,
            )
            log_audit(
                action=AuditLog.Action.CREATE,
                entity_type='user',
                entity_id=instance.id,
                entity_label=instance.username,
                actor=user,
                company=None,
                metadata={'scope': 'platform', 'platform_type': 'support'},
                request=self.request,
            )
            return

        if is_platform_user and not is_platform_admin(user):
            raise ValidationError({'is_superuser': 'Apenas superuser pode criar usuário de plataforma.'})
        if is_platform_user:
            instance = serializer.save(
                company=None,
                is_superuser=True,
                is_staff=True,
                role=User.Role.GESTOR,
            )
            log_audit(
                action=AuditLog.Action.CREATE,
                entity_type='user',
                entity_id=instance.id,
                entity_label=instance.username,
                actor=user,
                company=None,
                metadata={'scope': 'platform', 'is_superuser': True},
                request=self.request,
            )
            return

        if user.is_gestor:
            company = user.company
            serializer.validated_data['company'] = company

        if not company:
            raise ValidationError({'company_id': 'Informe a empresa do colaborador.'})

        assert_can_create_user_role(company, serializer.validated_data['role'])
        instance = serializer.save(company=company)

        log_audit(
            action=AuditLog.Action.CREATE,
            entity_type='user',
            entity_id=instance.id,
            entity_label=instance.username,
            actor=user,
            company=company,
            metadata={'role': instance.role},
            request=self.request,
        )

    def perform_update(self, serializer):
        actor = self.request.user
        if not is_platform_admin(actor):
            if serializer.validated_data.get('is_superuser'):
                raise ValidationError({'is_superuser': 'Sem permissão para alterar superuser.'})
            if getattr(serializer.instance, 'is_staff', False) and actor.is_gestor:
                raise ValidationError({'detail': 'Gestor não pode alterar usuário de suporte.'})
        was_active = serializer.instance.is_active
        password_changed = 'password' in serializer.validated_data and serializer.validated_data['password']
        instance = serializer.save()
        if was_active and not instance.is_active:
            revoke_user_tokens(instance.id)
            revoke_all_trusted_devices(instance)
        if password_changed:
            revoke_user_tokens(instance.id)
            revoke_all_trusted_devices(instance)
        log_audit(
            action=AuditLog.Action.UPDATE,
            entity_type='user',
            entity_id=instance.id,
            entity_label=instance.username,
            actor=self.request.user,
            company=instance.company,
            metadata=sanitize_metadata(dict(serializer.validated_data)),
            request=self.request,
        )

    def perform_destroy(self, instance):
        if instance.is_gestor and User.objects.filter(
            company=instance.company,
            role=User.Role.GESTOR,
            is_active=True,
        ).exclude(pk=instance.pk).count() == 0:
            raise ValidationError({'detail': 'Não é possível excluir o único gestor da empresa.'})

        log_audit(
            action=AuditLog.Action.DELETE,
            entity_type='user',
            entity_id=instance.id,
            entity_label=instance.username,
            actor=self.request.user,
            company=instance.company,
            request=self.request,
        )
        instance.delete()
