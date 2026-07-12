import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  CheckCircle2,
  Clock,
  ExternalLink,
  KeyRound,
  Link2,
  Save,
  Server,
  Sparkles,
  Star,
  Trash2,
} from 'lucide-react'
import {
  disconnectAIProvider,
  fetchAIProviders,
  saveAIProviderToken,
  setDefaultAIProvider,
} from '@/services/aiProviders'
import type { AIProviderConfig, AIProviderStatus, AIProviderType } from '@/types'
import { AI_PROVIDER_CATALOG, getAIProviderMeta } from '@/lib/aiProviderTypes'
import { getActiveCompanyId } from '@/lib/companyContext'
import CompanyScopePrompt, { useRequiresCompanyScope } from '@/components/admin/CompanyScopePrompt'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'

function statusBadge(status: AIProviderStatus, pulse = false) {
  const map: Record<AIProviderStatus, { label: string; variant: 'success' | 'default' | 'danger' }> = {
    connected: { label: 'Conectado', variant: 'success' },
    disconnected: { label: 'Desconectado', variant: 'default' },
    error: { label: 'Erro', variant: 'danger' },
  }
  const { label, variant } = map[status]
  return (
    <Badge variant={variant} pulse={pulse && status === 'connected'}>
      {label}
    </Badge>
  )
}

export default function AIProvidersPage() {
  const queryClient = useQueryClient()
  const companyId = getActiveCompanyId()
  const showScopePrompt = useRequiresCompanyScope()
  const queriesEnabled = !showScopePrompt

  const [selectedType, setSelectedType] = useState<AIProviderType | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  const { data: providers = [], isLoading, isError } = useQuery({
    queryKey: ['ai-providers', companyId],
    queryFn: fetchAIProviders,
    enabled: queriesEnabled,
    retry: false,
  })

  const providerMap = useMemo(() => {
    const map = new Map<AIProviderType, AIProviderConfig>()
    providers.forEach((item) => map.set(item.provider_type, item))
    return map
  }, [providers])

  const selectedProvider = selectedType ? providerMap.get(selectedType) : null
  const selectedMeta = selectedType ? getAIProviderMeta(selectedType) : null

  const saveMutation = useMutation({
    mutationFn: () => saveAIProviderToken(selectedType!, apiKey, true),
    onSuccess: () => {
      setSaveError('')
      setApiKey('')
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
    },
    onError: (err: unknown) => {
      if (axios.isAxiosError(err) && typeof err.response?.data?.detail === 'string') {
        setSaveError(err.response.data.detail)
        queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
        return
      }
      setSaveError('Erro ao salvar token. Tente novamente.')
    },
  })

  const defaultMutation = useMutation({
    mutationFn: (type: AIProviderType) => setDefaultAIProvider(type),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai-providers'] }),
  })

  const disconnectMutation = useMutation({
    mutationFn: (type: AIProviderType) => disconnectAIProvider(type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
      if (selectedType) setApiKey('')
    },
  })

  if (showScopePrompt) {
    return (
      <CompanyScopePrompt
        title="Selecione uma empresa"
        description="Use o seletor de empresa no topo para configurar os canais de IA."
      />
    )
  }

  const configRows = selectedProvider
    ? [
        ['Base URL', selectedProvider.base_url],
        ['Modelo principal', selectedProvider.chat_model],
        ['Modelo avançado', selectedProvider.reasoner_model],
        ['Endpoint', selectedProvider.chat_endpoint],
      ]
    : []

  return (
    <div className="h-full p-4 sm:p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <PageHeader
          title="Inteligência Artificial"
          description="Adicione e configure canais de IA por provedor. Cada canal usa seu próprio token e pode ser definido como padrão para automações."
        />

        {isError && (
          <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-sm text-amber-200">
            API indisponível. Reinicie o backend e execute as migrations se necessário.
          </div>
        )}

        {isLoading && (
          <div className="grid gap-4 md:grid-cols-2">
            {AI_PROVIDER_CATALOG.map((item) => (
              <Skeleton key={item.type} className="h-36 rounded-card" />
            ))}
          </div>
        )}

        {!isLoading && providers.length === 0 && (
          <EmptyState
            icon={Sparkles}
            title="Nenhum canal de IA"
            description="Os canais disponíveis aparecerão aqui para configuração."
          />
        )}

        {!isLoading && (
          <div className="grid gap-4 md:grid-cols-2">
            {AI_PROVIDER_CATALOG.map((meta) => {
              const config = providerMap.get(meta.type)
              const Icon = meta.icon
              const isSelected = selectedType === meta.type
              return (
                <button
                  key={meta.type}
                  type="button"
                  onClick={() => {
                    setSelectedType(meta.type)
                    setApiKey('')
                    setSaveError('')
                  }}
                  className={cn(
                    'text-left rounded-card border p-4 transition-all',
                    isSelected
                      ? 'border-wa-green shadow-glow-green/20 bg-wa-panel'
                      : 'border-wa-border bg-wa-panel/70 hover:border-gray-600',
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="w-11 h-11 rounded-xl bg-gray-800 border border-wa-border flex items-center justify-center shrink-0">
                        <Icon className={cn('w-5 h-5', meta.accentClass)} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold">{meta.label}</h3>
                          {config?.is_default && (
                            <Badge variant="info" className="text-[10px]">Padrão</Badge>
                          )}
                        </div>
                        <p className="text-xs text-wa-muted mt-1 line-clamp-2">{meta.description}</p>
                      </div>
                    </div>
                    {config ? statusBadge(config.status, true) : <Badge variant="default">Novo</Badge>}
                  </div>
                  {config?.api_key_masked && (
                    <p className="text-[11px] text-wa-muted mt-3 font-mono">{config.api_key_masked}</p>
                  )}
                </button>
              )
            })}
          </div>
        )}

        {selectedType && selectedMeta && (
          <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
            <Card padding="lg">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                    <KeyRound className="w-4 h-4 text-wa-green" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">Configurar {selectedMeta.label}</h3>
                    <a
                      href={selectedMeta.docsUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] text-wa-green hover:underline inline-flex items-center gap-1"
                    >
                      Obter token
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
                {selectedProvider && statusBadge(selectedProvider.status)}
              </div>

              {saveSuccess && (
                <div className="mb-4 p-3 rounded-lg bg-sky-900/30 border border-sky-700/50 text-xs text-sky-300 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  Token salvo e validado com sucesso.
                </div>
              )}

              <Input
                type="password"
                label={selectedMeta.tokenLabel}
                placeholder={selectedMeta.tokenPlaceholder}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                autoComplete="off"
              />

              {saveError && <p className="text-red-300 text-sm mt-3">{saveError}</p>}

              <div className="flex flex-wrap gap-2 mt-4">
                <Button
                  onClick={() => saveMutation.mutate()}
                  loading={saveMutation.isPending}
                  disabled={!apiKey.trim()}
                >
                  <Save className="w-4 h-4" />
                  Salvar e conectar
                </Button>
                {selectedProvider?.status === 'connected' && !selectedProvider.is_default && (
                  <Button
                    variant="secondary"
                    onClick={() => defaultMutation.mutate(selectedType)}
                    loading={defaultMutation.isPending}
                  >
                    <Star className="w-4 h-4" />
                    Definir como padrão
                  </Button>
                )}
                {selectedProvider?.api_key_set && (
                  <Button
                    variant="secondary"
                    className="text-red-300"
                    onClick={() => disconnectMutation.mutate(selectedType)}
                    loading={disconnectMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4" />
                    Desconectar
                  </Button>
                )}
              </div>

              {selectedProvider?.last_validated_at && (
                <p className="text-xs text-wa-muted mt-4 inline-flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  Última validação:{' '}
                  {new Date(selectedProvider.last_validated_at).toLocaleString('pt-BR')}
                </p>
              )}
              {selectedProvider?.last_error && selectedProvider.status === 'error' && (
                <p className="text-sm text-red-300 mt-2">{selectedProvider.last_error}</p>
              )}
            </Card>

            <Card padding="lg" className="border-wa-border/80">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                  <Server className="w-4 h-4 text-wa-green" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Parâmetros do sistema</h3>
                  <p className="text-[11px] text-wa-muted">Somente leitura — gerenciados pelo backend</p>
                </div>
              </div>

              <dl className="space-y-3">
                {configRows.map(([label, value]) => (
                  <div
                    key={label}
                    className="rounded-lg bg-wa-dark/40 border border-wa-border/50 px-3 py-2.5"
                  >
                    <dt className="text-[10px] font-semibold uppercase tracking-wider text-wa-muted mb-1">
                      {label}
                    </dt>
                    <dd className="font-mono text-xs text-gray-300 break-all inline-flex items-start gap-1.5">
                      <Link2 className="w-3 h-3 shrink-0 mt-0.5 opacity-60" />
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
