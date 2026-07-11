import { memo } from 'react'
import { Handle, Position, useReactFlow, type NodeProps } from '@xyflow/react'
import type { BotNodeData } from '@/types'
import { cn } from '@/lib/cn'
import { useChatbotChannel } from '@/components/chatbot/chatbotChannelContext'

type CustomNodeProps = NodeProps & { data: BotNodeData }

function NodeShell({
  title,
  color,
  children,
  showSource = true,
}: {
  title: string
  color: string
  children: React.ReactNode
  showSource?: boolean
}) {
  return (
    <div className={cn('min-w-[220px] rounded-lg border-2 shadow-panel', color)}>
      <Handle type="target" position={Position.Top} className="!bg-wa-green !w-2 !h-2" />
      <div className="px-3 py-2 border-b border-white/10">
        <span className="text-xs font-semibold uppercase tracking-wide">{title}</span>
      </div>
      <div className="p-3">{children}</div>
      {showSource && (
        <Handle type="source" position={Position.Bottom} className="!bg-wa-green !w-2 !h-2" />
      )}
    </div>
  )
}

function useUpdateNodeData(nodeId: string) {
  const { setNodes } = useReactFlow()
  return (field: keyof BotNodeData, value: string) => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, [field]: value } } : n,
      ),
    )
  }
}

export const MessageNode = memo(function MessageNode({ id, data }: CustomNodeProps) {
  const updateData = useUpdateNodeData(id)
  return (
    <NodeShell title="Mensagem" color="border-emerald-600 bg-emerald-950/80">
      <textarea
        className="w-full min-h-[60px] text-xs bg-black/30 border border-emerald-700/50 rounded p-2 resize-y focus:outline-none focus:border-emerald-500 nodrag"
        placeholder="Texto da mensagem..."
        value={data.content || ''}
        onChange={(e) => updateData('content', e.target.value)}
        onPointerDown={(e) => e.stopPropagation()}
      />
    </NodeShell>
  )
})

export const DecisionNode = memo(function DecisionNode({ id, data }: CustomNodeProps) {
  const updateData = useUpdateNodeData(id)
  return (
    <div className="min-w-[240px] rounded-lg border-2 border-amber-600 bg-amber-950/80 shadow-panel">
      <Handle type="target" position={Position.Top} className="!bg-wa-green !w-2 !h-2" />
      <div className="px-3 py-2 border-b border-white/10">
        <span className="text-xs font-semibold uppercase tracking-wide text-amber-300">
          Decisão Sim/Não
        </span>
      </div>
      <div className="p-3">
        <textarea
          className="w-full min-h-[60px] text-xs bg-black/30 border border-amber-700/50 rounded p-2 resize-y focus:outline-none focus:border-amber-500 nodrag"
          placeholder="Pergunta sim/não real (ex: Deseja falar com atendente?)"
          value={data.content || ''}
          onChange={(e) => updateData('content', e.target.value)}
          onPointerDown={(e) => e.stopPropagation()}
        />
        <div className="flex justify-between mt-3 text-[10px] text-wa-muted px-1">
          <span className="text-green-400">Sim</span>
          <span className="text-red-400">Não</span>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="yes"
        style={{ left: '30%' }}
        className="!bg-green-500 !w-2.5 !h-2.5"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="no"
        style={{ left: '70%' }}
        className="!bg-red-500 !w-2.5 !h-2.5"
      />
    </div>
  )
})

function parseOptionsText(value: string): string[] {
  return value
    .split(/[,;\n]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export const MenuNode = memo(function MenuNode({ id, data }: CustomNodeProps) {
  const updateData = useUpdateNodeData(id)
  const { setNodes } = useReactFlow()
  const options = data.options?.length ? data.options : ['1', '2', '3']
  const optionsText = (data.options || ['1', '2', '3']).join(', ')

  const updateOptions = (text: string) => {
    const parsed = parseOptionsText(text)
    setNodes((nds) =>
      nds.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, options: parsed.length ? parsed : ['1'] } }
          : n,
      ),
    )
  }

  const handleCount = options.length + 1
  const handleSpacing = 100 / (handleCount + 1)

  return (
    <div className="min-w-[260px] rounded-lg border-2 border-violet-600 bg-violet-950/80 shadow-panel">
      <Handle type="target" position={Position.Top} className="!bg-wa-green !w-2 !h-2" />
      <div className="px-3 py-2 border-b border-white/10">
        <span className="text-xs font-semibold uppercase tracking-wide text-violet-300">
          Menu de opções
        </span>
      </div>
      <div className="p-3 space-y-2">
        <textarea
          className="w-full min-h-[70px] text-xs bg-black/30 border border-violet-700/50 rounded p-2 resize-y focus:outline-none focus:border-violet-500 nodrag"
          placeholder="Texto do menu (ex: Digite 1, 2 ou 3...)"
          value={data.content || ''}
          onChange={(e) => updateData('content', e.target.value)}
          onPointerDown={(e) => e.stopPropagation()}
        />
        <input
          className="w-full text-xs bg-black/30 border border-violet-700/50 rounded p-2 focus:outline-none focus:border-violet-500 nodrag"
          placeholder="Opções: 1, 2, 3"
          value={optionsText}
          onChange={(e) => updateOptions(e.target.value)}
          onPointerDown={(e) => e.stopPropagation()}
        />
        <p className="text-[10px] text-wa-muted">
          O bot valida a resposta e roteia para a opção correta.
        </p>
      </div>
      {options.map((opt, i) => (
        <Handle
          key={opt}
          type="source"
          position={Position.Bottom}
          id={opt}
          style={{ left: `${handleSpacing * (i + 1)}%` }}
          className="!bg-violet-400 !w-2.5 !h-2.5"
          title={`Opção ${opt}`}
        />
      ))}
      <Handle
        type="source"
        position={Position.Bottom}
        id="invalid"
        style={{ left: `${handleSpacing * (options.length + 1)}%` }}
        className="!bg-red-500 !w-2.5 !h-2.5"
        title="Inválido"
      />
      <div className="flex justify-between px-3 pb-2 text-[9px] text-wa-muted">
        {options.map((opt) => (
          <span key={opt}>{opt}</span>
        ))}
        <span className="text-red-400">inv</span>
      </div>
    </div>
  )
})

export const AssignNode = memo(function AssignNode({ id, data }: CustomNodeProps) {
  const updateData = useUpdateNodeData(id)
  const { setNodes } = useReactFlow()
  const { channelTeams } = useChatbotChannel()

  const setTeamId = (teamId: number | '') => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, team_id: teamId === '' ? null : teamId } }
          : n,
      ),
    )
  }

  return (
    <NodeShell title="Atribuir atendente" color="border-blue-600 bg-blue-950/80" showSource={false}>
      <textarea
        className="w-full min-h-[50px] text-xs bg-black/30 border border-blue-700/50 rounded p-2 resize-y focus:outline-none focus:border-blue-500 nodrag"
        placeholder="Mensagem antes de transferir (opcional)..."
        value={data.content || ''}
        onChange={(e) => updateData('content', e.target.value)}
        onPointerDown={(e) => e.stopPropagation()}
      />
      <label className="block text-[10px] text-wa-muted mt-2 mb-1">Equipe de destino *</label>
      <select
        className="w-full text-xs bg-black/30 border border-blue-700/50 rounded p-2 focus:outline-none focus:border-blue-500 nodrag"
        value={data.team_id ?? ''}
        onChange={(e) => setTeamId(e.target.value ? Number(e.target.value) : '')}
        onPointerDown={(e) => e.stopPropagation()}
      >
        <option value="">Selecione a equipe...</option>
        {channelTeams.map((team) => (
          <option key={team.id} value={team.id}>
            {team.name}
          </option>
        ))}
      </select>
      {channelTeams.length === 0 && (
        <p className="text-[10px] text-amber-400 mt-1">
          Vincule equipes ao canal em Admin → Equipes.
        </p>
      )}
      <p className="text-[10px] text-wa-muted mt-2">
        Abre a conversa na fila da equipe para admin, supervisor ou atendente assumir.
      </p>
    </NodeShell>
  )
})

export const EndNode = memo(function EndNode({ id, data }: CustomNodeProps) {
  const updateData = useUpdateNodeData(id)
  return (
    <NodeShell title="Fim" color="border-gray-600 bg-gray-900/80" showSource={false}>
      <textarea
        className="w-full min-h-[50px] text-xs bg-black/30 border border-gray-600 rounded p-2 resize-y focus:outline-none focus:border-gray-500 nodrag"
        placeholder="Mensagem final (opcional)..."
        value={data.content || ''}
        onChange={(e) => updateData('content', e.target.value)}
        onPointerDown={(e) => e.stopPropagation()}
      />
    </NodeShell>
  )
})

export const nodeTypes = {
  message: MessageNode,
  decision: DecisionNode,
  menu: MenuNode,
  assign: AssignNode,
  end: EndNode,
}
