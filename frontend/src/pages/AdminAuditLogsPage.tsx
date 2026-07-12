import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Building2,
  Clock,
  Filter,
  Globe,
  ScrollText,
  User,
  X,
} from 'lucide-react'
import { fetchAuditLogs, fetchCompanies } from '@/services/companies'
import type { AuditLog } from '@/types'
import Badge from '@/components/ui/Badge'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import Select from '@/components/ui/Select'
import Skeleton from '@/components/ui/Skeleton'

type EntityType = 'company' | 'user' | 'team' | ''

const entityLabels: Record<string, string> = {
  company: 'Empresa',
  user: 'Usuário',
  team: 'Equipe',
  channel: 'Canal',
  auth: 'Autenticação',
}

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'

function actionVariant(action: string): BadgeVariant {
  if (action.includes('delete')) return 'danger'
  if (action.includes('create') || action.includes('enabled') || action.includes('success')) return 'success'
  if (action.includes('failed') || action.includes('blocked')) return 'warning'
  return 'info'
}

function formatLogTime(iso: string) {
  const date = new Date(iso)
  return {
    date: date.toLocaleDateString('pt-BR'),
    time: date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  }
}

function AuditLogRow({ log }: { log: AuditLog }) {
  const { date, time } = formatLogTime(log.created_at)

  return (
    <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_auto] gap-3 md:gap-4 items-start md:items-center px-4 py-3 border-b border-wa-border/60 last:border-b-0 hover:bg-wa-dark/30 transition-colors">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <Badge variant={actionVariant(log.action)}>{log.action}</Badge>
          <Badge variant="default">{entityLabels[log.entity_type] || log.entity_type}</Badge>
        </div>
        <p className="text-sm text-white truncate">{log.entity_label || log.entity_id}</p>
      </div>

      <div className="text-xs text-wa-muted min-w-0">
        <span className="inline-flex items-center gap-1.5">
          <User className="w-3.5 h-3.5 shrink-0 text-wa-green/80" />
          {log.actor_name || 'Sistema'}
        </span>
      </div>

      <div className="text-xs text-wa-muted min-w-0">
        {log.ip_address && (
          <span className="inline-flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5 shrink-0" />
            {log.ip_address}
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

export default function AdminAuditLogsPage() {
  const [companyId, setCompanyId] = useState<number | ''>('')
  const [entityType, setEntityType] = useState<EntityType>('')

  const { data: companiesData } = useQuery({
    queryKey: ['companies'],
    queryFn: fetchCompanies,
  })

  const params = useMemo(() => {
    const base: { company_id?: number; entity_type?: EntityType } = {}
    if (companyId) base.company_id = companyId
    if (entityType) base.entity_type = entityType
    return base
  }, [companyId, entityType])

  const hasFilters = Boolean(companyId || entityType)

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => fetchAuditLogs(params),
  })

  const logs = data?.results || []
  const companies = companiesData?.results || []

  const clearFilters = () => {
    setCompanyId('')
    setEntityType('')
  }

  return (
    <div className="h-full p-4 sm:p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <PageHeader
          title="Auditoria da plataforma"
          description="Histórico de ações administrativas em empresas, usuários e equipes."
        />

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

          <div className="grid gap-3 sm:grid-cols-2">
            <Select
              label="Empresa"
              value={companyId}
              onChange={(e) => setCompanyId(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">Todas as empresas</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.trade_name} ({company.code})
                </option>
              ))}
            </Select>
            <Select
              label="Entidade"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as EntityType)}
            >
              <option value="">Todas as entidades</option>
              <option value="company">Empresas</option>
              <option value="user">Usuários</option>
              <option value="team">Equipes</option>
            </Select>
          </div>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-wa-border bg-wa-dark/40">
            <div className="flex items-center gap-2">
              <ScrollText className="w-4 h-4 text-wa-green" />
              <h3 className="text-sm font-semibold text-white">Registros</h3>
            </div>
            <Badge variant="info">{logs.length} registro(s)</Badge>
          </div>

          {!isLoading && logs.length > 0 && (
            <div className="hidden md:grid grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_auto] gap-4 px-4 py-2 border-b border-wa-border/60 text-[10px] font-semibold uppercase tracking-wider text-wa-muted">
              <span>Ação / entidade</span>
              <span>Responsável</span>
              <span>IP</span>
              <span className="text-right">Data / hora</span>
            </div>
          )}

          {isLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={ScrollText}
                title="Nenhum registro encontrado"
                description={
                  hasFilters
                    ? 'Nenhum evento corresponde aos filtros aplicados.'
                    : 'Os eventos de auditoria aparecerão aqui conforme ações forem realizadas.'
                }
              />
            </div>
          ) : (
            <div>
              {logs.map((log) => (
                <AuditLogRow key={log.id} log={log} />
              ))}
            </div>
          )}
        </Card>

        <p className="text-[11px] text-wa-muted text-center flex items-center justify-center gap-3 flex-wrap pb-2">
          <span className="inline-flex items-center gap-1">
            <Building2 className="w-3 h-3" />
            Filtre por empresa para ver ações de um tenant
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Horários no fuso local
          </span>
        </p>
      </div>
    </div>
  )
}
