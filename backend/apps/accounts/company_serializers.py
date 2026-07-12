from rest_framework import serializers

from .models import AuditLog, Company, SecurityEvent, User
from .services.capabilities import is_platform_admin, is_platform_operator
from .validators import validate_user_password


class CompanyUsageSerializer(serializers.Serializer):
    supervisors = serializers.IntegerField()
    atendentes = serializers.IntegerField()
    gestores = serializers.IntegerField()
    teams = serializers.IntegerField()
    channels = serializers.IntegerField()
    limits = serializers.DictField()


class CompanySerializer(serializers.ModelSerializer):
    usage = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = (
            'id', 'code', 'legal_name', 'trade_name', 'cnpj', 'address',
            'contact_email', 'billing_email', 'contact_phone', 'billing_phone',
            'dpo_name', 'dpo_email', 'data_retention_days',
            'is_active', 'max_supervisors', 'max_atendentes', 'max_teams', 'max_channels',
            'usage', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'code', 'created_at', 'updated_at', 'usage')

    def get_usage(self, obj):
        return obj.usage_summary()


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'legal_name', 'trade_name', 'cnpj', 'address',
            'contact_email', 'billing_email', 'contact_phone', 'billing_phone',
            'max_supervisors', 'max_atendentes', 'max_teams', 'max_channels',
        )

    def create(self, validated_data):
        validated_data['code'] = Company.generate_unique_code()
        return Company.objects.create(**validated_data)


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'legal_name', 'trade_name', 'cnpj', 'address',
            'contact_email', 'billing_email', 'contact_phone', 'billing_phone',
            'dpo_name', 'dpo_email', 'data_retention_days',
            'is_active', 'max_supervisors', 'max_atendentes', 'max_teams', 'max_channels',
        )


class GestorCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_password(self, value):
        validate_user_password(value)
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            'id', 'actor', 'actor_name', 'company', 'action', 'entity_type',
            'entity_id', 'entity_label', 'metadata', 'ip_address', 'created_at',
        )
        read_only_fields = fields

    def get_actor_name(self, obj):
        if not obj.actor:
            return 'Sistema'
        return obj.actor.get_full_name() or obj.actor.username


class UserSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source='company',
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )
    is_superuser = serializers.BooleanField(required=False)
    platform_type = serializers.ChoiceField(
        choices=[('superuser', 'Superuser'), ('support', 'Suporte WeConnect')],
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'cpf', 'phone', 'company_id', 'is_active', 'is_superuser', 'platform_type', 'password',
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'is_active': {'required': False},
        }

    def validate_password(self, value):
        if value:
            validate_user_password(value)
        return value

    def validate(self, attrs):
        role = attrs.get('role', getattr(self.instance, 'role', None))
        company = attrs.get('company', getattr(self.instance, 'company', None))
        is_superuser = attrs.get('is_superuser', getattr(self.instance, 'is_superuser', False))
        platform_type = attrs.pop('platform_type', None)
        request = self.context.get('request')

        if platform_type == 'superuser':
            is_superuser = True
            attrs['is_superuser'] = True

        if is_superuser:
            if not request or not request.user.is_superuser:
                raise serializers.ValidationError({'is_superuser': 'Apenas superuser pode criar outro superuser.'})
            attrs['company'] = None
            attrs['role'] = User.Role.GESTOR
            return attrs

        if platform_type == 'support':
            if not request or not request.user.is_superuser:
                raise serializers.ValidationError({'platform_type': 'Apenas superuser pode criar suporte técnico.'})
            attrs['company'] = None
            attrs['is_superuser'] = False
            attrs['is_staff'] = True
            attrs['role'] = User.Role.GESTOR
            return attrs

        if request and request.user.is_gestor:
            attrs['company'] = request.user.company
            company = request.user.company
            if role == User.Role.GESTOR:
                raise serializers.ValidationError({'role': 'Gestor não pode criar outro gestor.'})
            if is_superuser:
                raise serializers.ValidationError({'is_superuser': 'Gestor não pode criar usuários de plataforma.'})

        if request and is_platform_operator(request.user) and not is_platform_admin(request.user):
            if is_superuser:
                raise serializers.ValidationError({'is_superuser': 'Suporte técnico não pode criar superuser.'})
            if role == User.Role.GESTOR and not company:
                raise serializers.ValidationError({'company_id': 'Gestor deve estar vinculado a uma empresa.'})
        elif request and is_platform_admin(request.user):
            if role == User.Role.GESTOR and not company:
                raise serializers.ValidationError({'company_id': 'Gestor deve estar vinculado a uma empresa.'})

        if role in (User.Role.GESTOR, User.Role.SUPERVISOR, User.Role.ATENDENTE) and not company:
            raise serializers.ValidationError({'company_id': 'Colaborador deve estar vinculado a uma empresa.'})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserPublicSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'cpf', 'phone', 'is_active', 'is_superuser', 'is_staff', 'company',
        )

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            'id': obj.company_id,
            'code': obj.company.code,
            'trade_name': obj.company.trade_name,
        }


class UserProfileSerializer(UserPublicSerializer):
    """Perfil próprio — mesmos campos públicos, sem dados administrativos extras."""

    class Meta(UserPublicSerializer.Meta):
        read_only_fields = ('id', 'username', 'role', 'is_active', 'is_superuser', 'company', 'cpf')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')

    def validate_email(self, value):
        if not value:
            return value
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Este e-mail já está em uso.')
        return value


class SecurityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityEvent
        fields = (
            'id', 'event_type', 'ip_address', 'username', 'channel_id',
            'metadata', 'created_at',
        )
        read_only_fields = fields
