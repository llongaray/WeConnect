from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer
from apps.accounts.models import Company
from apps.accounts.services.tenant_scope import validate_channel_ids_for_company, validate_entities_same_company

from .models import Team, TeamMembership


class TeamMembershipSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TeamMembership
        fields = ('id', 'user', 'user_id', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')


class TeamSerializer(serializers.ModelSerializer):
    channel_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )
    company_id = serializers.PrimaryKeyRelatedField(
        source='company',
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )
    channels = serializers.SerializerMethodField()
    memberships = TeamMembershipSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = (
            'id', 'name', 'is_active', 'company_id', 'channels', 'channel_ids',
            'memberships', 'members_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_channels(self, obj):
        return [{'id': ch.id, 'name': ch.name} for ch in obj.channels.all()]

    def get_members_count(self, obj):
        return obj.memberships.count()

    def validate(self, attrs):
        request = self.context.get('request')
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        if request and request.user.is_gestor:
            company = request.user.company
            attrs['company'] = company

        channel_ids = attrs.get('channel_ids')
        if channel_ids is not None and company is not None:
            validate_channel_ids_for_company(channel_ids, company)

        new_company = attrs.get('company')
        if new_company is not None and self.instance is not None:
            validate_entities_same_company(self.instance, company=new_company)

        return attrs

    def create(self, validated_data):
        channel_ids = validated_data.pop('channel_ids', [])
        company = validated_data.get('company')
        if company and channel_ids:
            validate_channel_ids_for_company(channel_ids, company)
        team = Team.objects.create(**validated_data)
        if channel_ids:
            team.channels.set(channel_ids)
        return team

    def update(self, instance, validated_data):
        channel_ids = validated_data.pop('channel_ids', None)
        company = validated_data.get('company', instance.company)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if company:
            validate_entities_same_company(instance, company=company)
        instance.save()
        if channel_ids is not None:
            validate_channel_ids_for_company(channel_ids, company)
            instance.channels.set(channel_ids)
        return instance


class TeamMemberUpsertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=TeamMembership.MemberRole.choices)
