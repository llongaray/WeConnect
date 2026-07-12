"""Serviço central do ciclo de vida das conversas."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import Team, TeamMembership, User
from apps.accounts.services.capabilities import is_platform_operator, user_has_capability
from apps.accounts.services.tenant_scope import validate_entities_same_company
from apps.whatsapp.models import Channel

from .models import Contact, Conversation, ConversationEvent


def get_user_team_ids(user: User) -> set[int]:
    """IDs das equipes em que o usuário é membro."""
    if is_platform_operator(user):
        return set(Team.objects.filter(is_active=True).values_list('id', flat=True))
    if user.is_gestor and user.company_id:
        return set(
            Team.objects.filter(is_active=True, company_id=user.company_id).values_list('id', flat=True),
        )
    return set(
        TeamMembership.objects.filter(user=user, team__is_active=True).values_list('team_id', flat=True),
    )


def get_supervised_team_ids(user: User) -> set[int]:
    """Equipes que o supervisor lidera (membership role supervisor)."""
    if is_platform_operator(user) or user.is_gestor:
        return get_user_team_ids(user)
    if not user.is_supervisor:
        return set()
    return set(
        TeamMembership.objects.filter(
            user=user,
            role=TeamMembership.MemberRole.SUPERVISOR,
            team__is_active=True,
        ).values_list('team_id', flat=True),
    )


def user_can_access_conversation(user: User, conversation: Conversation) -> bool:
    if is_platform_operator(user):
        return True
    channel_company_id = conversation.channel.company_id
    if user.company_id and channel_company_id != user.company_id:
        return False
    if user.is_gestor:
        return True
    team_ids = get_user_team_ids(user)
    if conversation.team_id and conversation.team_id not in team_ids:
        return False
    if conversation.assigned_to_id is None:
        return True
    if conversation.assigned_to_id == user.id:
        return True
    if user.is_supervisor and conversation.team_id in get_supervised_team_ids(user):
        return True
    return False


def user_can_send_message(user: User, conversation: Conversation) -> bool:
    if conversation.status != Conversation.Status.OPEN:
        return False
    if user.is_admin:
        return True
    if user.is_supervisor and conversation.team_id in get_supervised_team_ids(user):
        return True
    return conversation.assigned_to_id == user.id


def user_can_transfer(user: User) -> bool:
    return user_has_capability(user, 'transfer_conversations')


def user_can_reopen(user: User) -> bool:
    return user_has_capability(user, 'reopen_conversations')


def _resolve_team_for_channel(channel: Channel) -> Team | None:
    if channel.default_team_id:
        return channel.default_team
    team = channel.teams.filter(is_active=True).first()
    return team


def _record_event(
    conversation: Conversation,
    actor: User,
    event_type: str,
    from_user: User | None = None,
    to_user: User | None = None,
    note: str = '',
):
    ConversationEvent.objects.create(
        conversation=conversation,
        actor=actor,
        event_type=event_type,
        from_user=from_user,
        to_user=to_user,
        note=note,
    )


def _broadcast_conversation(conversation: Conversation):
    from .services import broadcast_conversation_updated

    broadcast_conversation_updated(conversation)


def _clear_bot(conversation: Conversation):
    from apps.automation.engine import clear_bot_state

    clear_bot_state(conversation)


def _team_allowed_for_channel(channel: Channel, team_id: int) -> bool:
    if channel.default_team_id == team_id:
        return True
    return channel.teams.filter(pk=team_id).exists()


def _channel_has_active_bot(channel: Channel) -> bool:
    from apps.automation.models import BotFlow

    return BotFlow.objects.filter(channel=channel, is_active=True).exists()


@transaction.atomic
def resolve_for_inbound(channel: Channel, contact: Contact) -> tuple[Conversation, bool]:
    """
    Retorna conversa ativa (bot ou aberta) existente ou cria nova.
    Nunca reabre conversa fechada.
    """
    active_conv = (
        Conversation.objects.select_for_update()
        .filter(
            channel=channel,
            contact=contact,
            status__in=[Conversation.Status.OPEN, Conversation.Status.BOT],
        )
        .first()
    )
    if active_conv:
        return active_conv, False

    team = _resolve_team_for_channel(channel)
    initial_status = (
        Conversation.Status.BOT
        if _channel_has_active_bot(channel)
        else Conversation.Status.OPEN
    )
    conversation = Conversation.objects.create(
        channel=channel,
        contact=contact,
        team=team,
        status=initial_status,
        last_message_at=timezone.now(),
    )
    _broadcast_conversation(conversation)
    return conversation, True


def _ensure_access(user: User, conversation: Conversation):
    if not user_can_access_conversation(user, conversation):
        raise PermissionDenied('Você não tem acesso a esta conversa.')


def _ensure_open(conversation: Conversation):
    if conversation.status != Conversation.Status.OPEN:
        raise ValidationError({'detail': 'Esta conversa está encerrada.'})


@transaction.atomic
def assume(conversation: Conversation, actor: User) -> Conversation:
    _ensure_access(actor, conversation)
    _ensure_open(conversation)

    if conversation.assigned_to_id and conversation.assigned_to_id != actor.id:
        if not actor.is_admin and not (
            actor.is_supervisor and conversation.team_id in get_supervised_team_ids(actor)
        ):
            raise PermissionDenied('Conversa já atribuída a outro atendente.')

    from_user = conversation.assigned_to
    conversation.assigned_to = actor
    conversation.assigned_at = timezone.now()
    conversation.handoff_pending = False
    conversation.save(update_fields=['assigned_to', 'assigned_at', 'handoff_pending', 'updated_at'])
    _clear_bot(conversation)
    _record_event(
        conversation,
        actor,
        ConversationEvent.EventType.ASSUMED,
        from_user=from_user,
        to_user=actor,
    )
    _broadcast_conversation(conversation)
    return conversation


@transaction.atomic
def release(conversation: Conversation, actor: User) -> Conversation:
    _ensure_access(actor, conversation)
    _ensure_open(conversation)

    if conversation.assigned_to_id != actor.id and not actor.is_admin:
        if not (actor.is_supervisor and conversation.team_id in get_supervised_team_ids(actor)):
            raise PermissionDenied('Apenas o responsável pode devolver à fila.')

    from_user = conversation.assigned_to
    conversation.assigned_to = None
    conversation.assigned_at = None
    conversation.save(update_fields=['assigned_to', 'assigned_at', 'updated_at'])
    _record_event(
        conversation,
        actor,
        ConversationEvent.EventType.RELEASED,
        from_user=from_user,
    )
    _broadcast_conversation(conversation)
    return conversation


@transaction.atomic
def transfer(
    conversation: Conversation,
    actor: User,
    to_user: User,
    note: str = '',
) -> Conversation:
    if not user_can_transfer(actor):
        raise PermissionDenied('Apenas administradores e supervisores podem transferir.')

    _ensure_access(actor, conversation)
    _ensure_open(conversation)

    validate_entities_same_company(to_user, company=conversation.channel.company)

    if conversation.team_id:
        is_member = TeamMembership.objects.filter(
            team_id=conversation.team_id,
            user=to_user,
        ).exists()
        if not is_member and not to_user.is_admin:
            raise ValidationError({'assigned_to_id': 'Usuário não pertence à equipe da conversa.'})

    from_user = conversation.assigned_to
    conversation.assigned_to = to_user
    conversation.assigned_at = timezone.now()
    conversation.handoff_pending = False
    conversation.save(update_fields=['assigned_to', 'assigned_at', 'handoff_pending', 'updated_at'])
    _clear_bot(conversation)
    _record_event(
        conversation,
        actor,
        ConversationEvent.EventType.TRANSFERRED,
        from_user=from_user,
        to_user=to_user,
        note=note,
    )
    _broadcast_conversation(conversation)
    return conversation


@transaction.atomic
def close(
    conversation: Conversation,
    actor: User,
    farewell_message: str = '',
) -> Conversation:
    _ensure_access(actor, conversation)
    _ensure_open(conversation)

    if not actor.is_admin and not actor.is_supervisor:
        if conversation.assigned_to_id != actor.id:
            raise PermissionDenied('Apenas o responsável pode encerrar esta conversa.')

    if farewell_message and farewell_message.strip():
        from .message_service import send_outbound_message

        send_outbound_message(
            actor,
            conversation,
            {'content': farewell_message.strip(), 'message_type': 'text'},
            force=True,
        )

    conversation.status = Conversation.Status.CLOSED
    conversation.closed_at = timezone.now()
    conversation.closed_by = actor
    conversation.assigned_to = None
    conversation.assigned_at = None
    conversation.handoff_pending = False
    conversation.save(update_fields=[
        'status', 'closed_at', 'closed_by', 'assigned_to', 'assigned_at',
        'handoff_pending', 'updated_at',
    ])
    _clear_bot(conversation)
    _record_event(conversation, actor, ConversationEvent.EventType.CLOSED)
    _broadcast_conversation(conversation)
    return conversation


@transaction.atomic
def reopen(conversation: Conversation, actor: User) -> Conversation:
    if not user_can_reopen(actor):
        raise PermissionDenied('Apenas administradores e supervisores podem reabrir.')

    if conversation.status != Conversation.Status.CLOSED:
        raise ValidationError({'detail': 'Somente conversas encerradas podem ser reabertas.'})

    has_active = Conversation.objects.filter(
        channel_id=conversation.channel_id,
        contact_id=conversation.contact_id,
        status__in=[Conversation.Status.OPEN, Conversation.Status.BOT],
    ).exists()
    if has_active:
        raise ValidationError({
            'detail': 'Este contato já possui uma conversa aberta mais recente.',
        })

    conversation.status = Conversation.Status.OPEN
    conversation.assigned_to = actor
    conversation.assigned_at = timezone.now()
    conversation.closed_at = None
    conversation.closed_by = None
    conversation.handoff_pending = False
    conversation.save(update_fields=[
        'status', 'assigned_to', 'assigned_at', 'closed_at', 'closed_by',
        'handoff_pending', 'updated_at',
    ])
    _record_event(
        conversation,
        actor,
        ConversationEvent.EventType.REOPENED,
        to_user=actor,
    )
    _broadcast_conversation(conversation)
    return conversation


def set_handoff_pending(conversation: Conversation, team_id: int | None = None):
    """Encaminha conversa para fila humana (nó assign do bot)."""
    handoff_to_team(conversation, team_id)


@transaction.atomic
def handoff_to_team(conversation: Conversation, team_id: int | None = None) -> Conversation:
    """Marca handoff, define equipe de destino e abre a conversa para atendentes."""
    channel = conversation.channel
    team = None

    if team_id is not None:
        try:
            tid = int(team_id)
        except (TypeError, ValueError):
            tid = None
        if tid and _team_allowed_for_channel(channel, tid):
            team = Team.objects.filter(pk=tid, is_active=True).first()

    if team is None:
        team = _resolve_team_for_channel(channel)

    conversation.team = team
    conversation.status = Conversation.Status.OPEN
    conversation.handoff_pending = True
    conversation.save(update_fields=['team', 'status', 'handoff_pending', 'updated_at'])
    _broadcast_conversation(conversation)
    return conversation
