"""Validação compartilhada de grafos de fluxo do chatbot."""

import re
import unicodedata

VALID_NODE_TYPES = frozenset({'message', 'decision', 'menu', 'assign', 'end'})

FAKE_MENU_DECISION_PATTERNS = (
    'opcao valida',
    'opção válida',
    'escolheu uma opcao',
    'escolheu uma opção',
    'opcao invalida',
    'opção inválida',
    'sim/nao',
    'sim/não',
    'sim ou nao',
    'sim ou não',
)


def _normalize_text(text: str) -> str:
    text = (text or '').strip().lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip()


def _normalize_menu_options(raw) -> list[str]:
    if isinstance(raw, list):
        return [str(o).strip() for o in raw if str(o).strip()]
    if isinstance(raw, str):
        import re
        return [part.strip() for part in re.split(r'[,;\n]+', raw) if part.strip()]
    return []


def message_has_numbered_menu(text: str) -> bool:
    """Detecta menu numerado no texto (1 -, 2 -, digite 1...)."""
    if not text:
        return False
    if re.search(r'(?:^|\n)\s*\d+\s*[-–.)]', text):
        return True
    lowered = text.lower()
    return 'digite 1' in lowered or 'digite 2' in lowered or 'digite 3' in lowered


def extract_numbered_options(text: str) -> list[str]:
    """Extrai chaves de menu (1, 2, 3...) do texto."""
    found = re.findall(r'(?:^|\n)\s*(\d+)\s*[-–.)]', text or '')
    if found:
        return list(dict.fromkeys(found))
    nums = re.findall(r'\b(\d+)\b', text or '')
    if len(nums) >= 2:
        return list(dict.fromkeys(nums))
    return ['1', '2', '3']


def is_fake_menu_decision(node: dict) -> bool:
    """Decisão Sim/Não usada indevidamente para validar menu numerado."""
    if node.get('type') != 'decision':
        return False
    content = _normalize_text((node.get('data') or {}).get('content', ''))
    return any(pattern in content for pattern in FAKE_MENU_DECISION_PATTERNS)


ATTENDANT_QUESTION_MARKERS = (
    'deseja falar com atendente',
    'deseja falar com um atendente',
    'quer falar com atendente',
    'quer falar com um atendente',
    'gostaria de falar com',
)


def message_has_yes_no_question(content: str) -> bool:
    """Detecta pergunta Sim/Não embutida em nó message."""
    normalized = _normalize_text(content)
    if any(marker in normalized for marker in ATTENDANT_QUESTION_MARKERS):
        return True
    return '?' in (content or '') and any(
        word in normalized for word in ('deseja', 'quer', 'gostaria')
    )


def _node_map(nodes: list) -> dict:
    return {n['id']: n for n in nodes}


def _outgoing_targets(edges: list, source_id: str) -> list[str]:
    return [e.get('target') for e in edges if e.get('source') == source_id and e.get('target')]


def _get_single_target(edges: list, source_id: str) -> str | None:
    outs = [e for e in edges if e.get('source') == source_id]
    if len(outs) == 1:
        return outs[0].get('target')
    return None


def _are_targets_linear_chain(target_ids: list, edges: list) -> bool:
    """Verifica se todos os destinos estão na mesma cadeia linear."""
    if len(target_ids) < 2:
        return False
    first = target_ids[0]
    chain = [first]
    current = first
    for _ in range(len(target_ids) + 10):
        nxt = _get_single_target(edges, current)
        if not nxt:
            break
        chain.append(nxt)
        current = nxt
    chain_set = set(chain)
    return all(t in chain_set for t in target_ids) and len(set(target_ids)) == len(target_ids)


def validate_flow_semantics(definition: dict) -> str | None:
    """Regras de negócio: menu numerado não pode usar decision em cadeia linear."""
    nodes = definition.get('nodes', [])
    edges = definition.get('edges', [])
    if not isinstance(nodes, list):
        return None

    has_numbered_message = False
    has_menu = False

    for node in nodes:
        node_type = node.get('type')
        if node_type == 'menu':
            has_menu = True
        if node_type == 'message':
            content = (node.get('data') or {}).get('content', '')
            if message_has_numbered_menu(content):
                has_numbered_message = True
        if is_fake_menu_decision(node):
            return (
                f"Nó '{node['id']}' usa Sim/Não para validar menu — "
                "use type 'menu' com arestas 1, 2, 3 e invalid."
            )

    if has_numbered_message and not has_menu:
        return 'Mensagem com opções numeradas exige um nó menu após a saudação.'

    for node in nodes:
        if node.get('type') != 'menu':
            continue
        node_id = node['id']
        options = _normalize_menu_options(node.get('data', {}).get('options', []))
        option_edges = [
            e for e in edges
            if e.get('source') == node_id and e.get('sourceHandle') in options
        ]
        targets = [e.get('target') for e in option_edges if e.get('target')]
        if len(set(targets)) < min(2, len(options)):
            return (
                f"Nó menu '{node_id}' deve ramificar para destinos diferentes "
                "(não em cadeia linear)."
            )
        if _are_targets_linear_chain(targets, edges):
            return (
                f"Nó menu '{node_id}' conecta opções em sequência — "
                "cada opção deve ir direto ao seu nó de resposta."
            )

    node_map = _node_map(nodes)

    for node in nodes:
        if node.get('type') != 'message':
            continue
        node_id = node['id']
        content = (node.get('data') or {}).get('content', '')
        lowered = content.lower()

        if message_has_yes_no_question(content):
            for target_id in _outgoing_targets(edges, node_id):
                target = node_map.get(target_id)
                if target and target.get('type') == 'end':
                    return (
                        f"Nó '{node_id}': pergunta Sim/Não em message ligada ao Fim — "
                        "o bot envia tudo sem esperar. Use message → decision → "
                        "yes=assign / no=end."
                    )

        if any(x in lowered for x in ('inválid', 'invalid', 'digite 1')):
            for target_id in _outgoing_targets(edges, node_id):
                target = node_map.get(target_id)
                if target and target.get('type') == 'end':
                    return (
                        f"Nó '{node_id}': opção inválida deve voltar ao menu, "
                        "não ir direto ao Fim."
                    )

    return None


def validate_flow_definition(definition: dict, start_node_id: str = '') -> str | None:
    """
    Valida definition + start_node_id.
    Retorna mensagem de erro ou None se válido.
    """
    if not isinstance(definition, dict):
        return 'definition deve ser um objeto JSON.'

    nodes = definition.get('nodes', [])
    edges = definition.get('edges', [])

    if not isinstance(nodes, list) or not nodes:
        return 'O fluxo precisa ter pelo menos um nó.'

    if not isinstance(edges, list):
        return 'edges deve ser uma lista.'

    if not start_node_id:
        return 'Informe o nó inicial do fluxo.'

    node_map = {}
    for node in nodes:
        if not isinstance(node, dict):
            return 'Cada nó deve ser um objeto.'
        node_id = node.get('id')
        node_type = node.get('type')
        if not node_id:
            return 'Todo nó precisa de um id.'
        if node_type not in VALID_NODE_TYPES:
            return f"Tipo de nó inválido: {node_type}."
        node_map[node_id] = node

    if start_node_id not in node_map:
        return 'Nó inicial não encontrado no fluxo.'

    for node in nodes:
        node_id = node['id']
        node_type = node.get('type')
        node_edges = [e for e in edges if e.get('source') == node_id]

        if node_type == 'decision':
            handles = {e.get('sourceHandle') for e in node_edges}
            if 'yes' not in handles or 'no' not in handles:
                return f"Nó de decisão '{node_id}' precisa de arestas Sim (yes) e Não (no)."

        if node_type == 'menu':
            options = _normalize_menu_options(node.get('data', {}).get('options', []))
            if not options:
                return f"Nó de menu '{node_id}' precisa de opções em data.options."
            handles = {e.get('sourceHandle') for e in node_edges}
            missing = [opt for opt in options if opt not in handles]
            if missing:
                return f"Nó de menu '{node_id}' sem aresta para opção(ões): {', '.join(missing)}."
            if 'invalid' not in handles:
                return f"Nó de menu '{node_id}' precisa de aresta 'invalid' para opção inválida."

        for edge in node_edges:
            target = edge.get('target')
            if target and target not in node_map:
                return f"Aresta de '{node_id}' aponta para nó inexistente '{target}'."

    semantic_error = validate_flow_semantics(definition)
    if semantic_error:
        return semantic_error

    return None
