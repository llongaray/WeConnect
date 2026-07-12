"""Validação de uploads do chat interno da plataforma (até 100 MB)."""

import mimetypes
import os

from rest_framework.exceptions import ValidationError

ALLOWED_PLATFORM_CHAT_MIMES = frozenset({
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
    'audio/ogg',
    'audio/mpeg',
    'audio/mp4',
    'audio/aac',
    'application/zip',
    'application/x-zip-compressed',
})

ALLOWED_PLATFORM_CHAT_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.webp', '.gif',
    '.ogg', '.mp3', '.m4a', '.aac',
    '.zip',
})

MAX_PLATFORM_CHAT_BYTES = 100 * 1024 * 1024


def validate_platform_chat_media(uploaded_file) -> str:
    """Valida arquivo e retorna message_type inferido."""
    if not uploaded_file:
        raise ValidationError({'media': 'Arquivo obrigatório.'})

    if uploaded_file.size > MAX_PLATFORM_CHAT_BYTES:
        raise ValidationError({'media': 'Arquivo excede o limite de 100 MB.'})

    name = os.path.basename(uploaded_file.name or '')
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_PLATFORM_CHAT_EXTENSIONS:
        raise ValidationError({'media': 'Tipo de arquivo não permitido.'})

    content_type = getattr(uploaded_file, 'content_type', '') or mimetypes.guess_type(name)[0] or ''
    if content_type and content_type not in ALLOWED_PLATFORM_CHAT_MIMES:
        raise ValidationError({'media': f'Tipo MIME não permitido: {content_type}.'})

    if ext in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
        return 'image'
    if ext in {'.ogg', '.mp3', '.m4a', '.aac'}:
        return 'audio'
    return 'file'
