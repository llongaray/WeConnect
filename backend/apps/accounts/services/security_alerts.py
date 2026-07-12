import json
import logging
import os
from datetime import timedelta

import httpx
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('security')

ALERT_WEBHOOK_URL = os.getenv('SECURITY_ALERT_WEBHOOK_URL', '')
ALERT_TOTP_WINDOW_SECONDS = 600
ALERT_TOTP_THRESHOLD = 5


def _alert_cache_key(event_type: str, identifier: str) -> str:
    return f'security:alert:sent:{event_type}:{identifier}'


def _should_alert(event_type: str, identifier: str, cooldown_seconds: int = 300) -> bool:
    if not ALERT_WEBHOOK_URL:
        return False
    key = _alert_cache_key(event_type, identifier)
    if cache.get(key):
        return False
    cache.set(key, 1, cooldown_seconds)
    return True


def send_security_alert(title: str, payload: dict) -> None:
    if not ALERT_WEBHOOK_URL:
        return
    body = {
        'content': f'**{title}**',
        'embeds': [{
            'description': json.dumps(payload, ensure_ascii=False, indent=2)[:4000],
        }],
    }
    try:
        httpx.post(ALERT_WEBHOOK_URL, json=body, timeout=10.0)
    except httpx.HTTPError:
        logger.exception('Falha ao enviar alerta de segurança')


def maybe_alert_for_event(event_type: str, *, ip_address: str | None = None, username: str = '', metadata: dict | None = None) -> None:
    meta = metadata or {}
    if event_type == 'login_blocked':
        ident = ip_address or username or 'unknown'
        if _should_alert(event_type, ident):
            send_security_alert('Login bloqueado', {
                'ip': ip_address,
                'username': username,
                **meta,
            })
    elif event_type == 'webhook_rejected':
        ident = str(meta.get('channel_id', ip_address or 'unknown'))
        if _should_alert(event_type, ident):
            send_security_alert('Webhook rejeitado', {
                'ip': ip_address,
                **meta,
            })
    elif event_type == 'totp_failed' and username:
        key = f'totp:fail:{username}'
        count = cache.get(key) or 0
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, ALERT_TOTP_WINDOW_SECONDS)
            count = 1
        if count >= ALERT_TOTP_THRESHOLD and _should_alert('totp_failed_burst', username, 900):
            send_security_alert('Múltiplas falhas 2FA', {
                'username': username,
                'count': count,
            })
    elif event_type == 'idor_blocked':
        ident = f'{username}:{meta.get("resource", "")}'
        if _should_alert(event_type, ident, 120):
            send_security_alert('Tentativa IDOR bloqueada', {
                'username': username,
                'ip': ip_address,
                **meta,
            })
