import { Building2 } from 'lucide-react'
import { needsPlatformCompanyScope } from '@/lib/companyContext'
import { useAuthStore } from '@/store/authStore'
import EmptyState from '@/components/ui/EmptyState'

interface CompanyScopePromptProps {
  title?: string
  description?: string
  className?: string
}

export function useRequiresCompanyScope(): boolean {
  const hasCompanyScope = useAuthStore((s) => s.hasCompanyScope())
  const platformScopeRequired = needsPlatformCompanyScope()
  return platformScopeRequired && !hasCompanyScope
}

export default function CompanyScopePrompt({
  title = 'Selecione uma empresa',
  description = 'Use o seletor de empresa no topo para visualizar e gerenciar os dados desta área.',
  className = 'flex h-full items-center justify-center p-6',
}: CompanyScopePromptProps) {
  const showPrompt = useRequiresCompanyScope()

  if (!showPrompt) return null

  return (
    <div className={className}>
      <EmptyState
        icon={Building2}
        title={title}
        description={description}
        className="max-w-md"
      />
    </div>
  )
}
