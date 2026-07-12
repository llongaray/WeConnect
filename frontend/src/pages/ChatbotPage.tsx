import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import axios from 'axios'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  Bot,
  GitBranch,
  ListOrdered,
  MessageSquare,
  Save,
  UserCheck,
  Flag,
} from 'lucide-react'
import { fetchChannels } from '@/services/channels'
import { createBotFlow, fetchBotFlows, updateBotFlow } from '@/services/chatbot'
import { fetchTeams } from '@/services/teams'
import type { BotFlow, BotNodeType, GeneratedBotFlow } from '@/types'
import { nodeTypes } from '@/components/chatbot/FlowNodes'
import { ChatbotChannelContext } from '@/components/chatbot/chatbotChannelContext'
import FlowAssistantChat from '@/components/chatbot/FlowAssistantChat'
import CompanyScopePrompt, { useRequiresCompanyScope } from '@/components/admin/CompanyScopePrompt'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import { getActiveCompanyId } from '@/lib/companyContext'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/cn'
import { validateBotFlow } from '@/lib/validateBotFlow'

const PALETTE: { type: BotNodeType; label: string; icon: typeof MessageSquare; color: string }[] = [
  { type: 'message', label: 'Mensagem', icon: MessageSquare, color: 'border-emerald-600 hover:bg-emerald-900/30' },
  { type: 'menu', label: 'Menu 1/2/3', icon: ListOrdered, color: 'border-violet-600 hover:bg-violet-900/30' },
  { type: 'decision', label: 'Sim/Não', icon: GitBranch, color: 'border-amber-600 hover:bg-amber-900/30' },
  { type: 'assign', label: 'Atribuir', icon: UserCheck, color: 'border-blue-600 hover:bg-blue-900/30' },
  { type: 'end', label: 'Fim', icon: Flag, color: 'border-gray-600 hover:bg-gray-800/50' },
]

function createDefaultFlow(channelId: number) {
  const startId = 'start'
  return {
    channel: channelId,
    name: 'Fluxo principal',
    is_active: false,
    start_node_id: startId,
    definition: {
      nodes: [
        {
          id: startId,
          type: 'message' as BotNodeType,
          position: { x: 280, y: 80 },
          data: { content: 'Olá! Bem-vindo ao nosso atendimento.' },
        },
      ],
      edges: [],
    },
  }
}

function FlowCanvas() {
  const { fitView } = useReactFlow()
  const queryClient = useQueryClient()
  const companyId = getActiveCompanyId()
  const selectedCompanyId = useAuthStore((s) => s.selectedCompanyId)
  const showScopePrompt = useRequiresCompanyScope()
  const queriesEnabled = !showScopePrompt
  const [selectedChannelId, setSelectedChannelId] = useState<number | ''>('')
  const [currentFlow, setCurrentFlow] = useState<BotFlow | null>(null)
  const [startNodeId, setStartNodeId] = useState('')
  const [isActive, setIsActive] = useState(false)
  const [flowName, setFlowName] = useState('Fluxo principal')
  const [saveError, setSaveError] = useState('')
  const [apiError, setApiError] = useState('')
  const [nodeCounter, setNodeCounter] = useState(1)
  const loadedKeyRef = useRef<string | null>(null)

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  const { data: channels = [] } = useQuery({
    queryKey: ['channels', companyId],
    queryFn: () => fetchChannels(),
    enabled: queriesEnabled,
  })

  const { data: teamsData } = useQuery({
    queryKey: ['teams', companyId],
    queryFn: fetchTeams,
    enabled: queriesEnabled,
  })

  const channelTeams = useMemo(() => {
    if (!selectedChannelId) return []
    const cid = Number(selectedChannelId)
    return (
      teamsData?.results
        ?.filter((t) => t.is_active && t.channels.some((c) => c.id === cid))
        .map((t) => ({ id: t.id, name: t.name })) ?? []
    )
  }, [teamsData, selectedChannelId])

  const { data: flows = [], isLoading: flowsLoading, isError: flowsError } = useQuery({
    queryKey: ['bot-flows', companyId, selectedChannelId],
    queryFn: () => fetchBotFlows(Number(selectedChannelId)),
    enabled: queriesEnabled && !!selectedChannelId,
    retry: false,
  })

  useEffect(() => {
    setSelectedChannelId('')
    loadedKeyRef.current = null
    setCurrentFlow(null)
    setNodes([])
    setEdges([])
  }, [selectedCompanyId, setNodes, setEdges])

  useEffect(() => {
    if (flowsError) {
      setApiError(
        'API de chatbot indisponível. Reinicie o backend e execute: python manage.py migrate',
      )
    } else {
      setApiError('')
    }
  }, [flowsError])

  useEffect(() => {
    if (!selectedChannelId) {
      loadedKeyRef.current = null
      setCurrentFlow(null)
      setNodes([])
      setEdges([])
      return
    }
    if (flowsLoading || flowsError) return

    const flow = flows.find((f) => f.channel === Number(selectedChannelId))
    const loadKey = flow
      ? `flow-${flow.id}-${flow.updated_at}`
      : `channel-${selectedChannelId}-default`

    if (loadedKeyRef.current === loadKey) return
    loadedKeyRef.current = loadKey

    if (flow) {
      setCurrentFlow(flow)
      setStartNodeId(flow.start_node_id)
      setIsActive(flow.is_active)
      setFlowName(flow.name)
      setNodes((flow.definition?.nodes || []) as Node[])
      setEdges((flow.definition?.edges || []) as Edge[])
      setNodeCounter((flow.definition?.nodes?.length || 0) + 1)
    } else {
      setCurrentFlow(null)
      const defaults = createDefaultFlow(Number(selectedChannelId))
      setStartNodeId(defaults.start_node_id)
      setIsActive(false)
      setFlowName(defaults.name)
      setNodes(defaults.definition.nodes as Node[])
      setEdges([])
      setNodeCounter(2)
    }

    requestAnimationFrame(() => {
      fitView({ padding: 0.2, duration: 200 })
    })
  }, [selectedChannelId, flows, flowsLoading, flowsError, setNodes, setEdges])

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            id: `e-${connection.source}-${connection.target}-${connection.sourceHandle || 'out'}`,
          },
          eds,
        ),
      )
    },
    [setEdges],
  )

  const addNode = (type: BotNodeType) => {
    const id = `${type}-${nodeCounter}`
    setNodeCounter((c) => c + 1)
    const yOffset = nodes.length * 40
    setNodes((nds) => [
      ...nds,
      {
        id,
        type,
        position: { x: 120 + yOffset, y: 200 + yOffset },
        data:
          type === 'menu'
            ? { content: '', options: ['1', '2', '3'] }
            : type === 'assign'
              ? { content: '', team_id: channelTeams[0]?.id ?? null }
              : { content: '' },
      },
    ])
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const validationError = validateBotFlow(nodes, edges, startNodeId)
      if (validationError) throw new Error(validationError)

      const definition = {
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type as BotNodeType,
          position: n.position,
          data: n.data as { content?: string; options?: string[]; team_id?: number | null },
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || undefined,
        })),
      }

      const payload = {
        name: flowName,
        is_active: isActive,
        definition,
        start_node_id: startNodeId,
      }

      if (currentFlow) {
        return updateBotFlow(currentFlow.id, payload)
      }
      return createBotFlow({
        channel: Number(selectedChannelId),
        ...payload,
      })
    },
    onSuccess: (flow) => {
      setSaveError('')
      setApiError('')
      setCurrentFlow(flow)
      loadedKeyRef.current = `flow-${flow.id}-${flow.updated_at}`
      queryClient.invalidateQueries({ queryKey: ['bot-flows', selectedChannelId] })
    },
    onError: (err: unknown) => {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data
        if (err.response?.status === 404) {
          setSaveError('API não encontrada. Reinicie o backend após aplicar as migrations.')
          return
        }
        if (typeof data === 'object' && data) {
          const first = Object.values(data)[0]
          if (Array.isArray(first)) {
            setSaveError(String(first[0]))
            return
          }
          if (typeof first === 'string') {
            setSaveError(first)
            return
          }
        }
      }
      if (err instanceof Error) {
        setSaveError(err.message)
        return
      }
      setSaveError('Erro ao salvar fluxo.')
    },
  })

  const startNodeOptions = useMemo(
    () => nodes.map((n) => ({ id: n.id, label: `${n.type} (${n.id})` })),
    [nodes],
  )

  const currentFlowContext = useMemo(() => {
    if (!selectedChannelId || nodes.length === 0) return null
    return {
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type as BotNodeType,
        position: n.position,
        data: n.data as { content?: string; options?: string[]; team_id?: number | null },
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle || undefined,
      })),
      start_node_id: startNodeId,
    }
  }, [selectedChannelId, nodes, edges, startNodeId])

  const applyGeneratedFlow = useCallback(
    (flow: GeneratedBotFlow) => {
      loadedKeyRef.current = null
      setFlowName(flow.name)
      setStartNodeId(flow.start_node_id)
      setNodes(flow.nodes as Node[])
      setEdges(flow.edges as Edge[])
      setNodeCounter(flow.nodes.length + 1)
      requestAnimationFrame(() => {
        fitView({ padding: 0.2, duration: 300 })
      })
    },
    [fitView, setNodes, setEdges],
  )

  if (showScopePrompt) {
    return (
      <CompanyScopePrompt
        title="Selecione uma empresa"
        description="Use o seletor de empresa no topo para configurar fluxos de chatbot."
      />
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="p-4 sm:p-6 border-b border-wa-border shrink-0">
        <div className="max-w-6xl">
        <PageHeader
          title="Chatbot"
          description="Configure fluxos automáticos por canal. O bot responde quando nenhum atendente assumiu a conversa."
        />

        {channels.length === 0 ? (
          <div className="max-w-lg mx-auto mt-4">
            <Card padding="lg" className="border-dashed border-wa-border/80 text-center">
              <EmptyState
                icon={Bot}
                title="Nenhum canal disponível"
                description="Para configurar fluxos automáticos, primeiro crie e conecte um canal WhatsApp."
                action={
                  <div className="space-y-4">
                    <ol className="text-left text-xs text-wa-muted space-y-2 max-w-xs mx-auto">
                      <li className="flex gap-2">
                        <span className="w-5 h-5 rounded-full bg-wa-green/20 text-wa-green text-[10px] font-bold flex items-center justify-center shrink-0">1</span>
                        Acesse Canais e crie um canal WhatsApp
                      </li>
                      <li className="flex gap-2">
                        <span className="w-5 h-5 rounded-full bg-wa-green/20 text-wa-green text-[10px] font-bold flex items-center justify-center shrink-0">2</span>
                        Conecte via QR Code ou Meta Cloud API
                      </li>
                      <li className="flex gap-2">
                        <span className="w-5 h-5 rounded-full bg-wa-green/20 text-wa-green text-[10px] font-bold flex items-center justify-center shrink-0">3</span>
                        Volte aqui para montar o fluxo do bot
                      </li>
                    </ol>
                    <Link to="/admin/channels">
                      <Button>
                        <Bot className="w-4 h-4" />
                        Ir para Canais
                      </Button>
                    </Link>
                  </div>
                }
              />
            </Card>
          </div>
        ) : (
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-wa-muted mb-1">Canal</label>
              <select
                value={selectedChannelId}
                onChange={(e) => {
                  loadedKeyRef.current = null
                  setSelectedChannelId(e.target.value ? Number(e.target.value) : '')
                }}
                className="px-3 py-2 bg-gray-800 border border-wa-border rounded-lg text-sm min-w-[200px]"
              >
                <option value="">Selecione um canal...</option>
                {channels.map((ch) => (
                  <option key={ch.id} value={ch.id}>
                    {ch.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedChannelId && (
              <>
                <div>
                  <label className="block text-xs text-wa-muted mb-1">Nome do fluxo</label>
                  <input
                    value={flowName}
                    onChange={(e) => setFlowName(e.target.value)}
                    className="px-3 py-2 bg-gray-800 border border-wa-border rounded-lg text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs text-wa-muted mb-1">Nó inicial</label>
                  <select
                    value={startNodeId}
                    onChange={(e) => setStartNodeId(e.target.value)}
                    className="px-3 py-2 bg-gray-800 border border-wa-border rounded-lg text-sm min-w-[180px]"
                  >
                    <option value="">Selecione...</option>
                    {startNodeOptions.map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-wa-border rounded-lg cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="accent-wa-green"
                  />
                  <span className="text-sm">Ativo</span>
                </label>

                <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
                  <Save className="w-4 h-4" />
                  Salvar fluxo
                </Button>
              </>
            )}
          </div>
        )}

        {apiError && (
          <p className="text-yellow-400 text-sm mt-2">{apiError}</p>
        )}
        {saveError && (
          <p className="text-red-400 text-sm mt-2">{saveError}</p>
        )}
        </div>
      </div>

      {selectedChannelId && !flowsError && (
        <div className="flex flex-1 min-h-0">
          <aside className="w-48 border-r border-wa-border p-3 shrink-0 overflow-y-auto bg-wa-panel/50">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-wa-muted mb-3">
              Adicionar nó
            </p>
            <div className="space-y-2">
              {PALETTE.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.type}
                    onClick={() => addNode(item.type)}
                    className={cn(
                      'w-full flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all',
                      'hover:-translate-y-0.5 active:scale-95',
                      item.color,
                    )}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    {item.label}
                  </button>
                )
              })}
            </div>
            <p className="text-[10px] text-wa-muted mt-4 leading-relaxed">
              Mensagem avança sozinha. Perguntas Sim/Não precisam do nó Sim/Não (yes→Atribuir, no→Fim). Menu aguarda 1/2/3.
            </p>
          </aside>

          <div className="flex-1 bg-wa-chat">
            <ChatbotChannelContext.Provider value={{ channelTeams }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              className="bg-wa-chat"
              defaultEdgeOptions={{ animated: true, style: { stroke: '#00A3FF' } }}
            >
              <Background gap={20} size={1} color="#2A3942" />
              <Controls className="!bg-wa-panel !border-wa-border !shadow-panel" />
              <MiniMap
                className="!bg-wa-panel !border-wa-border"
                nodeColor={(n) => {
                  if (n.type === 'menu') return '#7c3aed'
                  if (n.type === 'decision') return '#d97706'
                  if (n.type === 'assign') return '#2563eb'
                  if (n.type === 'end') return '#6b7280'
                  return '#059669'
                }}
              />
            </ReactFlow>
            </ChatbotChannelContext.Provider>
          </div>

          <FlowAssistantChat
            currentFlow={currentFlowContext}
            onFlowGenerated={applyGeneratedFlow}
            disabled={!selectedChannelId}
          />
        </div>
      )}
    </div>
  )
}

export default function ChatbotPage() {
  return (
    <ReactFlowProvider>
      <FlowCanvas />
    </ReactFlowProvider>
  )
}
