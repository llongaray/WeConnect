"""Operações LGPD para titulares WhatsApp (contatos)."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AuditLog
from apps.accounts.services.audit import log_audit

from apps.chat.models import Contact, Conversation, ConversationEvent, Message


def export_contact_data(contact: Contact) -> dict:
    """Exporta dados do titular para portabilidade (Art. 18 V LGPD)."""
    conversations = []
    for conversation in Conversation.objects.filter(contact=contact).select_related('channel', 'assigned_to'):
        messages = [
            {
                'id': msg.id,
                'direction': msg.direction,
                'message_type': msg.message_type,
                'content': msg.content,
                'status': msg.status,
                'created_at': msg.created_at.isoformat(),
            }
            for msg in Message.objects.filter(conversation=conversation).order_by('created_at')
        ]
        events = [
            {
                'event_type': event.event_type,
                'note': event.note,
                'created_at': event.created_at.isoformat(),
            }
            for event in ConversationEvent.objects.filter(conversation=conversation).order_by('created_at')
        ]
        conversations.append({
            'id': conversation.id,
            'status': conversation.status,
            'channel': conversation.channel.name,
            'assigned_to': conversation.assigned_to.username if conversation.assigned_to else None,
            'created_at': conversation.created_at.isoformat(),
            'messages': messages,
            'events': events,
        })

    return {
        'exported_at': timezone.now().isoformat(),
        'contact': {
            'id': contact.id,
            'external_id': contact.external_id,
            'phone': contact.phone,
            'name': contact.name,
            'profile_pic_url': contact.profile_pic_url,
            'created_at': contact.created_at.isoformat(),
            'updated_at': contact.updated_at.isoformat(),
        },
        'conversations': conversations,
    }


@transaction.atomic
def erase_contact_data(contact: Contact, *, actor, request=None) -> None:
    """Exclui dados do titular e conversas associadas (Art. 18 VI LGPD)."""
    conversation_ids = list(
        Conversation.objects.filter(contact=contact).values_list('id', flat=True)
    )
    Message.objects.filter(conversation_id__in=conversation_ids).delete()
    ConversationEvent.objects.filter(conversation_id__in=conversation_ids).delete()
    Conversation.objects.filter(id__in=conversation_ids).delete()
    contact_label = contact.phone or contact.name or str(contact.id)
    company = contact.channel.company
    contact_id = contact.id
    contact.delete()
    log_audit(
        action=AuditLog.Action.DELETE,
        entity_type='contact_lgpd_erase',
        entity_id=contact_id,
        entity_label=contact_label,
        actor=actor,
        company=company,
        metadata={'conversations_removed': len(conversation_ids)},
        request=request,
    )
