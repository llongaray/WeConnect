from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer

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
    channels = serializers.SerializerMethodField()
    memberships = TeamMembershipSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = (
            'id', 'name', 'is_active', 'channels', 'channel_ids',
            'memberships', 'members_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_channels(self, obj):
        return [{'id': ch.id, 'name': ch.name} for ch in obj.channels.all()]

    def get_members_count(self, obj):
        return obj.memberships.count()

    def create(self, validated_data):
        channel_ids = validated_data.pop('channel_ids', [])
        team = Team.objects.create(**validated_data)
        if channel_ids:
            team.channels.set(channel_ids)
        return team

    def update(self, instance, validated_data):
        channel_ids = validated_data.pop('channel_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if channel_ids is not None:
            instance.channels.set(channel_ids)
        return instance


class TeamMemberUpsertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=TeamMembership.MemberRole.choices)
