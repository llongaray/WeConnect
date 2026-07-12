import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Clock,
  Filter,
  Globe,
  Radio,
  ShieldAlert,
  Unlock,
  User,
  X,
} from 'lucide-react'
import { fetchSecurityEvents, unlockIp, type SecurityEvent } from '@/services/security'
import { confirmDialog } from '@/lib/confirmDialog'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Select from '@/components/ui/Select'
import Skeleton from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'

const eventLabels: Record<string, string> = {
  login_failed: 'Falha de login',
  login_blocked: 'Login bloqueado',
  webhook_rejected: 'Webhook rejeitado',
  rate_limit_hit: 'Rate limit',
  totp_failed: 'Falha 2FA',
  totp_success: '2FA validado',
  ip_unlocked: 'IP desbloqueado',
  idor_blocked: 'IDOR bloqueado',
}

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'

function eventVariant(type: string): BadgeVariant {
  if (['totp_success', 'ip_unlocked'].includes(type)) return 'success'
  if (['login_failed', 'totp_failed', 'rate_limit_hit'].includes(type)) return 'warning'
  if (['login_blocked', 'idor_blocked', 'webhook_rejected'].includes(type)) return 'danger'
  return 'info'
}

function formatEventTime(iso: string) {
  const date = new Date(iso)
  return {
    date: date.toLocaleDateString('pt-BR'),
    time: date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  }
}

function EventRow({ event }: { event: SecurityEvent }) {
  const { date, time } = formatEventTime(event.created_at)

  return (
    <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_minmax(0,0.8fr)_auto] gap-3 md:gap-4 items-start md:items-center px-4 py-3 border-b border-wa-border/60 last:border-b-0 hover:bg-wa-dark/30 transition-colors">
      <div className="min-w-0">
        <Badge variant={eventVariant(event.event_type)} className="mb-1.5">
          {eventLabels[event.event_type] || event.event_type}
        </Badge>
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <p className="text-[11px] text-wa-muted truncate font-mono">
            {JSON.stringify(event.metadata)}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1 text-xs text-wa-muted min-w-0">
        {event.ip_address && (
          <span className="inline-flex items-center gap-1.5 truncate">
            <Globe className="w-3.5 h-3.5 shrink-0 text-wa-green/80" />
            {event.ip_address}
          </span>
        )}
        {event.username && (
          <span className="inline-flex items-center gap-1.5 truncate">
            <User className="w-3.5 h-3.5 shrink-0 text-wa-green/80" />
            {event.username}
          </span>
        )}
      </div>

      <div className="text-xs text-wa-muted min-w-0">
        {event.channel_id != null && (
          <span className="inline-flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 shrink-0" />
            Canal #{event.channel_id}
          </span>
        )}
      </div>

      <div className="text-right shrink-0">
        <p className="text-xs text-white">{time}</p>
        <p className="text-[11px] text-wa-muted">{date}</p>
      </div>
    </div>
  )
}

export default function AdminSecurityPage() {
  const queryClient = useQueryClient()
  const [eventType, setEventType] = useState('')
  const [ipFilter, setIpFilter] = useState('')
  const [usernameFilter, setUsernameFilter] = useState('')
  const [unlockIpValue, setUnlockIpValue] = useState('')
  const [unlockUserValue, setUnlockUserValue] = useState('')
  const [unlockSuccess, setUnlockSuccess] = useState(false)

  const params = useMemo(() => {
    const base: Record<string, string> = {}
    if (eventType) base.event_type = eventType
    if (ipFilter) base.ip_address = ipFilter
    if (usernameFilter) base.username = usernameFilter
    return base
  }, [eventType, ipFilter, usernameFilter])

  const hasFilters = Boolean(eventType || ipFilter || usernameFilter)

  const { data, isLoading } = useQuery({
    queryKey: ['security-events', params],
    queryFn: () => fetchSecurityEvents(params),
  })

  const unlockMutation = useMutation({
    mutationFn: unlockIp,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-events'] })
      setUnlockIpValue('')
      setUnlockUserValue('')
      setUnlockSuccess(true)
      setTimeout(() => setUnlockSuccess(false), 3000)
    },
  })

  const events = data?.results || []

  const handleUnlock = async () => {
    if (!unlockIpValue && !unlockUserValue) return
    const target = unlockIpValue
      ? `IP ${unlockIpValue}`
      : `usuário ${unlockUserValue}`
    const ok = await confirmDialog({
      title: 'Desbloquear acesso',
      message: `Confirmar desbloqueio do ${target}?`,
      confirmLabel: 'Desbloquear',
      variant: 'danger',
    })
    if (!ok) return
    unlockMutation.mutate({
      ip_address: unlockIpValue || undefined,
      username: unlockUserValue || undefined,
    })
  }

  const clearFilters = () => {
    setEventType('')
    setIpFilter('')
    setUsernameFilter('')
  }

  return (
    <div className="h-full p-4 sm:p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <PageHeader
          title="Segurança"
          description="Monitore eventos críticos e desbloqueie IPs ou usuários bloqueados."
        />

        <div className="grid gap-6 lg:grid-cols-3 lg:items-start">
          <Card padding="lg" className="lg:col-span-1 border-wa-green/20">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                <Unlock className="w-4 h-4 text-wa-green" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Desbloquear acesso</h3>
                <p className="text-[11px] text-wa-muted">Informe IP ou usuário bloqueado</p>
              </div>
            </div>

            {unlockSuccess && (
              <div className="mb-4 p-3 rounded-lg bg-sky-900/30 border border-sky-700/50 text-xs text-sky-300">
                Desbloqueio realizado com sucesso.
              </div>
            )}

            <div className="space-y-3">
              <Input
                label="Endereço IP"
                value={unlockIpValue}
                onChange={(e) => setUnlockIpValue(e.target.value)}
                placeholder="192.168.1.1"
              />
              <Input
                label="Usuário"
                value={unlockUserValue}
                onChange={(e) => setUnlockUserValue(e.target.value)}
                placeholder="admin"
              />
              <p className="text-[11px] text-wa-muted">
                Preencha pelo menos um dos campos acima.
              </p>
              <Button
                onClick={() => void handleUnlock()}
                loading={unlockMutation.isPending}
                disabled={!unlockIpValue && !unlockUserValue}
                className="w-full"
              >
                <Unlock className="w-4 h-4" />
                Desbloquear
              </Button>
            </div>
          </Card>

          <div className="lg:col-span-2 space-y-4">
            <Card padding="md" className="border-wa-border/80">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="w-4 h-4 text-wa-muted" />
                <h3 className="text-sm font-semibold text-white">Filtros</h3>
                {hasFilters && (
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="ml-auto inline-flex items-center gap-1 text-xs text-wa-muted hover:text-white transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                    Limpar
                  </button>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <Select
                  label="Tipo de evento"
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                >
                  <option value="">Todos os eventos</option>
                  {Object.entries(eventLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </Select>
                <Input
                  label="Filtrar IP"
                  value={ipFilter}
                  onChange={(e) => setIpFilter(e.target.value)}
                  placeholder="172.18.0.1"
                />
                <Input
                  label="Filtrar usuário"
                  value={usernameFilter}
                  onChange={(e) => setUsernameFilter(e.target.value)}
                  placeholder="admin"
                />
              </div>
            </Card>

            <Card className="overflow-hidden p-0">
              <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-wa-border bg-wa-dark/40">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-wa-green" />
                  <h3 className="text-sm font-semibold text-white">Eventos recentes</h3>
                </div>
                <Badge variant="info">{events.length} evento(s)</Badge>
              </div>

              {!isLoading && events.length > 0 && (
                <div className="hidden md:grid grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_minmax(0,0.8fr)_auto] gap-4 px-4 py-2 border-b border-wa-border/60 text-[10px] font-semibold uppercase tracking-wider text-wa-muted">
                  <span>Evento</span>
                  <span>Origem</span>
                  <span>Canal</span>
                  <span className="text-right">Data / hora</span>
                </div>
              )}

              {isLoading ? (
                <div className="p-4 space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-14 w-full" />
                  ))}
                </div>
              ) : events.length === 0 ? (
                <div className="p-6">
                  <EmptyState
                    icon={ShieldAlert}
                    title="Nenhum evento encontrado"
                    description={
                      hasFilters
                        ? 'Nenhum evento corresponde aos filtros aplicados.'
                        : 'Eventos de segurança aparecerão aqui conforme ocorrerem.'
                    }
                  />
                </div>
              ) : (
                <div className={cn('divide-y divide-wa-border/40')}>
                  {events.map((event) => (
                    <EventRow key={event.id} event={event} />
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>

        <p className="text-[11px] text-wa-muted text-center flex items-center justify-center gap-1.5 pb-2">
          <Clock className="w-3 h-3" />
          Horários exibidos no fuso local do navegador
        </p>
      </div>
    </div>
  )
}
