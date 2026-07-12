import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  CheckCircle2,
  Clock,
  KeyRound,
  Link2,
  Save,
  Server,
  Sparkles,
} from 'lucide-react'
import { fetchDeepSeekConfig, saveDeepSeekToken } from '@/services/deepseek'
import type { DeepSeekStatus } from '@/types'
import CompanyScopePrompt, { useRequiresCompanyScope } from '@/components/admin/CompanyScopePrompt'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'
import { getActiveCompanyId } from '@/lib/companyContext'

function statusBadge(status: DeepSeekStatus, pulse = false) {
  const map: Record<DeepSeekStatus, { label: string; variant: 'success' | 'default' | 'danger' }> = {
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

export default function DeepSeekPage() {
  const queryClient = useQueryClient()
  const [apiKey, setApiKey] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)
  const companyId = getActiveCompanyId()
  const showScopePrompt = useRequiresCompanyScope()
  const queriesEnabled = !showScopePrompt

  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['deepseek-config', companyId],
    queryFn: fetchDeepSeekConfig,
    enabled: queriesEnabled,
    retry: false,
  })

  const saveMutation = useMutation({
    mutationFn: () => saveDeepSeekToken(apiKey),
    onSuccess: () => {
      setSaveError('')
      setApiKey('')
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      queryClient.invalidateQueries({ queryKey: ['deepseek-config'] })
    },
    onError: (err: unknown) => {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data
        if (typeof data?.detail === 'string') {
          setSaveError(data.detail)
          queryClient.invalidateQueries({ queryKey: ['deepseek-config'] })
          return
        }
      }
      setSaveError('Erro ao salvar token. Tente novamente.')
    },
  })

  const lastValidated = config?.last_validated_at
    ? new Date(config.last_validated_at).toLocaleString('pt-BR')
    : null

  const configRows = [
    ['Base URL', config?.base_url ?? 'https://api.deepseek.com'],
    ['Modelo Chat', config?.chat_model ?? 'deepseek-chat'],
    ['Modelo Pensamento', config?.reasoner_model ?? 'deepseek-reasoner'],
    ['Endpoint Chat', config?.chat_endpoint ?? 'https://api.deepseek.com/v1/chat/completions'],
  ]

  if (showScopePrompt) {
    return (
      <CompanyScopePrompt
        title="Selecione uma empresa"
        description="Use o seletor de empresa no topo para configurar a integração DeepSeek."
      />
    )
  }

  return (
    <div className="h-full p-4 sm:p-6 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6">
        <PageHeader
          title="DeepSeek"
          description="Integre a IA DeepSeek informando apenas o token. URLs e modelos são gerenciados pelo sistema."
        />

        {isError && (
          <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-sm text-amber-200">
            API indisponível. Reinicie o backend e execute as migrations se necessário.
          </div>
        )}

        <Card
          padding="lg"
          className="border-wa-green/20 bg-gradient-to-br from-wa-panel to-wa-dark/60"
        >
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-wa-green/20 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-wa-green" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Status da conexão</h3>
                <p className="text-xs text-wa-muted">Validação automática via API DeepSeek</p>
              </div>
            </div>
            {isLoading ? (
              <Skeleton className="h-6 w-24 rounded-full" />
            ) : config ? (
              statusBadge(config.status, true)
            ) : (
              <Badge variant="default">Indisponível</Badge>
            )}
          </div>

          {!isLoading && config && (
            <div className="mt-4 pt-4 border-t border-wa-border/60 space-y-2 text-sm">
              {config.api_key_set && config.api_key_masked && (
                <p className="text-wa-muted">
                  Token: <span className="font-mono text-gray-300">{config.api_key_masked}</span>
                </p>
              )}
              {lastValidated && (
                <p className="text-xs text-wa-muted inline-flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  Última validação: {lastValidated}
                </p>
              )}
              {config.last_error && config.status === 'error' && (
                <p className="text-sm text-red-300">{config.last_error}</p>
              )}
              {config.status === 'connected' && (
                <p className="text-xs text-sky-300 inline-flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Pronto para uso no assistente de fluxos
                </p>
              )}
            </div>
          )}
        </Card>

        <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
          <Card padding="lg">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                <KeyRound className="w-4 h-4 text-wa-green" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">API Token</h3>
                <p className="text-[11px] text-wa-muted">Cole o token gerado no painel DeepSeek</p>
              </div>
            </div>

            {saveSuccess && (
              <div className="mb-4 p-3 rounded-lg bg-sky-900/30 border border-sky-700/50 text-xs text-sky-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                Token salvo e validado com sucesso.
              </div>
            )}

            <Input
              type="password"
              label="Token DeepSeek"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              autoComplete="off"
            />

            {saveError && (
              <p className="text-red-300 text-sm mt-3">{saveError}</p>
            )}

            <Button
              className="mt-4 w-full sm:w-auto"
              onClick={() => saveMutation.mutate()}
              loading={saveMutation.isPending}
              disabled={!apiKey.trim()}
            >
              <Save className="w-4 h-4" />
              Salvar e conectar
            </Button>
          </Card>

          <Card padding="lg" className="border-wa-border/80">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                <Server className="w-4 h-4 text-wa-green" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Configuração do sistema</h3>
                <p className="text-[11px] text-wa-muted">Parâmetros fixos — somente leitura</p>
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
      </div>
    </div>
  )
}
