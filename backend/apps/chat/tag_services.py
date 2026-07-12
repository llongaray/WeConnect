"""Serviços de tags por contato e funil."""

from collections import defaultdict

from django.db.models import Count, Max, Q

from apps.chat.contact_keys import resolve_contact_key
from apps.chat.models import Contact, ContactTag, Conversation, Tag


def tags_for_contact_key(company_id: int, contact_key: str) -> list[Tag]:
  return list(
    Tag.objects.filter(
      company_id=company_id,
      is_active=True,
      assignments__contact_key=contact_key,
    ).order_by('-funnel_order', 'name')
  )


def tags_for_contact(contact: Contact) -> list[Tag]:
  company_id = contact.channel.company_id
  contact_key = resolve_contact_key(contact)
  return tags_for_contact_key(company_id, contact_key)


def assign_tag_to_contact(contact: Contact, tag: Tag, user) -> ContactTag:
  if tag.company_id != contact.channel.company_id:
    raise ValueError('Tag não pertence à empresa do contato.')
  contact_key = resolve_contact_key(contact)
  assignment, _ = ContactTag.objects.get_or_create(
    tag=tag,
    contact_key=contact_key,
    defaults={'created_by': user},
  )
  return assignment


def remove_tag_from_contact(contact: Contact, tag: Tag) -> None:
  contact_key = resolve_contact_key(contact)
  ContactTag.objects.filter(tag=tag, contact_key=contact_key).delete()


def funnel_stages_for_company(company_id: int) -> list[dict]:
  """Etapas do funil com contatos agrupados pela tag de maior ordem."""
  stages = list(
    Tag.objects.filter(company_id=company_id, is_active=True, funnel_order__gt=0)
    .order_by('funnel_order', 'name')
  )
  if not stages:
    return []

  assignments = ContactTag.objects.filter(
    tag__company_id=company_id,
    tag__is_active=True,
    tag__funnel_order__gt=0,
  ).select_related('tag')

  contact_best: dict[str, Tag] = {}
  for assignment in assignments:
    key = assignment.contact_key
    current = contact_best.get(key)
    if not current or assignment.tag.funnel_order > current.funnel_order:
      contact_best[key] = assignment.tag

  stage_contacts: dict[int, list[str]] = defaultdict(list)
  for contact_key, tag in contact_best.items():
    stage_contacts[tag.id].append(contact_key)

  active_counts = {
    row['contact__phone']: row['total']
    for row in Conversation.objects.filter(
      channel__company_id=company_id,
      status__in=[Conversation.Status.OPEN, Conversation.Status.BOT],
    ).values('contact__phone').annotate(total=Count('id'))
    if row['contact__phone']
  }

  result = []
  for stage in stages:
    keys = stage_contacts.get(stage.id, [])
    contacts_payload = []
    for key in keys:
      contact = (
        Contact.objects.filter(channel__company_id=company_id)
        .filter(Q(phone=key) | Q(external_id=key))
        .select_related('channel')
        .order_by('-updated_at')
        .first()
      )
      contacts_payload.append({
        'contact_key': key,
        'name': contact.name if contact else key,
        'phone': contact.phone if contact else key,
        'channel_name': contact.channel.name if contact else '',
        'active_conversations': active_counts.get(contact.phone if contact else '', 0),
      })
    result.append({
      'tag': {
        'id': stage.id,
        'name': stage.name,
        'color': stage.color,
        'funnel_order': stage.funnel_order,
      },
      'contacts_count': len(keys),
      'contacts': contacts_payload,
    })
  return result
