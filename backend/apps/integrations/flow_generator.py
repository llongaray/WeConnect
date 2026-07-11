import json
import logging
import re

from apps.automation.flow_validation import (
    extract_numbered_options,
    is_fake_menu_decision,
    message_has_numbered_menu,
    message_has_yes_no_question,
    validate_flow_definition,
    validate_flow_semantics,
)

from .deepseek_client import DeepSeekAPIError, chat_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um assistente que cria fluxos de chatbot WhatsApp para o MoneyConnect.

Responda SEMPRE em JSON válido com este formato exato:
{
  "reply": "mensagem amigável em pt-BR para o usuário",
  "flow": {
    "name": "nome do fluxo",
    "start_node_id": "id do primeiro nó",
    "nodes": [...],
    "edges": [...]
  }
}

Tipos de nó:
- message: envia texto e AVANÇA AUTOMATICAMENTE para o próximo nó (NÃO espera resposta)
  - Use só para informar algo, SEM perguntas Sim/Não
- menu: valida opção numerada (1, 2, 3...); O BOT roteia automaticamente
  - data.options: ["1", "2", "3"]
  - arestas OBRIGATÓRIAS: sourceHandle "1", "2", "3" (uma por opção) + "invalid"
  - Cada opção vai para UM nó message DIFERENTE (ramificação, NÃO cadeia linear)
- decision: pergunta Sim/Não — ÚNICO tipo que ESPERA resposta sim/não do usuário
  - arestas: sourceHandle "yes" → assign (ou próximo passo) e "no" → end
  - Use APÓS message de confirmação de perfil para perguntar "Deseja falar com atendente?"
- assign: transfere para humano (handoff); data.team_id opcional na IA (configure no editor)
  - Ao executar: status vira "open", handoff_pending=true, equipe definida
- end: encerra

REGRAS CRÍTICAS (violação = fluxo rejeitado):
1. Menu 1/2/3 → SEMPRE use nó "menu", NUNCA "decision"
2. NUNCA coloque "Deseja falar com atendente?" dentro de message ligada ao Fim
3. Pergunta de atendente → nó decision com yes=assign e no=end
4. NUNCA encadeie mensagens de perfil em sequência
5. Opção inválida do menu deve voltar ao menu_perfil (loop)
6. ids em snake_case; posições x~280, y += 120

EXEMPLO CORRETO (menu + atendente):
{
  "reply": "Fluxo com menu e handoff.",
  "flow": {
    "name": "Atendimento MoneyConn",
    "start_node_id": "saudacao",
    "nodes": [
      {"id": "saudacao", "type": "message", "position": {"x": 280, "y": 80}, "data": {"content": "Olá! Bem-vindo.\\n1 - Funcionário\\n2 - Parceiro\\n3 - Outros"}},
      {"id": "menu_perfil", "type": "menu", "position": {"x": 280, "y": 200}, "data": {"content": "", "options": ["1", "2", "3"]}},
      {"id": "resposta_1", "type": "message", "position": {"x": 80, "y": 320}, "data": {"content": "Ótimo! Você é funcionário interno."}},
      {"id": "decisao_1", "type": "decision", "position": {"x": 80, "y": 440}, "data": {"content": "Deseja falar com um atendente?"}},
      {"id": "resposta_2", "type": "message", "position": {"x": 280, "y": 320}, "data": {"content": "Perfeito! Você é parceiro."}},
      {"id": "decisao_2", "type": "decision", "position": {"x": 280, "y": 440}, "data": {"content": "Deseja falar com um atendente?"}},
      {"id": "resposta_3", "type": "message", "position": {"x": 480, "y": 320}, "data": {"content": "Entendi. Perfil outros."}},
      {"id": "decisao_3", "type": "decision", "position": {"x": 480, "y": 440}, "data": {"content": "Deseja falar com um atendente?"}},
      {"id": "opcao_invalida", "type": "message", "position": {"x": 280, "y": 560}, "data": {"content": "Opção inválida. Digite 1, 2 ou 3."}},
      {"id": "assign_atendente", "type": "assign", "position": {"x": 480, "y": 680}, "data": {"content": "Transferindo para atendente. Aguarde.", "team_id": null}},
      {"id": "fim", "type": "end", "position": {"x": 280, "y": 680}, "data": {"content": "Obrigado pelo contato!"}}
    ],
    "edges": [
      {"id": "e1", "source": "saudacao", "target": "menu_perfil"},
      {"id": "e2", "source": "menu_perfil", "target": "resposta_1", "sourceHandle": "1"},
      {"id": "e3", "source": "menu_perfil", "target": "resposta_2", "sourceHandle": "2"},
      {"id": "e4", "source": "menu_perfil", "target": "resposta_3", "sourceHandle": "3"},
      {"id": "e5", "source": "menu_perfil", "target": "opcao_invalida", "sourceHandle": "invalid"},
      {"id": "e6", "source": "opcao_invalida", "target": "menu_perfil"},
      {"id": "e7", "source": "resposta_1", "target": "decisao_1"},
      {"id": "e8", "source": "decisao_1", "target": "assign_atendente", "sourceHandle": "yes"},
      {"id": "e9", "source": "decisao_1", "target": "fim", "sourceHandle": "no"},
      {"id": "e10", "source": "resposta_2", "target": "decisao_2"},
      {"id": "e11", "source": "decisao_2", "target": "assign_atendente", "sourceHandle": "yes"},
      {"id": "e12", "source": "decisao_2", "target": "fim", "sourceHandle": "no"},
      {"id": "e13", "source": "resposta_3", "target": "decisao_3"},
      {"id": "e14", "source": "decisao_3", "target": "assign_atendente", "sourceHandle": "yes"},
      {"id": "e15", "source": "decisao_3", "target": "fim", "sourceHandle": "no"}
    ]
  }
}

Se não puder gerar fluxo válido, retorne "flow": null e explique no reply.
"""

VALID_NODE_TYPES = frozenset({'message', 'decision', 'menu', 'assign', 'end'})

CORRECTION_PROMPT = """CORREÇÃO OBRIGATÓRIA — o fluxo anterior foi REJEITADO:
{error}

Reescreva o fluxo inteiro corrigindo:
- Troque decision por menu onde houver opções 1/2/3
- Ramifique: menu → resposta_1, resposta_2, resposta_3 (paralelo, não sequencial)
- Pergunta "Deseja atendente?" → nó decision (NÃO message) com yes=assign e no=end
- Opção inválida do menu deve voltar ao menu_perfil
"""


def _extract_json(text: str) -> dict:
    """Extrai JSON da resposta (remove markdown se houver)."""
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def _normalize_positions(nodes: list[dict]) -> list[dict]:
    """Garante posições válidas em layout vertical."""
    for i, node in enumerate(nodes):
        pos = node.get('position') or {}
        if not isinstance(pos, dict) or 'x' not in pos or 'y' not in pos:
            node['position'] = {'x': 280, 'y': 80 + i * 120}
        node.setdefault('data', {})
        if 'content' not in node['data']:
            node['data']['content'] = ''
        if node.get('type') == 'menu':
            opts = node['data'].get('options', [])
            if isinstance(opts, str):
                node['data']['options'] = [
                    p.strip() for p in re.split(r'[,;\n]+', opts) if p.strip()
                ]
            elif isinstance(opts, list):
                node['data']['options'] = [str(o).strip() for o in opts if str(o).strip()]
            else:
                node['data']['options'] = []
    return nodes


def _get_single_target(edges: list, source_id: str) -> str | None:
    outs = [e for e in edges if e.get('source') == source_id]
    if len(outs) == 1:
        return outs[0].get('target')
    return None


def _collect_linear_messages(
    start_id: str | None,
    node_by_id: dict,
    edges: list,
) -> list[dict]:
    """Coleta mensagens encadeadas linearmente após um nó."""
    if not start_id:
        return []
    chain = []
    current = start_id
    seen = set()
    while current and current not in seen:
        seen.add(current)
        node = node_by_id.get(current)
        if not node:
            break
        if node.get('type') == 'message':
            chain.append(node)
        elif node.get('type') in ('decision', 'menu', 'assign', 'end'):
            break
        nxt = _get_single_target(edges, current)
        if not nxt:
            break
        current = nxt
    return chain


def _repair_fake_menu_decisions(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict], bool]:
    """
    Converte decision falsa (validação de menu) em menu com ramificações.
    Desfaz cadeias lineares funcionário→parceiro→outros.
    """
    node_by_id = {n['id']: n for n in nodes}
    edges = list(edges)
    changed = False

    for node in list(nodes):
        if not is_fake_menu_decision(node):
            continue

        options = ['1', '2', '3']
        for edge in edges:
            if edge.get('target') != node['id']:
                continue
            pred = node_by_id.get(edge.get('source'))
            if pred and pred.get('type') == 'message':
                opts = extract_numbered_options((pred.get('data') or {}).get('content', ''))
                if opts:
                    options = opts
                    break

        start_chain_id = None
        for handle in ('yes', 'no', None):
            for edge in edges:
                if edge.get('source') != node['id']:
                    continue
                if handle is None or edge.get('sourceHandle') == handle:
                    start_chain_id = edge.get('target')
                    break
            if start_chain_id:
                break

        chain = _collect_linear_messages(start_chain_id, node_by_id, edges)
        profile_msgs = []
        invalid_msg = None
        for msg in chain:
            content = (msg.get('data') or {}).get('content', '').lower()
            if any(x in content for x in ('inválid', 'invalid', 'digite 1', 'digite 2', 'digite 3')):
                invalid_msg = msg
            else:
                profile_msgs.append(msg)

        node['type'] = 'menu'
        node.setdefault('data', {})
        node['data']['content'] = ''
        node['data']['options'] = options
        changed = True

        edges = [e for e in edges if e.get('source') != node['id']]

        chain_ids = [m['id'] for m in chain]
        for i in range(len(chain_ids) - 1):
            src, tgt = chain_ids[i], chain_ids[i + 1]
            edges = [e for e in edges if not (e.get('source') == src and e.get('target') == tgt)]

        for i, opt in enumerate(options):
            if i < len(profile_msgs):
                edges.append({
                    'id': f'repair_{node["id"]}_{opt}',
                    'source': node['id'],
                    'target': profile_msgs[i]['id'],
                    'sourceHandle': opt,
                })

        if invalid_msg:
            edges.append({
                'id': f'repair_{node["id"]}_invalid',
                'source': node['id'],
                'target': invalid_msg['id'],
                'sourceHandle': 'invalid',
            })
            if not any(
                e.get('source') == invalid_msg['id'] and e.get('target') == node['id']
                for e in edges
            ):
                edges.append({
                    'id': f'repair_{invalid_msg["id"]}_back',
                    'source': invalid_msg['id'],
                    'target': node['id'],
                })

    return nodes, edges, changed


def _ensure_menu_after_numbered_message(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict], bool]:
    """Insere nó menu quando há saudação numerada seguida de decision falsa ou message."""
    node_by_id = {n['id']: n for n in nodes}
    edges = list(edges)
    changed = False

    for node in nodes:
        if node.get('type') != 'message':
            continue
        content = (node.get('data') or {}).get('content', '')
        if not message_has_numbered_menu(content):
            continue

        out_edges = [e for e in edges if e.get('source') == node['id']]
        if not out_edges:
            continue

        target = out_edges[0].get('target')
        target_node = node_by_id.get(target)
        if not target_node:
            continue
        if target_node.get('type') == 'menu':
            continue

        options = extract_numbered_options(content)
        menu_id = f'menu_{node["id"]}'
        if menu_id in node_by_id:
            continue

        pos = node.get('position') or {'x': 280, 'y': 80}
        menu_node = {
            'id': menu_id,
            'type': 'menu',
            'position': {'x': pos.get('x', 280), 'y': pos.get('y', 80) + 120},
            'data': {'content': '', 'options': options},
        }
        nodes.append(menu_node)
        node_by_id[menu_id] = menu_node
        changed = True

        edges = [e for e in edges if e.get('source') != node['id']]
        edges.append({'id': f'repair_{node["id"]}_to_menu', 'source': node['id'], 'target': menu_id})

        if is_fake_menu_decision(target_node):
            nodes, edges, sub_changed = _repair_fake_menu_decisions(nodes, edges)
            changed = changed or sub_changed

    return nodes, edges, changed


def _split_profile_and_question(content: str) -> tuple[str, str]:
    """Separa confirmação de perfil da pergunta Sim/Não."""
    text = (content or '').strip()
    if not text:
        return '', 'Deseja falar com um atendente?'
    parts = re.split(r'(?<=[?!.])\s+', text)
    if len(parts) >= 2 and '?' in parts[-1]:
        question = parts[-1].strip()
        profile = ' '.join(p.strip() for p in parts[:-1] if p.strip()).strip()
        if profile:
            return profile, question
    return text, 'Deseja falar com um atendente?'


def _repair_attendant_question_messages(
    nodes: list[dict],
    edges: list[dict],
) -> tuple[list[dict], list[dict], bool]:
    """
    Corrige message com pergunta de atendente ligada direto ao Fim.
    Insere decision + assign automaticamente.
    """
    node_by_id = {n['id']: n for n in nodes}
    edges = list(edges)
    changed = False

    assign_id = next((n['id'] for n in nodes if n.get('type') == 'assign'), None)
    if not assign_id:
        assign_id = 'assign_atendente'
        if assign_id not in node_by_id:
            nodes.append({
                'id': assign_id,
                'type': 'assign',
                'position': {'x': 480, 'y': 680},
                'data': {'content': 'Transferindo para um atendente. Aguarde.', 'team_id': None},
            })
            node_by_id[assign_id] = nodes[-1]
            changed = True

    for node in list(nodes):
        if node.get('type') != 'message':
            continue
        content = (node.get('data') or {}).get('content', '')
        if not message_has_yes_no_question(content):
            continue

        outs = [e for e in edges if e.get('source') == node['id']]
        if len(outs) != 1:
            continue
        end_node = node_by_id.get(outs[0].get('target'))
        if not end_node or end_node.get('type') != 'end':
            continue

        profile, question = _split_profile_and_question(content)
        node.setdefault('data', {})['content'] = profile

        decision_id = f'decisao_{node["id"]}'
        if decision_id not in node_by_id:
            pos = node.get('position') or {'x': 280, 'y': 320}
            decision_node = {
                'id': decision_id,
                'type': 'decision',
                'position': {'x': pos.get('x', 280), 'y': pos.get('y', 80) + 100},
                'data': {'content': question},
            }
            nodes.append(decision_node)
            node_by_id[decision_id] = decision_node
            changed = True

        end_id = end_node['id']
        edges = [e for e in edges if e.get('source') != node['id']]
        edges.append({
            'id': f'repair_{node["id"]}_dec',
            'source': node['id'],
            'target': decision_id,
        })
        edges.append({
            'id': f'repair_{decision_id}_yes',
            'source': decision_id,
            'target': assign_id,
            'sourceHandle': 'yes',
        })
        edges.append({
            'id': f'repair_{decision_id}_no',
            'source': decision_id,
            'target': end_id,
            'sourceHandle': 'no',
        })

    return nodes, edges, changed


def _repair_invalid_option_loop(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict], bool]:
    """Opção inválida ligada ao Fim deve voltar ao menu mais próximo."""
    node_by_id = {n['id']: n for n in nodes}
    menu_ids = [n['id'] for n in nodes if n.get('type') == 'menu']
    if not menu_ids:
        return nodes, edges, False

    edges = list(edges)
    changed = False
    menu_id = menu_ids[0]

    for node in nodes:
        if node.get('type') != 'message':
            continue
        content = (node.get('data') or {}).get('content', '').lower()
        if not any(x in content for x in ('inválid', 'invalid', 'digite 1')):
            continue
        for i, edge in enumerate(edges):
            if edge.get('source') != node['id']:
                continue
            target = node_by_id.get(edge.get('target'))
            if target and target.get('type') == 'end':
                edges[i] = {**edge, 'target': menu_id}
                changed = True

    return nodes, edges, changed


def _repair_flow(flow: dict) -> dict:
    """Aplica correções automáticas em fluxos mal gerados pela IA."""
    nodes = list(flow.get('nodes', []))
    edges = list(flow.get('edges', []))
    if not nodes:
        return flow

    nodes, edges, c1 = _repair_fake_menu_decisions(nodes, edges)
    nodes, edges, c2 = _ensure_menu_after_numbered_message(nodes, edges)
    nodes, edges, c3 = _repair_attendant_question_messages(nodes, edges)
    nodes, edges, c4 = _repair_invalid_option_loop(nodes, edges)
    if c1 or c2 or c3 or c4:
        logger.info('Fluxo IA reparado automaticamente.')

    flow['nodes'] = nodes
    flow['edges'] = edges
    return flow


def _flow_has_issues(flow: dict | None) -> str | None:
    """Retorna descrição do problema semântico/estrutural, ou None."""
    if not flow:
        return 'Fluxo vazio.'
    nodes = flow.get('nodes', [])
    edges = flow.get('edges', [])
    start = flow.get('start_node_id', '')
    if not nodes:
        return 'Sem nós.'
    definition = {'nodes': nodes, 'edges': edges}
    err = validate_flow_definition(definition, start or nodes[0]['id'])
    if err:
        return err
    err = validate_flow_semantics(definition)
    return err


def _normalize_flow(flow: dict) -> dict | None:
    """Normaliza, repara e valida o fluxo retornado pela IA."""
    if not flow or not isinstance(flow, dict):
        return None

    flow = _repair_flow(dict(flow))
    nodes = flow.get('nodes', [])
    edges = flow.get('edges', [])
    start_node_id = flow.get('start_node_id', '')
    name = flow.get('name', 'Fluxo gerado por IA')

    if not nodes:
        return None

    nodes = _normalize_positions(list(nodes))
    for node in nodes:
        if node.get('type') not in VALID_NODE_TYPES:
            node['type'] = 'message'

    definition = {'nodes': nodes, 'edges': edges if isinstance(edges, list) else []}

    if not start_node_id and nodes:
        start_node_id = nodes[0]['id']

    error = validate_flow_definition(definition, start_node_id)
    if error:
        logger.warning('Fluxo IA inválido: %s', error)
        return None

    return {
        'name': name,
        'start_node_id': start_node_id,
        'nodes': nodes,
        'edges': definition['edges'],
    }


def _current_flow_warning(current_flow: dict | None) -> str | None:
    """Avisa a IA quando o canvas atual está com estrutura errada."""
    if not current_flow or not current_flow.get('nodes'):
        return None
    nodes = current_flow['nodes']
    has_fake = any(is_fake_menu_decision(n) for n in nodes)
    has_numbered = any(
        n.get('type') == 'message' and message_has_numbered_menu((n.get('data') or {}).get('content', ''))
        for n in nodes
    )
    has_menu = any(n.get('type') == 'menu' for n in nodes)
    if has_fake or (has_numbered and not has_menu):
        return (
            'ATENÇÃO: o fluxo atual no canvas está ERRADO — usa decision/cadeia linear '
            'para menu 1/2/3. Reescreva com nó menu e ramificações paralelas. '
            'NÃO mantenha a estrutura linear atual.'
        )
    return None


def _call_deepseek(api_messages: list[dict]) -> dict:
    raw = chat_completion(
        api_messages,
        response_format={'type': 'json_object'},
        temperature=0.2,
        max_tokens=4096,
    )
    return _extract_json(raw)


def generate_bot_flow(
    messages: list[dict],
    current_flow: dict | None = None,
) -> dict:
    """
    Gera fluxo via DeepSeek.
    Retorna { reply, flow?, applied }.
    """
    api_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    warning = _current_flow_warning(current_flow)
    if warning:
        api_messages.append({'role': 'system', 'content': warning})

    if current_flow and current_flow.get('nodes'):
        context = json.dumps(current_flow, ensure_ascii=False, indent=2)
        api_messages.append({
            'role': 'system',
            'content': f'Fluxo atual no canvas (substitua estrutura errada se necessário):\n{context}',
        })

    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role in ('user', 'assistant') and content:
            api_messages.append({'role': role, 'content': content})

    last_error = ''
    parsed = None
    normalized = None

    for attempt in range(2):
        try:
            parsed = _call_deepseek(api_messages)
        except (json.JSONDecodeError, DeepSeekAPIError) as exc:
            logger.exception('Falha ao gerar fluxo: %s', exc)
            return {
                'reply': f'Não consegui gerar o fluxo: {exc}',
                'flow': None,
                'applied': False,
            }

        reply = parsed.get('reply', 'Fluxo processado.')
        raw_flow = parsed.get('flow')
        normalized = _normalize_flow(raw_flow) if raw_flow else None

        if normalized:
            return {
                'reply': reply,
                'flow': normalized,
                'applied': True,
            }

        last_error = _flow_has_issues(raw_flow) if raw_flow else 'Fluxo ausente ou malformado.'
        logger.warning('Tentativa %s fluxo IA falhou: %s', attempt + 1, last_error)

        if attempt == 0 and raw_flow:
            api_messages.append({
                'role': 'assistant',
                'content': json.dumps(parsed, ensure_ascii=False),
            })
            api_messages.append({
                'role': 'system',
                'content': CORRECTION_PROMPT.format(error=last_error),
            })
            continue

        return {
            'reply': (
                f'{reply}\n\nNão foi possível aplicar o fluxo ({last_error}). '
                'Tente: "Crie fluxo com menu 1=funcionário, 2=parceiro, 3=outros, ramificações paralelas".'
            ),
            'flow': None,
            'applied': False,
        }

    return {
        'reply': parsed.get('reply', 'Fluxo processado.') if parsed else 'Erro ao gerar.',
        'flow': normalized,
        'applied': normalized is not None,
    }
