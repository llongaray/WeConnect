from datetime import timedelta

from django.db.models import Q

from celery import shared_task
from django.utils import timezone

from apps.accounts.models import Company
from apps.chat.models import Contact, Conversation, ConversationEvent, Message


@shared_task(name='chat.purge_expired_data')
def purge_expired_data_task() -> dict:
    """Remove mensagens e contatos além do prazo de retenção por empresa."""
    total_messages = 0
    total_contacts = 0
    now = timezone.now()

    for company in Company.objects.filter(is_active=True):
        days = company.data_retention_days or 365
        cutoff = now - timedelta(days=days)

        old_conversations = Conversation.objects.filter(
            channel__company=company,
        ).filter(
            Q(last_message_at__lt=cutoff)
            | Q(last_message_at__isnull=True, updated_at__lt=cutoff),
        )
        conv_ids = list(old_conversations.values_list('id', flat=True))
        if conv_ids:
            deleted_msgs, _ = Message.objects.filter(conversation_id__in=conv_ids).delete()
            ConversationEvent.objects.filter(conversation_id__in=conv_ids).delete()
            old_conversations.delete()
            total_messages += deleted_msgs

        stale_contacts = Contact.objects.filter(
            channel__company=company,
            updated_at__lt=cutoff,
        ).exclude(
            id__in=Conversation.objects.filter(channel__company=company).values_list('contact_id', flat=True),
        )
        deleted_contacts, _ = stale_contacts.delete()
        total_contacts += deleted_contacts

    return {'messages_removed': total_messages, 'contacts_removed': total_contacts}
