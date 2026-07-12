import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  Archive,
  Copy,
  Eye,
  MoreVertical,
  Plus,
  QrCode,
  Radio,
  RotateCcw,
  type LucideIcon,
} from 'lucide-react'
import {
  connectChannel,
  archiveChannel,
  createChannel,
  deactivateChannel,
  deleteChannel,
  fetchChannelStatus,
  fetchChannels,
  restoreChannel,
  revealChannelCredentials,
  revealWebhookSecret,
} from '@/services/channels'
import { fetchCompany } from '@/services/companies'
import type { Channel, ChannelType, CreateChannelPayload } from '@/types'
import { getActiveCompanyId, needsPlatformCompanyScope } from '@/lib/companyContext'
import { useAuthStore } from '@/store/authStore'
import UsageDashboard from '@/components/admin/UsageDashboard'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonList } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'
import { confirmDialog } from '@/lib/confirmDialog'
import { getChannelTypeIcon, isMetaManualChannel } from '@/lib/channelTypes'

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
  icon: LucideIcon
}

const channelTypeOptions: ChannelTypeOption[] = [
  {
    value: 'evolution_normal',
    label: 'WhatsApp Normal',
    description: 'Conexão via QR Code usando Evolution API (Baileys).',
    group: 'Evolution API',
    icon: getChannelTypeIcon('evolution_normal'),
  },
  {
    value: 'evolution_business',
    label: 'WhatsApp Business',
    description: 'QR Code com o app WhatsApp Business no celular.',
    group: 'Evolution API',
    icon: getChannelTypeIcon('evolution_business'),
  },
  {
    value: 'meta_cloud',
    label: 'API Oficial Meta',
    description: 'WhatsApp Cloud API da Meta — sem Evolution.',
    group: 'API Oficial',
    icon: getChannelTypeIcon('meta_cloud'),
  },
  {
    value: 'meta_messenger',
    label: 'Facebook Messenger',
    description: 'Mensagens da sua Facebook Page via app Meta (BYOA).',
    group: 'Meta Messaging',
    icon: getChannelTypeIcon('meta_messenger'),
  },
  {
    value: 'meta_instagram',
    label: 'Instagram DM',
    description: 'Direct do Instagram Business vinculado à sua Page.',
    group: 'Meta Messaging',
    icon: getChannelTypeIcon('meta_instagram'),
  },
]

const channelGroups = ['Evolution API', 'API Oficial', 'Meta Messaging']

export default function AdminChannelsPage() {
  const queryClient = useQueryClient()
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const isGestor = useAuthStore((s) => s.isGestor())
  const companyId = getActiveCompanyId()
  const platformScope = needsPlatformCompanyScope()
  const hasCompanyScope = !platformScope || Boolean(companyId)
  const [activeTab, setActiveTab] = useState<'active' | 'archived'>('active')
  const [showWizard, setShowWizard] = useState(false)
  const [wizardStep, setWizardStep] = useState(0)
  const [selectedChannelId, setSelectedChannelId] = useState<number | null>(null)
  const [openMenuId, setOpenMenuId] = useState<number | null>(null)
  const [copied, setCopied] = useState(false)
  const [revealedMeta, setRevealedMeta] = useState<Record<number, Record<string, string>>>({})
  const [revealedWebhook, setRevealedWebhook] = useState<Record<number, { secret: string; header: string }>>({})
  const [revealLoadingId, setRevealLoadingId] = useState<number | null>(null)
  const [form, setForm] = useState<CreateChannelPayload>({
    name: '',
    channel_type: 'evolution_normal',
    phone_number_id: '',
    access_token: '',
    verify_token: '',
    waba_id: '',
    app_id: '',
    app_secret: '',
    page_id: '',
    page_access_token: '',
    instagram_business_account_id: '',
  })
  const [error, setError] = useState('')

  const { data: channels = [], isLoading, isError } = useQuery({
    queryKey: ['channels', companyId, 'management'],
    queryFn: () => fetchChannels({ companyId, includeInactive: true, includeArchived: true }),
    enabled: hasCompanyScope,
    refetchInterval: 5000,
  })

  const { data: companyData } = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompany(companyId!),
    enabled: Boolean(companyId),
  })

  const activeChannels = channels.filter((channel) => !channel.is_archived)
  const archivedChannels = channels.filter((channel) => channel.is_archived)
  const visibleChannels = activeTab === 'active' ? activeChannels : archivedChannels
  const selectedChannel = visibleChannels.find((c) => c.id === selectedChannelId) || null

  const { data: channelDetail } = useQuery({
    queryKey: ['channel-status', selectedChannelId],
    queryFn: () => fetchChannelStatus(selectedChannelId!),
    enabled: !!selectedChannelId,
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'connecting' ? 2000 : 5000
    },
  })

  const displayChannel = channelDetail?.id === selectedChannelId ? channelDetail : selectedChannel

  const createMutation = useMutation({
    mutationFn: createChannel,
    onSuccess: (channel) => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['company'] })
      resetWizard()
      setSelectedChannelId(channel.id)
      queryClient.invalidateQueries({ queryKey: ['channel-status', channel.id] })
      if (!isMetaManualChannel(channel.channel_type) && !channel.qrcode_base64) {
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
    mutationFn: async ({ id, reset, reactivate }: { id: number; reset?: boolean; reactivate?: boolean }) => {
      if (reactivate) {
        await restoreChannel(id, true)
      }
      return connectChannel(id, reset)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['channel-status'] })
      queryClient.invalidateQueries({ queryKey: ['company'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteChannel,
    onSuccess: () => {
      setSelectedChannelId(null)
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['company'] })
    },
  })

  const invalidateChannels = () => {
    queryClient.invalidateQueries({ queryKey: ['channels'] })
    queryClient.invalidateQueries({ queryKey: ['channel-status'] })
    queryClient.invalidateQueries({ queryKey: ['company'] })
  }

  const deactivateMutation = useMutation({
    mutationFn: deactivateChannel,
    onSuccess: invalidateChannels,
  })

  const archiveMutation = useMutation({
    mutationFn: archiveChannel,
    onSuccess: () => {
      setSelectedChannelId(null)
      setOpenMenuId(null)
      invalidateChannels()
    },
  })

  const restoreMutation = useMutation({
    mutationFn: (id: number) => restoreChannel(id, true),
    onSuccess: () => {
      setActiveTab('active')
      invalidateChannels()
    },
  })

  useEffect(() => {
    const closeMenu = () => setOpenMenuId(null)
    if (openMenuId !== null) {
      document.addEventListener('click', closeMenu)
      return () => document.removeEventListener('click', closeMenu)
    }
  }, [openMenuId])

  const handleCreate = () => {
    setError('')
    if (!form.name.trim()) {
      setError('Informe o nome do canal.')
      return
    }
    if (!companyId) {
      setError('Selecione uma empresa antes de criar o canal.')
      return
    }
    createMutation.mutate({ ...form, company_id: companyId })
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
      app_id: '',
      app_secret: '',
      page_id: '',
      page_access_token: '',
      instagram_business_account_id: '',
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

  const handleRevealMeta = async (channelId: number) => {
    const password = window.prompt('Confirme sua senha para revelar credenciais Meta:')
    if (!password) return
    setRevealLoadingId(channelId)
    try {
      const creds = await revealChannelCredentials(channelId, { password })
      setRevealedMeta((prev) => ({ ...prev, [channelId]: creds }))
    } catch {
      setError('Não foi possível revelar credenciais Meta.')
    } finally {
      setRevealLoadingId(null)
    }
  }

  const handleRevealWebhook = async (channelId: number) => {
    const password = window.prompt('Confirme sua senha para revelar o secret do webhook:')
    if (!password) return
    setRevealLoadingId(channelId)
    try {
      const data = await revealWebhookSecret(channelId, { password })
      setRevealedWebhook((prev) => ({
        ...prev,
        [channelId]: { secret: data.webhook_secret, header: data.webhook_header },
      }))
    } catch {
      setError('Não foi possível revelar o secret do webhook.')
    } finally {
      setRevealLoadingId(null)
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
        title="Canais omnichannel"
        description="Gerencie WhatsApp, Facebook Messenger e Instagram."
        actions={
          <Button onClick={() => setShowWizard(true)} disabled={!hasCompanyScope}>
            <Plus className="w-4 h-4" />
            Novo canal
          </Button>
        }
      />

      <UsageDashboard usage={companyData?.usage} only="channels" />

      <div className="flex border-b border-wa-border mb-5">
        <button
          type="button"
          onClick={() => {
            setActiveTab('active')
            setSelectedChannelId(null)
            setOpenMenuId(null)
          }}
          className={cn(
            'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'active'
              ? 'border-wa-green text-wa-green'
              : 'border-transparent text-wa-muted hover:text-white',
          )}
        >
          Canais (Em uso) <span className="ml-1 text-xs">({activeChannels.length})</span>
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab('archived')
            setSelectedChannelId(null)
            setOpenMenuId(null)
          }}
          className={cn(
            'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'archived'
              ? 'border-wa-green text-wa-green'
              : 'border-transparent text-wa-muted hover:text-white',
          )}
        >
          Canais arquivados <span className="ml-1 text-xs">({archivedChannels.length})</span>
        </button>
      </div>

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

            {(form.channel_type === 'meta_messenger' || form.channel_type === 'meta_instagram') && (
              <div className="space-y-3 mb-4 p-3 bg-gray-800/50 rounded-lg border border-wa-border">
                <p className="text-xs text-wa-muted">
                  Use o app Meta da sua empresa em developers.facebook.com. Configure o webhook
                  após criar o canal com o Verify Token informado abaixo.
                </p>
                <Input
                  value={form.app_id}
                  onChange={(e) => setForm({ ...form, app_id: e.target.value })}
                  placeholder="App ID *"
                />
                <Input
                  value={form.app_secret}
                  onChange={(e) => setForm({ ...form, app_secret: e.target.value })}
                  placeholder="App Secret *"
                  type="password"
                />
                <Input
                  value={form.page_id}
                  onChange={(e) => setForm({ ...form, page_id: e.target.value })}
                  placeholder="Facebook Page ID *"
                />
                <Input
                  value={form.page_access_token}
                  onChange={(e) => setForm({ ...form, page_access_token: e.target.value })}
                  placeholder="Page Access Token *"
                  type="password"
                />
                <Input
                  value={form.verify_token}
                  onChange={(e) => setForm({ ...form, verify_token: e.target.value })}
                  placeholder="Verify Token (webhook) *"
                />
                {form.channel_type === 'meta_instagram' && (
                  <Input
                    value={form.instagram_business_account_id}
                    onChange={(e) =>
                      setForm({ ...form, instagram_business_account_id: e.target.value })
                    }
                    placeholder="Instagram Business Account ID *"
                  />
                )}
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

      <div>
        {isLoading && <SkeletonList count={3} />}

        {isError && (
          <Card padding="md" className="mb-4 border-red-500/40 bg-red-950/20">
            <p className="text-sm text-red-300">Não foi possível carregar os canais. Tente recarregar a página.</p>
          </Card>
        )}

        {!isLoading && !isError && visibleChannels.length === 0 && (
          <EmptyState
            icon={activeTab === 'active' ? Radio : Archive}
            title={activeTab === 'active' ? 'Nenhum canal em uso' : 'Nenhum canal arquivado'}
            description={
              activeTab === 'active'
                ? 'Clique em "Novo canal" para conectar seu primeiro WhatsApp.'
                : 'Os canais arquivados aparecerão aqui.'
            }
            action={
              activeTab === 'active' ? (
                <Button onClick={() => setShowWizard(true)}>
                  <Plus className="w-4 h-4" />
                  Criar canal
                </Button>
              ) : undefined
            }
          />
        )}

        <div className="space-y-3">
          {visibleChannels.map((channel: Channel, index) => {
            const isExpanded = selectedChannelId === channel.id
            const expandedChannel = isExpanded && displayChannel ? displayChannel : channel
            const ChannelIcon = getChannelTypeIcon(channel.channel_type)

            return (
              <div
                key={channel.id}
                className={cn(
                  'relative rounded-card border bg-wa-panel transition-all duration-200 animate-fade-in',
                  isExpanded ? 'border-wa-green shadow-panel' : 'border-wa-border hover:border-gray-600',
                )}
                style={{ animationDelay: `${index * 40}ms` }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setSelectedChannelId(isExpanded ? null : channel.id)
                    setOpenMenuId(null)
                  }}
                  className="w-full text-left p-4 pr-14"
                >
                  <div className="flex justify-between items-start gap-3">
                    <div className="min-w-0 flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-gray-800 border border-wa-border shrink-0">
                        <ChannelIcon className="w-5 h-5 text-wa-green" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium">{channel.name}</p>
                        <p className="text-xs text-wa-muted">{channel.channel_type_label}</p>
                        {channel.phone && <p className="text-sm text-wa-muted mt-1">+{channel.phone}</p>}
                      </div>
                    </div>
                    <Badge variant={channel.is_archived ? 'default' : statusVariant(channel.status)}>
                      {channel.is_archived ? 'Arquivado' : getChannelStatusLabel(channel)}
                    </Badge>
                  </div>
                </button>

                <button
                  type="button"
                  aria-label={`Ações do canal ${channel.name}`}
                  onClick={(event) => {
                    event.stopPropagation()
                    setOpenMenuId(openMenuId === channel.id ? null : channel.id)
                  }}
                  className="absolute right-3 top-3 p-2 rounded-lg text-wa-muted hover:text-white hover:bg-gray-700 transition-colors"
                >
                  <MoreVertical className="w-5 h-5" />
                </button>

                {openMenuId === channel.id && (
                  <div
                    className="absolute right-3 top-12 z-20 min-w-[190px] overflow-hidden rounded-lg border border-wa-border bg-gray-800 shadow-xl"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {channel.status === 'close' && !channel.is_archived && (
                      <button
                        type="button"
                        onClick={() => {
                          setOpenMenuId(null)
                          setSelectedChannelId(channel.id)
                          connectMutation.mutate({
                            id: channel.id,
                            reset: !isMetaManualChannel(channel.channel_type),
                            reactivate: !channel.is_active,
                          })
                        }}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-700"
                      >
                        <QrCode className="w-4 h-4" />
                        {isMetaManualChannel(channel.channel_type)
                          ? 'Validar credenciais'
                          : 'Gerar QR Code'}
                      </button>
                    )}

                    {channel.status === 'open' && !channel.is_archived && (
                      <button
                        type="button"
                        onClick={async () => {
                          setOpenMenuId(null)
                          const ok = await confirmDialog({
                            title: 'Desconectar canal',
                            message: 'Desconectar este canal? Ele será inativado e deixará de consumir licença.',
                            confirmLabel: 'Desconectar',
                            variant: 'danger',
                          })
                          if (ok) deactivateMutation.mutate(channel.id)
                        }}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-700"
                      >
                        <Radio className="w-4 h-4" />
                        Desconectar
                      </button>
                    )}

                    {!channel.is_archived && (isGestor || isSuperUser) && (
                      <button
                        type="button"
                        onClick={async () => {
                          setOpenMenuId(null)
                          const ok = await confirmDialog({
                            title: 'Arquivar canal',
                            message: 'Arquivar este canal? Ele ficará oculto da operação.',
                            confirmLabel: 'Arquivar',
                          })
                          if (ok) archiveMutation.mutate(channel.id)
                        }}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-700"
                      >
                        <Archive className="w-4 h-4" />
                        Arquivar
                      </button>
                    )}

                    {channel.is_archived && (isGestor || isSuperUser) && (
                      <button
                        type="button"
                        onClick={() => {
                          setOpenMenuId(null)
                          restoreMutation.mutate(channel.id)
                        }}
                        className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-700"
                      >
                        <RotateCcw className="w-4 h-4" />
                        Restaurar
                      </button>
                    )}

                    {isSuperUser && (
                      <button
                        type="button"
                        onClick={async () => {
                          setOpenMenuId(null)
                          const ok = await confirmDialog({
                            title: 'Excluir canal',
                            message: 'Excluir este canal permanentemente? Esta ação não pode ser desfeita.',
                            confirmLabel: 'Excluir',
                            variant: 'danger',
                          })
                          if (ok) deleteMutation.mutate(channel.id)
                        }}
                        className="flex w-full items-center gap-2 border-t border-wa-border px-4 py-2.5 text-sm text-red-400 hover:bg-red-900/20"
                      >
                        Excluir
                      </button>
                    )}
                  </div>
                )}

                {isExpanded && (
                  <div className="border-t border-wa-border px-4 py-5 animate-fade-in">
                    <div className="flex items-center gap-3 mb-4">
                      <div
                        className={cn(
                          'w-3 h-3 rounded-full',
                          expandedChannel.status === 'open'
                            ? 'bg-wa-green'
                            : expandedChannel.status === 'connecting'
                              ? 'bg-yellow-400 animate-pulse'
                              : 'bg-red-500',
                        )}
                      />
                      <span>{getChannelStatusLabel(expandedChannel)}</span>
                    </div>

                    {expandedChannel.channel_type !== 'meta_cloud' &&
                      !expandedChannel.channel_type.startsWith('meta_') &&
                      expandedChannel.webhook_url && (
                      <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border border-wa-border">
                        <p className="text-xs text-wa-muted mb-2">
                          Webhook Evolution (use header {expandedChannel.webhook_header || 'X-Webhook-Secret'}):
                        </p>
                        <div className="flex items-start gap-2 mb-2">
                          <code className="text-xs text-wa-green break-all flex-1">
                            {expandedChannel.webhook_url}
                          </code>
                          <Button
                            variant="secondary"
                            onClick={() => copyWebhook(expandedChannel.webhook_url)}
                            className="px-2 py-1 shrink-0"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                        {!revealedWebhook[expandedChannel.id] ? (
                          <Button
                            variant="secondary"
                            className="text-xs"
                            loading={revealLoadingId === expandedChannel.id}
                            onClick={() => handleRevealWebhook(expandedChannel.id)}
                          >
                            Revelar secret
                          </Button>
                        ) : (
                          <p className="text-xs text-amber-200 break-all">
                            {revealedWebhook[expandedChannel.id].header}:{' '}
                            {revealedWebhook[expandedChannel.id].secret}
                          </p>
                        )}
                      </div>
                    )}

                    {(expandedChannel.channel_type === 'meta_cloud' ||
                      expandedChannel.channel_type === 'meta_messenger' ||
                      expandedChannel.channel_type === 'meta_instagram') &&
                      expandedChannel.webhook_url && (
                      <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border border-wa-border">
                        <p className="text-xs text-wa-muted mb-2">
                          URL do Webhook (configure no App Dashboard da Meta):
                        </p>
                        {expandedChannel.channel_type === 'meta_messenger' && (
                          <p className="text-[10px] text-wa-muted mb-2">
                            Inscreva o objeto <strong>Page</strong> nos campos messages e messaging_postbacks.
                          </p>
                        )}
                        {expandedChannel.channel_type === 'meta_instagram' && (
                          <p className="text-[10px] text-wa-muted mb-2">
                            Inscreva o objeto <strong>Instagram</strong> nos campos messages e messaging_postbacks.
                          </p>
                        )}
                        <div className="flex items-start gap-2">
                          <code className="text-xs text-wa-green break-all flex-1">
                            {expandedChannel.webhook_url}
                          </code>
                          <Button
                            variant="secondary"
                            onClick={() => copyWebhook(expandedChannel.webhook_url)}
                            className="px-2 py-1 shrink-0"
                            title="Copiar URL"
                          >
                            <Copy className="w-3.5 h-3.5" />
                            {copied ? 'Copiado!' : 'Copiar'}
                          </Button>
                        </div>
                      </div>
                    )}

                    {(expandedChannel.channel_type === 'meta_cloud' ||
                      expandedChannel.channel_type === 'meta_messenger' ||
                      expandedChannel.channel_type === 'meta_instagram') && (
                      <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border border-wa-border">
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <p className="text-xs text-wa-muted">Credenciais Meta (mascaradas na listagem)</p>
                          {!revealedMeta[expandedChannel.id] && (
                            <Button
                              variant="secondary"
                              className="px-2 py-1 text-xs"
                              disabled={revealLoadingId === expandedChannel.id}
                              onClick={() => void handleRevealMeta(expandedChannel.id)}
                            >
                              <Eye className="w-3.5 h-3.5 mr-1" />
                              Revelar credenciais
                            </Button>
                          )}
                        </div>
                        {expandedChannel.channel_type === 'meta_cloud' &&
                          expandedChannel.meta_credentials &&
                          !revealedMeta[expandedChannel.id] && (
                          <code className="text-xs text-wa-muted block break-all">
                            access_token: {expandedChannel.meta_credentials.access_token}
                          </code>
                        )}
                        {(expandedChannel.channel_type === 'meta_messenger' ||
                          expandedChannel.channel_type === 'meta_instagram') &&
                          expandedChannel.meta_messaging_credentials &&
                          !revealedMeta[expandedChannel.id] && (
                          <code className="text-xs text-wa-muted block break-all">
                            page_access_token:{' '}
                            {expandedChannel.meta_messaging_credentials.page_access_token}
                          </code>
                        )}
                        {revealedMeta[expandedChannel.id] && (
                          <div className="space-y-1 text-xs font-mono text-yellow-300 break-all">
                            {Object.entries(revealedMeta[expandedChannel.id]).map(([key, value]) => (
                              <p key={key}>
                                {key}: {value}
                              </p>
                            ))}
                            <p className="text-wa-muted text-[10px] mt-2">
                              Revelação registrada em audit log. Não compartilhe estes valores.
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {expandedChannel.qrcode_base64 && (
                      <Card padding="md" className="max-w-md text-center shadow-panel">
                        <div className="flex items-center justify-center gap-2 mb-3">
                          <QrCode className="w-4 h-4 text-wa-green" />
                          <p className="text-sm text-gray-300">Escaneie o QR Code com o WhatsApp:</p>
                        </div>
                        <img
                          src={expandedChannel.qrcode_base64}
                          alt="QR Code WhatsApp"
                          className="mx-auto max-w-[280px] rounded-lg border border-wa-border"
                        />
                      </Card>
                    )}

                    {expandedChannel.detail && (
                      <p className="text-sm text-yellow-400">{expandedChannel.detail}</p>
                    )}

                    {expandedChannel.is_archived && (
                      <p className="text-sm text-wa-muted">
                        Canal arquivado — restaure-o pelo menu para voltar a utilizá-lo.
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
