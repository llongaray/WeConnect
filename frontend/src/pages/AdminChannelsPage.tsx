import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  Building2,
  Cloud,
  Copy,
  Plus,
  QrCode,
  Radio,
  Smartphone,
} from 'lucide-react'
import {
  connectChannel,
  createChannel,
  deleteChannel,
  disconnectChannel,
  fetchChannelStatus,
  fetchChannels,
} from '@/services/channels'
import type { Channel, ChannelType, CreateChannelPayload } from '@/types'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonList } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'

const statusLabel: Record<string, string> = {
  open: 'Conectado',
  connecting: 'Aguardando QR Code',
  close: 'Desconectado',
}

function getChannelStatusLabel(channel: Channel): string {
  if (channel.status === 'connecting' && channel.qrcode_base64) {
    return 'Aguardando leitura do QR Code'
  }
  return statusLabel[channel.status] || channel.status
}

interface ChannelTypeOption {
  value: ChannelType
  label: string
  description: string
  group: string
  icon: typeof Smartphone
}

const channelTypeOptions: ChannelTypeOption[] = [
  {
    value: 'evolution_normal',
    label: 'WhatsApp Normal',
    description: 'Conexão via QR Code usando Evolution API (Baileys).',
    group: 'Evolution API',
    icon: Smartphone,
  },
  {
    value: 'evolution_business',
    label: 'WhatsApp Business',
    description: 'QR Code com o app WhatsApp Business no celular.',
    group: 'Evolution API',
    icon: Building2,
  },
  {
    value: 'meta_cloud',
    label: 'API Oficial Meta',
    description: 'WhatsApp Cloud API da Meta — sem Evolution.',
    group: 'API Oficial',
    icon: Cloud,
  },
]

const channelGroups = ['Evolution API', 'API Oficial']

export default function AdminChannelsPage() {
  const queryClient = useQueryClient()
  const [showWizard, setShowWizard] = useState(false)
  const [wizardStep, setWizardStep] = useState(0)
  const [selectedChannelId, setSelectedChannelId] = useState<number | null>(null)
  const [copied, setCopied] = useState(false)
  const [form, setForm] = useState<CreateChannelPayload>({
    name: '',
    channel_type: 'evolution_normal',
    phone_number_id: '',
    access_token: '',
    verify_token: '',
    waba_id: '',
  })
  const [error, setError] = useState('')

  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: fetchChannels,
    refetchInterval: 5000,
  })

  const selectedChannel = channels.find((c) => c.id === selectedChannelId) || null

  const { data: channelDetail } = useQuery({
    queryKey: ['channel-status', selectedChannelId],
    queryFn: () => fetchChannelStatus(selectedChannelId!),
    enabled: !!selectedChannelId,
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'connecting' ? 2000 : 5000
    },
  })

  const displayChannel = channelDetail || selectedChannel

  const createMutation = useMutation({
    mutationFn: createChannel,
    onSuccess: (channel) => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      resetWizard()
      setSelectedChannelId(channel.id)
      queryClient.invalidateQueries({ queryKey: ['channel-status', channel.id] })
      if (channel.channel_type !== 'meta_cloud' && !channel.qrcode_base64) {
        connectMutation.mutate({ id: channel.id, reset: false })
      }
    },
    onError: (err: unknown) => {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data
        if (typeof data?.detail === 'string') {
          setError(data.detail)
          return
        }
        const firstField = data && typeof data === 'object' ? Object.values(data)[0] : null
        if (Array.isArray(firstField) && firstField[0]) {
          setError(String(firstField[0]))
          return
        }
        if (typeof firstField === 'string') {
          setError(firstField)
          return
        }
      }
      setError('Erro ao criar canal. Verifique os dados e tente novamente.')
    },
  })

  const connectMutation = useMutation({
    mutationFn: ({ id, reset }: { id: number; reset?: boolean }) => connectChannel(id, reset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['channel-status'] })
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: disconnectChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['channel-status'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteChannel,
    onSuccess: () => {
      setSelectedChannelId(null)
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    },
  })

  const handleCreate = () => {
    setError('')
    if (!form.name.trim()) {
      setError('Informe o nome do canal.')
      return
    }
    createMutation.mutate(form)
  }

  const resetWizard = () => {
    setShowWizard(false)
    setWizardStep(0)
    setError('')
    setForm({
      name: '',
      channel_type: 'evolution_normal',
      phone_number_id: '',
      access_token: '',
      verify_token: '',
      waba_id: '',
    })
  }

  const copyWebhook = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard indisponível */
    }
  }

  const statusVariant = (status: string) => {
    if (status === 'open') return 'success' as const
    if (status === 'connecting') return 'warning' as const
    return 'danger' as const
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Canais WhatsApp"
        description="Gerencie conexões Evolution API e Meta Cloud API."
        actions={
          <Button onClick={() => setShowWizard(true)}>
            <Plus className="w-4 h-4" />
            Novo canal
          </Button>
        }
      />

      <Modal
        open={showWizard}
        onClose={resetWizard}
        title="Criar novo canal"
        step={wizardStep}
        totalSteps={2}
      >
        {wizardStep === 0 && (
          <>
            <Input
              label="Nome do canal"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: Atendimento Principal"
            />
            <div className="flex gap-2 justify-end mt-6">
              <Button variant="ghost" onClick={resetWizard}>
                Cancelar
              </Button>
              <Button
                onClick={() => setWizardStep(1)}
                disabled={!form.name.trim()}
              >
                Próximo
              </Button>
            </div>
          </>
        )}

        {wizardStep === 1 && (
          <>
            <p className="text-sm text-wa-muted mb-3">Selecione o tipo de canal:</p>

            {channelGroups.map((group) => (
              <div key={group} className="mb-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-2">
                  {group}
                </p>
                <div className="space-y-2">
                  {channelTypeOptions
                    .filter((opt) => opt.group === group)
                    .map((opt) => {
                      const Icon = opt.icon
                      return (
                        <label
                          key={opt.value}
                          className={cn(
                            'flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-all duration-200',
                            form.channel_type === opt.value
                              ? 'border-wa-green bg-wa-green/10 shadow-glow-green/20'
                              : 'border-wa-border hover:border-gray-500',
                          )}
                        >
                          <input
                            type="radio"
                            name="channel_type"
                            value={opt.value}
                            checked={form.channel_type === opt.value}
                            onChange={() => setForm({ ...form, channel_type: opt.value })}
                            className="mt-1"
                          />
                          <Icon className="w-5 h-5 text-wa-green shrink-0 mt-0.5" />
                          <div>
                            <span className="font-medium">{opt.label}</span>
                            <p className="text-xs text-wa-muted mt-0.5">{opt.description}</p>
                          </div>
                        </label>
                      )
                    })}
                </div>
              </div>
            ))}

            {form.channel_type === 'meta_cloud' && (
              <div className="space-y-3 mb-4 p-3 bg-gray-800/50 rounded-lg border border-wa-border">
                <Input
                  value={form.phone_number_id}
                  onChange={(e) => setForm({ ...form, phone_number_id: e.target.value })}
                  placeholder="Phone Number ID *"
                />
                <Input
                  value={form.access_token}
                  onChange={(e) => setForm({ ...form, access_token: e.target.value })}
                  placeholder="Access Token *"
                  type="password"
                />
                <Input
                  value={form.verify_token}
                  onChange={(e) => setForm({ ...form, verify_token: e.target.value })}
                  placeholder="Verify Token (webhook)"
                />
                <Input
                  value={form.waba_id}
                  onChange={(e) => setForm({ ...form, waba_id: e.target.value })}
                  placeholder="WABA ID (opcional)"
                />
              </div>
            )}

            {error && (
              <p className="text-red-400 text-sm mb-3 animate-fade-in">{error}</p>
            )}

            <div className="flex gap-2 justify-end mt-4">
              <Button variant="ghost" onClick={() => setWizardStep(0)}>
                Voltar
              </Button>
              <Button onClick={handleCreate} loading={createMutation.isPending}>
                {createMutation.isPending ? 'Criando...' : 'Criar canal'}
              </Button>
            </div>
          </>
        )}
      </Modal>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {isLoading && <SkeletonList count={3} />}

          {!isLoading && channels.length === 0 && (
            <EmptyState
              icon={Radio}
              title="Nenhum canal criado"
              description='Clique em "Novo canal" para conectar seu primeiro WhatsApp.'
              action={
                <Button onClick={() => setShowWizard(true)}>
                  <Plus className="w-4 h-4" />
                  Criar canal
                </Button>
              }
            />
          )}

          <div className="space-y-3">
            {channels.map((channel: Channel, index) => (
              <button
                key={channel.id}
                onClick={() => setSelectedChannelId(channel.id)}
                className={cn(
                  'w-full text-left p-4 rounded-card border transition-all duration-200 animate-fade-in',
                  'hover:-translate-y-0.5 hover:shadow-panel',
                  selectedChannelId === channel.id
                    ? 'border-wa-green bg-wa-green/10'
                    : 'border-wa-border bg-wa-panel hover:border-gray-600',
                )}
                style={{ animationDelay: `${index * 40}ms` }}
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="min-w-0">
                    <p className="font-medium">{channel.name}</p>
                    <p className="text-xs text-wa-muted">{channel.channel_type_label}</p>
                  </div>
                  <Badge
                    variant={statusVariant(channel.status)}
                    pulse={channel.status === 'connecting'}
                  >
                    {getChannelStatusLabel(channel)}
                  </Badge>
                </div>
                {channel.phone && (
                  <p className="text-sm text-wa-muted mt-1">+{channel.phone}</p>
                )}
              </button>
            ))}
          </div>
        </div>

        <div>
          {displayChannel ? (
            <Card padding="lg" className="animate-fade-in">
              <h3 className="font-semibold text-lg mb-1">{displayChannel.name}</h3>
              <p className="text-sm text-wa-muted mb-4">{displayChannel.channel_type_label}</p>

              <div className="flex items-center gap-3 mb-4">
                <div
                  className={cn(
                    'w-3 h-3 rounded-full',
                    displayChannel.status === 'open'
                      ? 'bg-wa-green'
                      : displayChannel.status === 'connecting'
                        ? 'bg-yellow-400 animate-pulse'
                        : 'bg-red-500',
                  )}
                />
                <span>{getChannelStatusLabel(displayChannel)}</span>
              </div>

              {displayChannel.status === 'connecting' && !displayChannel.qrcode_base64 && (
                <p className="text-sm text-yellow-400 mb-4 p-3 bg-yellow-900/20 rounded-lg border border-yellow-700/30">
                  A instância foi criada na Evolution. Clique em &quot;Gerar QR Code&quot; para exibir o código de pareamento.
                </p>
              )}

              {displayChannel.phone && (
                <p className="text-sm text-wa-muted mb-4">Número: +{displayChannel.phone}</p>
              )}

              {displayChannel.channel_type === 'meta_cloud' && displayChannel.webhook_url && (
                <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border border-wa-border">
                  <p className="text-xs text-wa-muted mb-2">URL do Webhook (configure na Meta):</p>
                  <div className="flex items-start gap-2">
                    <code className="text-xs text-wa-green break-all flex-1">
                      {displayChannel.webhook_url}
                    </code>
                    <Button
                      variant="secondary"
                      onClick={() => copyWebhook(displayChannel.webhook_url)}
                      className="px-2 py-1 shrink-0"
                      title="Copiar URL"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      {copied ? 'Copiado!' : 'Copiar'}
                    </Button>
                  </div>
                </div>
              )}

              {displayChannel.qrcode_base64 && (
                <Card padding="md" className="mb-4 text-center shadow-panel">
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <QrCode className="w-4 h-4 text-wa-green" />
                    <p className="text-sm text-gray-300">Escaneie o QR Code com o WhatsApp:</p>
                  </div>
                  <img
                    src={displayChannel.qrcode_base64}
                    alt="QR Code WhatsApp"
                    className="mx-auto max-w-[280px] rounded-lg border border-wa-border"
                  />
                </Card>
              )}

              {displayChannel.detail && (
                <p className="text-sm text-yellow-400 mb-4">{displayChannel.detail}</p>
              )}

              <div className="flex flex-wrap gap-2">
                {displayChannel.channel_type !== 'meta_cloud' ? (
                  <Button
                    onClick={() =>
                      connectMutation.mutate({
                        id: displayChannel.id,
                        reset: !displayChannel.qrcode_base64 || displayChannel.status === 'close',
                      })
                    }
                    loading={connectMutation.isPending}
                  >
                    {connectMutation.isPending
                      ? 'Gerando QR...'
                      : displayChannel.qrcode_base64
                        ? 'Atualizar QR Code'
                        : 'Gerar QR Code'}
                  </Button>
                ) : (
                  <Button
                    onClick={() => connectMutation.mutate({ id: displayChannel.id })}
                    loading={connectMutation.isPending}
                  >
                    Validar credenciais
                  </Button>
                )}
                <Button
                  variant="secondary"
                  onClick={() => disconnectMutation.mutate(displayChannel.id)}
                  loading={disconnectMutation.isPending}
                >
                  Desconectar
                </Button>
                <Button
                  variant="danger"
                  onClick={() => {
                    if (confirm('Excluir este canal permanentemente?')) {
                      deleteMutation.mutate(displayChannel.id)
                    }
                  }}
                  loading={deleteMutation.isPending}
                >
                  Excluir
                </Button>
              </div>
            </Card>
          ) : (
            <EmptyState
              icon={Radio}
              title="Selecione um canal"
              description="Escolha um canal na lista para ver detalhes e conectar."
              className="h-full min-h-[300px] border border-wa-border rounded-card"
            />
          )}
        </div>
      </div>
    </div>
  )
}
