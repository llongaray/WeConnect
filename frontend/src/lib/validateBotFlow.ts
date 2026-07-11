import type { Edge, Node } from '@xyflow/react'

function messageHasYesNoQuestion(content: string): boolean {
  const lower = content.toLowerCase()
  if (lower.includes('deseja falar') || lower.includes('quer falar')) return true
  return content.includes('?') && (lower.includes('deseja') || lower.includes('quer'))
}

/** Valida o grafo do chatbot antes de salvar. Retorna mensagem de erro ou null se válido. */
export function validateBotFlow(
  nodes: Node[],
  edges: Edge[],
  startNodeId: string,
): string | null {
  if (!startNodeId) return 'Selecione o nó inicial do fluxo.'
  if (!nodes.find((n) => n.id === startNodeId)) return 'Nó inicial não encontrado no canvas.'

  const nodeMap = new Map(nodes.map((n) => [n.id, n]))

  for (const node of nodes) {
    if (node.type === 'decision') {
      const nodeEdges = edges.filter((e) => e.source === node.id)
      const handles = new Set(nodeEdges.map((e) => e.sourceHandle))
      if (!handles.has('yes') || !handles.has('no')) {
        return `Nó "${node.id}": conecte as saídas Sim e Não.`
      }
    }
    if (node.type === 'menu') {
      const data = node.data as { options?: string[] }
      const options = data?.options?.filter(Boolean) || []
      if (options.length === 0) {
        return `Nó "${node.id}": informe as opções do menu (ex: 1, 2, 3).`
      }
      const nodeEdges = edges.filter((e) => e.source === node.id)
      const handles = new Set(nodeEdges.map((e) => e.sourceHandle))
      for (const opt of options) {
        if (!handles.has(opt)) {
          return `Nó "${node.id}": conecte a saída da opção "${opt}".`
        }
      }
      if (!handles.has('invalid')) {
        return `Nó "${node.id}": conecte a saída "Inválido".`
      }
    }
    if (node.type === 'message') {
      const content = (node.data as { content?: string })?.content || ''
      const outEdges = edges.filter((e) => e.source === node.id)
      for (const edge of outEdges) {
        const target = nodeMap.get(edge.target)
        if (!target) continue
        if (messageHasYesNoQuestion(content) && target.type === 'end') {
          return (
            `Nó "${node.id}": pergunta Sim/Não em Mensagem ligada ao Fim — ` +
            'use Mensagem → Sim/Não → Sim=Atribuir / Não=Fim.'
          )
        }
        const lower = content.toLowerCase()
        if (
          (lower.includes('inválid') || lower.includes('invalid') || lower.includes('digite 1')) &&
          target.type === 'end'
        ) {
          return `Nó "${node.id}": opção inválida deve voltar ao Menu, não ao Fim.`
        }
      }
    }
    if (node.type === 'assign') {
      const teamId = (node.data as { team_id?: number | null })?.team_id
      if (!teamId) {
        return `Nó "${node.id}": selecione a equipe de destino no nó Atribuir.`
      }
    }
  }
  return null
}
