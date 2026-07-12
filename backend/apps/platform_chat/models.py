from django.conf import settings
from django.db import models


class PlatformRoom(models.Model):
    """Sala de chat interno da equipe WeConnect (grupo ou DM)."""

    class Kind(models.TextChoices):
        GROUP = 'group', 'Grupo'
        DIRECT = 'direct', 'Privado'

    kind = models.CharField(max_length=10, choices=Kind.choices)
    name = models.CharField(max_length=120, blank=True, default='')
    slug = models.SlugField(max_length=80, unique=True, null=True, blank=True)
    direct_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name or self.slug or f'Sala {self.pk}'


class PlatformRoomMember(models.Model):
    room = models.ForeignKey(
        PlatformRoom,
        on_delete=models.CASCADE,
        related_name='members',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_chat_memberships',
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['room', 'user'], name='uniq_platform_room_member'),
        ]

    def __str__(self):
        return f'{self.user_id} em {self.room_id}'


class PlatformMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Texto'
        IMAGE = 'image', 'Imagem'
        AUDIO = 'audio', 'Áudio'
        FILE = 'file', 'Arquivo'

    room = models.ForeignKey(
        PlatformRoom,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_chat_messages',
    )
    content = models.TextField(blank=True, default='')
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    media_file = models.FileField(upload_to='platform_chat/', blank=True)
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='platform_chat_mentioned_in',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Msg {self.pk} em sala {self.room_id}'


class PlatformReadState(models.Model):
    room = models.ForeignKey(
        PlatformRoom,
        on_delete=models.CASCADE,
        related_name='read_states',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_chat_read_states',
    )
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['room', 'user'], name='uniq_platform_read_state'),
        ]
