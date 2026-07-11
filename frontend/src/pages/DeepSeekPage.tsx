import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { KeyRound, Save, Sparkles } from 'lucide-react'
import { fetchDeepSeekConfig, saveDeepSeekToken } from '@/services/deepseek'
import type { DeepSeekStatus } from '@/types'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'

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

  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['deepseek-config'],
    queryFn: fetchDeepSeekConfig,
    retry: false,
  })

  const saveMutation = useMutation({
    mutationFn: () => saveDeepSeekToken(apiKey),
    onSuccess: () => {
      setSaveError('')
      setApiKey('')
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

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="DeepSeek"
        description="Configure o token da API. URLs e modelos são definidos automaticamente pelo sistema."
      />

      {isError && (
        <p className="text-yellow-400 text-sm mb-4">
          API indisponível. Reinicie o backend e execute: python manage.py migrate
        </p>
      )}

      <div className="grid gap-6 max-w-2xl">
        <Card padding="lg" className="border-wa-green/20">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-wa-green/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-wa-green" />
              </div>
              <div>
                <h3 className="font-semibold">Status da conexão</h3>
                <p className="text-xs text-wa-muted">Validação via API DeepSeek</p>
              </div>
            </div>
            {!isLoading && config && statusBadge(config.status, true)}
            {isLoading && <Badge variant="default">Carregando...</Badge>}
          </div>

          {config?.api_key_set && config.api_key_masked && (
            <p className="text-sm text-wa-muted mb-2">
              Token atual: <span className="font-mono text-gray-300">{config.api_key_masked}</span>
            </p>
          )}
          {lastValidated && (
            <p className="text-xs text-wa-muted">Última validação: {lastValidated}</p>
          )}
          {config?.last_error && config.status === 'error' && (
            <p className="text-sm text-red-400 mt-2">{config.last_error}</p>
          )}
        </Card>

        <Card padding="lg">
          <h3 className="font-medium mb-4">Configuração fixa do sistema</h3>
          <dl className="grid gap-3 text-sm">
            {[
              ['Base URL', config?.base_url ?? 'https://api.deepseek.com'],
              ['Modelo Chat', config?.chat_model ?? 'deepseek-chat'],
              ['Modelo Pensamento', config?.reasoner_model ?? 'deepseek-reasoner'],
              ['Endpoint Chat', config?.chat_endpoint ?? 'https://api.deepseek.com/v1/chat/completions'],
            ].map(([label, value]) => (
              <div key={label} className="flex flex-col sm:flex-row sm:gap-4">
                <dt className="text-wa-muted shrink-0 sm:w-36">{label}</dt>
                <dd className="font-mono text-xs text-gray-300 break-all">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4">
            <KeyRound className="w-5 h-5 text-wa-green" />
            <h3 className="font-medium">API Token</h3>
          </div>

          <Input
            type="password"
            label="Token DeepSeek"
            placeholder="sk-..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            autoComplete="off"
          />

          {saveError && (
            <p className="text-red-400 text-sm mt-3">{saveError}</p>
          )}

          <Button
            className="mt-4"
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
            disabled={!apiKey.trim()}
          >
            <Save className="w-4 h-4" />
            Salvar e conectar
          </Button>
        </Card>
      </div>
    </div>
  )
}
