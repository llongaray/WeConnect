import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2 } from 'lucide-react'
import { fetchCompanies } from '@/services/companies'
import { useAuthStore } from '@/store/authStore'
import Select from '@/components/ui/Select'
import { cn } from '@/lib/cn'

interface CompanyScopeBarProps {
  compact?: boolean
  variant?: 'default' | 'compact' | 'header'
}

function clearTenantQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.removeQueries({ queryKey: ['conversations'] })
  queryClient.removeQueries({ queryKey: ['conversation'] })
  queryClient.removeQueries({ queryKey: ['channels'] })
  queryClient.removeQueries({ queryKey: ['contacts'] })
  queryClient.removeQueries({ queryKey: ['teams'] })
  queryClient.removeQueries({ queryKey: ['bot-flows'] })
  queryClient.removeQueries({ queryKey: ['ai-providers'] })
  queryClient.removeQueries({ queryKey: ['deepseek-config'] })
  queryClient.removeQueries({ queryKey: ['users'] })
  queryClient.removeQueries({ queryKey: ['company'] })
}

export default function CompanyScopeBar({
  compact = false,
  variant = compact ? 'compact' : 'default',
}: CompanyScopeBarProps) {
  const queryClient = useQueryClient()
  const canSelectCompany = useAuthStore((s) => s.hasCapability('manage_companies'))
  const requiresTotpSetup = useAuthStore((s) => s.requiresTotpSetup)
  const selectedCompanyId = useAuthStore((s) => s.selectedCompanyId)
  const setSelectedCompanyId = useAuthStore((s) => s.setSelectedCompanyId)
  const userCompany = useAuthStore((s) => s.user?.company)

  const handleCompanyChange = (value: string) => {
    const companyId = value ? Number(value) : null
    setSelectedCompanyId(companyId)
    clearTenantQueries(queryClient)
  }

  const { data } = useQuery({
    queryKey: ['companies'],
    queryFn: fetchCompanies,
    enabled: canSelectCompany && !requiresTotpSetup,
  })

  if (!canSelectCompany) {
    if (!userCompany) return null
    if (variant === 'header') {
      return (
        <div className="hidden sm:flex items-center gap-1.5 min-w-0 max-w-[200px] lg:max-w-xs text-xs text-wa-muted">
          <Building2 className="w-3.5 h-3.5 text-wa-green shrink-0" />
          <span className="truncate">
            {userCompany.trade_name}
            <span className="font-mono text-[10px] ml-1 opacity-80">({userCompany.code})</span>
          </span>
        </div>
      )
    }
    return (
      <div className={`flex items-center gap-2 text-sm text-wa-muted ${variant === 'compact' ? '' : 'mb-6'}`}>
        <Building2 className="w-4 h-4 text-wa-green shrink-0" />
        <span className="truncate">
          Empresa: <strong className="text-white">{userCompany.trade_name}</strong>{' '}
          <span className="font-mono text-xs">({userCompany.code})</span>
        </span>
      </div>
    )
  }

  const companies = data?.results || []

  if (variant === 'header') {
    return (
      <div className="flex items-center gap-1.5 min-w-0 max-w-[180px] sm:max-w-[220px] lg:max-w-xs">
        <Building2 className="w-3.5 h-3.5 text-wa-green shrink-0 hidden sm:block" />
        <select
          value={selectedCompanyId ?? ''}
          onChange={(e) => handleCompanyChange(e.target.value)}
          className="min-w-0 flex-1 max-w-full py-1 px-2 text-xs h-8 bg-gray-800 border border-wa-border rounded-lg focus:outline-none focus:border-wa-green"
          title={
            !selectedCompanyId
              ? 'Selecione uma empresa para gerenciar colaboradores, equipes e canais'
              : undefined
          }
        >
          <option value="">Empresa...</option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.trade_name} ({company.code})
            </option>
          ))}
        </select>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'rounded-lg border border-wa-border bg-wa-dark/40 p-3',
        variant === 'compact' ? '' : 'mb-6',
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <Building2 className="w-4 h-4 text-wa-green shrink-0" />
        <span className="text-sm text-wa-muted">Empresa ativa:</span>
        <Select
          value={selectedCompanyId ?? ''}
          onChange={(e) => handleCompanyChange(e.target.value)}
          className="min-w-[220px] flex-1"
        >
          <option value="">Selecione uma empresa...</option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.trade_name} ({company.code})
            </option>
          ))}
        </Select>
      </div>
      {!selectedCompanyId && (
        <p className="text-xs text-amber-300/90 mt-2">
          Selecione uma empresa para gerenciar colaboradores, equipes, canais e integrações.
        </p>
      )}
    </div>
  )
}
