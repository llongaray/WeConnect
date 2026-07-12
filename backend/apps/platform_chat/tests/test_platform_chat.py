import io
import zipfile
from unittest.mock import patch

from django_otp.plugins.otp_totp.models import TOTPDevice

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.platform_chat.models import PlatformMessage, PlatformRoom
from apps.platform_chat.services import (
    GENERAL_ROOM_SLUG,
    get_or_create_direct_room,
    get_or_create_general_room,
    parse_mentions,
)

User = get_user_model()


class PlatformChatAccessTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_user(
            username='admin_chat',
            password='pass12345',
            is_superuser=True,
            is_staff=True,
            role='gestor',
        )
        self.support = User.objects.create_user(
            username='support_chat',
            password='pass12345',
            is_staff=True,
            is_superuser=False,
            role='gestor',
        )
        self.gestor = User.objects.create_user(
            username='gestor_chat',
            password='pass12345',
            role='gestor',
        )
        self.client = APIClient()
        TOTPDevice.objects.create(user=self.superuser, name='default', confirmed=True)
        TOTPDevice.objects.create(user=self.support, name='default', confirmed=True)

    def test_gestor_cannot_access_platform_chat(self):
        self.client.force_authenticate(self.gestor)
        response = self.client.get('/api/v1/platform-chat/rooms/')
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_list_rooms(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get('/api/v1/platform-chat/rooms/')
        self.assertEqual(response.status_code, 200)
        slugs = [item.get('slug') for item in response.data['results']]
        self.assertIn(GENERAL_ROOM_SLUG, slugs)

    def test_mention_parsing(self):
        mentioned = parse_mentions(f'Olá @{self.support.username} urgente')
        self.assertEqual(len(mentioned), 1)
        self.assertEqual(mentioned[0].username, self.support.username)

    def test_direct_room_unique(self):
        room1 = get_or_create_direct_room(self.superuser, self.support)
        room2 = get_or_create_direct_room(self.support, self.superuser)
        self.assertEqual(room1.id, room2.id)
        self.assertEqual(PlatformRoom.objects.filter(kind=PlatformRoom.Kind.DIRECT).count(), 1)

    def test_send_message_with_mention(self):
        self.client.force_authenticate(self.superuser)
        room = get_or_create_general_room()
        response = self.client.post(
            f'/api/v1/platform-chat/rooms/{room.id}/messages/',
            {'content': f'Ping @{self.support.username}'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        message = PlatformMessage.objects.get(pk=response.data['id'])
        self.assertIn(self.support.username, message.mentions.values_list('username', flat=True))

    @override_settings(MEDIA_ROOT='/tmp/weconnect_test_media')
    def test_upload_image_accepted(self):
        self.client.force_authenticate(self.superuser)
        room = get_or_create_general_room()
        image = SimpleUploadedFile('test.png', b'\x89PNG\r\n', content_type='image/png')
        response = self.client.post(
            f'/api/v1/platform-chat/rooms/{room.id}/messages/',
            {'content': 'foto', 'media': image},
            format='multipart',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['message_type'], 'image')

    @override_settings(MEDIA_ROOT='/tmp/weconnect_test_media')
    def test_upload_zip_accepted(self):
        self.client.force_authenticate(self.superuser)
        room = get_or_create_general_room()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            zf.writestr('a.txt', 'hello')
        buffer.seek(0)
        archive = SimpleUploadedFile('pacote.zip', buffer.read(), content_type='application/zip')
        response = self.client.post(
            f'/api/v1/platform-chat/rooms/{room.id}/messages/',
            {'content': 'arquivo', 'media': archive},
            format='multipart',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['message_type'], 'file')

    def test_upload_oversized_rejected(self):
        self.client.force_authenticate(self.superuser)
        room = get_or_create_general_room()
        archive = SimpleUploadedFile('big.zip', b'x', content_type='application/zip')
        with patch.object(archive, 'size', 101 * 1024 * 1024):
            response = self.client.post(
                f'/api/v1/platform-chat/rooms/{room.id}/messages/',
                {'media': archive},
                format='multipart',
            )
        self.assertEqual(response.status_code, 400)
