"""Validação de uploads de mídia no chat."""

import mimetypes
import os

from rest_framework.exceptions import ValidationError

ALLOWED_MEDIA_MIMES = frozenset({
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
    'audio/ogg',
    'audio/mpeg',
    'audio/mp4',
    'audio/aac',
    'video/mp4',
    'application/pdf',
})

ALLOWED_MEDIA_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.webp', '.gif',
    '.ogg', '.mp3', '.m4a', '.aac',
    '.mp4', '.pdf',
})

MAX_MEDIA_BYTES = 16 * 1024 * 1024


def validate_uploaded_media(uploaded_file) -> None:
    """Valida tamanho, extensão e MIME de arquivo enviado."""
    if not uploaded_file:
        return

    if uploaded_file.size > MAX_MEDIA_BYTES:
        raise ValidationError({'media': 'Arquivo excede o limite de 16 MB.'})

    name = os.path.basename(uploaded_file.name or '')
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        raise ValidationError({'media': 'Tipo de arquivo não permitido.'})

    content_type = getattr(uploaded_file, 'content_type', '') or mimetypes.guess_type(name)[0] or ''
    if content_type and content_type not in ALLOWED_MEDIA_MIMES:
        raise ValidationError({'media': f'Tipo MIME não permitido: {content_type}.'})
