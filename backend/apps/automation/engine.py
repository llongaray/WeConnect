import logging
import re
import unicodedata

from apps.chat.models import Conversation, Message

from .models import BotFlow, ConversationBotState
from .services import send_automated_message

logger = logging.getLogger(__name__)

MAX_INVALID_ATTEMPTS = 2

YES_VARIANTS = frozenset({
    'sim', 's', 'ss', 'yes', 'y', 'claro', 'ok', 'pode', 'quero',
    'confirmo', 'positivo', 'isso', 'certo', 'com certeza',
})

NO_VARIANTS = frozenset({
    'nao', 'n', 'no', 'negativo', 'nunca', 'nao quero', 'não',
    'nope', 'nem',
})


def _normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_yes_no(text: str) -> str | None:
    """Retorna 'yes', 'no' ou None se não reconhecer."""
    normalized = _normalize_text(text)
    if not normalized:
        return None
    if normalized in YES_VARIANTS:
        return 'yes'
    if normalized in NO_VARIANTS:
        return 'no'
    first_word = normalized.split()[0] if normalized else ''
    if first_word in YES_VARIANTS:
        return 'yes'
    if first_word in NO_VARIANTS:
        return 'no'
    return None


def _normalize_menu_options(raw) -> list[str]:
    """Normaliza opções do nó menu para lista de chaves."""
    if isinstance(raw, list):
        return [str(o).strip() for o in raw if str(o).strip()]
    if isinstance(raw, str):
        return [part.strip() for part in re.split(r'[,;\n]+', raw) if part.strip()]
    return []


def parse_menu_choice(text: str, options: list[str]) -> str | None:
    """Retorna a opção escolhida ou None se inválida."""
    if not options:
        return None
    normalized = _normalize_text(text)
    if not normalized:
        return None
    option_set = {str(o).strip() for o in options}
    if normalized in option_set:
        return normalized
    first_token = normalized.split()[0] if normalized else ''
    if first_token in option_set:
        return first_token
    return None


class FlowGraph:
    """Grafo de nós/arestas carregado do JSON do React Flow."""

    def __init__(self, definition: dict):
        self.nodes = {n['id']: n for n in definition.get('nodes', [])}
        self.edges = definition.get('edges', [])

    def get_node(self, node_id: str) -> dict | None:
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> list[dict]:
        return [e for e in self.edges if e.get('source') == node_id]

    def get_next_node_id(self, node_id: str, handle: str | None = None) -> str | None:
        edges = self.get_outgoing_edges(node_id)
        if not edges:
            return None
        if handle:
            for edge in edges:
                if edge.get('sourceHandle') == handle:
                    return edge.get('target')
            return None
        # Nó com saída única (message, assign, end)
        if len(edges) == 1:
            return edges[0].get('target')
        # Sem handle específico: primeira aresta sem sourceHandle nomeado
        for edge in edges:
            if not edge.get('sourceHandle'):
                return edge.get('target')
        return edges[0].get('target')


def clear_bot_state(conversation: Conversation):
    ConversationBotState.objects.filter(conversation=conversation).delete()


def maybe_process_chatbot(
    conversation: Conversation,
    message: Message,
    *,
    force_restart: bool = False,
):
    """Processa chatbot após mensagem inbound (chamado pelo webhook)."""
    if conversation.status not in (Conversation.Status.BOT, Conversation.Status.OPEN):
        logger.debug('Chatbot ignorado: conversa %s não está ativa para bot.', conversation.id)
        return
    if conversation.assigned_to_id is not None:
        logger.debug('Chatbot ignorado: conversa %s atribuída.', conversation.id)
        return
    if conversation.handoff_pending:
        logger.debug('Chatbot ignorado: conversa %s aguardando humano.', conversation.id)
        return
    if message.message_type != Message.MessageType.TEXT:
        return
    if message.direction != Message.Direction.INBOUND:
        return

    try:
        flow = BotFlow.objects.get(channel_id=conversation.channel_id, is_active=True)
    except BotFlow.DoesNotExist:
        logger.info(
            'Chatbot ignorado: nenhum fluxo ativo no canal %s (conversa %s).',
            conversation.channel_id,
            conversation.id,
        )
        return

    if not flow.start_node_id or not flow.definition:
        logger.warning('Chatbot: fluxo %s sem start_node_id ou definition.', flow.id)
        return

    graph = FlowGraph(flow.definition)
    if not graph.get_node(flow.start_node_id):
        logger.warning('Chatbot: start_node_id %s não encontrado no fluxo %s', flow.start_node_id, flow.id)
        return

    if conversation.status != Conversation.Status.BOT:
        conversation.status = Conversation.Status.BOT
        conversation.save(update_fields=['status', 'updated_at'])
        from apps.chat.services import broadcast_conversation_updated

        broadcast_conversation_updated(conversation)

    if force_restart:
        clear_bot_state(conversation)

    state, created = ConversationBotState.objects.get_or_create(
        conversation=conversation,
        defaults={
            'flow': flow,
            'current_node_id': flow.start_node_id,
            'waiting_for': ConversationBotState.WaitingFor.NONE,
        },
    )

    if not created and not graph.get_node(state.current_node_id):
        state.flow = flow
        state.current_node_id = flow.start_node_id
        state.waiting_for = ConversationBotState.WaitingFor.NONE
        state.invalid_attempts = 0
        state.save()
        created = True

    if not created and state.flow_id != flow.id:
        state.flow = flow
        state.current_node_id = flow.start_node_id
        state.waiting_for = ConversationBotState.WaitingFor.NONE
        state.invalid_attempts = 0
        state.save()
        created = True

    # Primeira mensagem da conversa: inicia o fluxo do começo
    if not created and state.waiting_for == ConversationBotState.WaitingFor.NONE:
        inbound_count = conversation.messages.filter(
            direction=Message.Direction.INBOUND,
            message_type=Message.MessageType.TEXT,
        ).count()
        if inbound_count <= 1 and state.current_node_id != flow.start_node_id:
            state.current_node_id = flow.start_node_id
            state.invalid_attempts = 0
            state.save()
            created = True

    # Aguardando escolha de menu (1, 2, 3...)
    if state.waiting_for == ConversationBotState.WaitingFor.MENU:
        node = graph.get_node(state.current_node_id) or {}
        menu_content = (node.get('data', {}) or {}).get('content', '')
        options = _normalize_menu_options((node.get('data', {}) or {}).get('options', []))
        choice = parse_menu_choice(message.content or '', options)

        if choice is None:
            state.invalid_attempts += 1
            if state.invalid_attempts <= MAX_INVALID_ATTEMPTS:
                send_automated_message(
                    conversation,
                    f'{menu_content}\n\nOpção inválida. Digite uma das opções do menu.',
                )
                state.save(update_fields=['invalid_attempts', 'updated_at'])
                return
            next_id = graph.get_next_node_id(state.current_node_id, 'invalid')
            if not next_id:
                send_automated_message(
                    conversation,
                    'Opção inválida. Um atendente irá ajudá-lo em breve.',
                )
                clear_bot_state(conversation)
                return
            state.current_node_id = next_id
            state.waiting_for = ConversationBotState.WaitingFor.NONE
            state.invalid_attempts = 0
            state.save()
        else:
            next_id = graph.get_next_node_id(state.current_node_id, choice)
            if not next_id:
                send_automated_message(
                    conversation,
                    'Desculpe, houve um erro no fluxo. Um atendente irá ajudá-lo em breve.',
                )
                clear_bot_state(conversation)
                return
            state.current_node_id = next_id
            state.waiting_for = ConversationBotState.WaitingFor.NONE
            state.invalid_attempts = 0
            state.save()

    # Aguardando resposta Sim/Não
    if state.waiting_for == ConversationBotState.WaitingFor.YES_NO:
        answer = parse_yes_no(message.content or '')
        if answer is None:
            state.invalid_attempts += 1
            if state.invalid_attempts <= MAX_INVALID_ATTEMPTS:
                node = graph.get_node(state.current_node_id)
                question = (node or {}).get('data', {}).get('content', '')
                send_automated_message(
                    conversation,
                    f'{question}\n\n(Responda Sim ou Não)',
                )
                state.save(update_fields=['invalid_attempts', 'updated_at'])
                return
            # Fallback para aresta default
            next_id = graph.get_next_node_id(state.current_node_id, 'default')
            if not next_id:
                node = graph.get_node(state.current_node_id)
                question = (node or {}).get('data', {}).get('content', '')
                send_automated_message(conversation, question)
                return
            state.current_node_id = next_id
            state.waiting_for = ConversationBotState.WaitingFor.NONE
            state.invalid_attempts = 0
            state.save()
        else:
            next_id = graph.get_next_node_id(state.current_node_id, answer)
            if not next_id:
                send_automated_message(
                    conversation,
                    'Desculpe, não entendi o fluxo. Um atendente irá ajudá-lo em breve.',
                )
                clear_bot_state(conversation)
                return
            state.current_node_id = next_id
            state.waiting_for = ConversationBotState.WaitingFor.NONE
            state.invalid_attempts = 0
            state.save()

    _process_nodes_until_wait(state, conversation, graph)


def _process_nodes_until_wait(
    state: ConversationBotState,
    conversation: Conversation,
    graph: FlowGraph,
    depth: int = 0,
):
    """Percorre nós em cadeia até precisar aguardar resposta do usuário."""
    if depth > 20:
        logger.warning('Chatbot: limite de profundidade atingido na conversa %s', conversation.id)
        return

    node = graph.get_node(state.current_node_id)
    if not node:
        clear_bot_state(conversation)
        return

    node_type = node.get('type', 'message')
    data = node.get('data', {})
    content = (data.get('content') or '').strip()

    if node_type == 'message':
        if content:
            send_automated_message(conversation, content)
        next_id = graph.get_next_node_id(state.current_node_id)
        if not next_id:
            clear_bot_state(conversation)
            return
        state.current_node_id = next_id
        state.save(update_fields=['current_node_id', 'updated_at'])
        _process_nodes_until_wait(state, conversation, graph, depth + 1)

    elif node_type == 'decision':
        if content:
            send_automated_message(conversation, content)
        state.waiting_for = ConversationBotState.WaitingFor.YES_NO
        state.save(update_fields=['waiting_for', 'updated_at'])

    elif node_type == 'menu':
        if content:
            send_automated_message(conversation, content)
        state.waiting_for = ConversationBotState.WaitingFor.MENU
        state.save(update_fields=['waiting_for', 'updated_at'])

    elif node_type == 'assign':
        if content:
            send_automated_message(conversation, content)
        from apps.chat.conversation_lifecycle import handoff_to_team

        team_id = data.get('team_id')
        handoff_to_team(conversation, team_id)
        clear_bot_state(conversation)

    elif node_type == 'end':
        if content:
            send_automated_message(conversation, content)
        clear_bot_state(conversation)
        if conversation.status == Conversation.Status.BOT:
            conversation.status = Conversation.Status.OPEN
            conversation.save(update_fields=['status', 'updated_at'])

    else:
        logger.warning('Chatbot: tipo de nó desconhecido %s', node_type)
        clear_bot_state(conversation)
