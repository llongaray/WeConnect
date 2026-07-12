"""Categorias derivadas do ciclo de vida da conversa."""

from django.db.models import Q

from .models import Conversation


class ConversationCategory:
  NOVO = 'novo'
  AGUARDANDO = 'aguardando'
  CONVERSANDO = 'conversando'
  FINALIZADO = 'finalizado'

  CHOICES = (
    (NOVO, 'Novo'),
    (AGUARDANDO, 'Aguardando'),
    (CONVERSANDO, 'Conversando'),
    (FINALIZADO, 'Finalizado'),
  )


def resolve_conversation_category(conversation: Conversation) -> str:
  """Deriva a categoria exibida na inbox a partir do estado da conversa."""
  if conversation.status == Conversation.Status.CLOSED:
    return ConversationCategory.FINALIZADO
  if conversation.status == Conversation.Status.BOT:
    return ConversationCategory.NOVO
  if conversation.assigned_to_id:
    return ConversationCategory.CONVERSANDO
  if conversation.handoff_pending or conversation.team_id:
    return ConversationCategory.AGUARDANDO
  return ConversationCategory.NOVO


def category_filter_q(category: str) -> Q:
  """Retorna filtro Q para a categoria solicitada."""
  if category == ConversationCategory.FINALIZADO:
    return Q(status=Conversation.Status.CLOSED)
  if category == ConversationCategory.CONVERSANDO:
    return Q(status=Conversation.Status.OPEN, assigned_to__isnull=False)
  if category == ConversationCategory.AGUARDANDO:
    return Q(
      status=Conversation.Status.OPEN,
      assigned_to__isnull=True,
    ) & (Q(handoff_pending=True) | Q(team__isnull=False))
  if category == ConversationCategory.NOVO:
    return Q(status=Conversation.Status.BOT) | Q(
      status=Conversation.Status.OPEN,
      assigned_to__isnull=True,
      handoff_pending=False,
      team__isnull=True,
    )
  return Q()
