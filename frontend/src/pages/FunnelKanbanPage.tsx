import { useQuery } from '@tanstack/react-query'
import { Columns3 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { fetchFunnelStages } from '@/services/tags'
import { getActiveCompanyId, needsPlatformCompanyScope } from '@/lib/companyContext'
import { useAuthStore } from '@/store/authStore'
import CompanyScopePrompt from '@/components/admin/CompanyScopePrompt'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonList } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'

export default function FunnelKanbanPage() {
  const companyId = getActiveCompanyId()
  const platformScope = needsPlatformCompanyScope()
  const showScopePrompt = platformScope && !companyId
  const isGestor = useAuthStore((s) => s.isGestor())
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const canManage = isGestor || isSuperUser

  const { data: stages = [], isLoading } = useQuery({
    queryKey: ['tags/funnel', companyId],
    queryFn: fetchFunnelStages,
    enabled: !showScopePrompt,
    refetchInterval: 30000,
  })

  if (showScopePrompt) {
    return (
      <CompanyScopePrompt
        title="Selecione uma empresa"
        description="Use o seletor de empresa no topo para visualizar o funil."
      />
    )
  }

  return (
    <div className="flex flex-col h-full min-h-0 p-4 md:p-6">
      <PageHeader
        title="Funil"
        description="Visualize os contatos por etapa do funil, no estilo CRM Kanban."
        actions={
          canManage ? (
            <Link to="/admin/funnel">
              <Button variant="secondary">Configurar etapas</Button>
            </Link>
          ) : undefined
        }
      />

      {isLoading && <SkeletonList count={4} />}

      {!isLoading && stages.length === 0 && (
        <EmptyState
          icon={Columns3}
          title="Funil vazio"
          description={
            canManage
              ? 'Configure as etapas do funil para começar a organizar seus contatos.'
              : 'Nenhuma etapa configurada pelo gestor ainda.'
          }
          className="py-16"
        />
      )}

      {!isLoading && stages.length > 0 && (
        <div className="flex-1 min-h-0 overflow-x-auto overflow-y-hidden pb-2">
          <div className="flex gap-4 h-full min-w-max px-1">
            {stages.map((stage) => (
              <section
                key={stage.tag.id}
                className="flex flex-col w-[300px] shrink-0 rounded-card border border-wa-border bg-wa-panel/80"
              >
                <header
                  className="px-4 py-3 border-b border-wa-border shrink-0"
                  style={{ borderTopColor: stage.tag.color, borderTopWidth: 3 }}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: stage.tag.color }}
                    />
                    <h3 className="font-semibold truncate">{stage.tag.name}</h3>
                  </div>
                  <p className="text-xs text-wa-muted mt-1">
                    Etapa {stage.tag.funnel_order} · {stage.contacts_count} contato(s)
                  </p>
                </header>

                <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-[320px] max-h-[calc(100vh-220px)]">
                  {stage.contacts.length === 0 ? (
                    <p className="text-xs text-wa-muted text-center py-8">
                      Nenhum contato nesta etapa.
                    </p>
                  ) : (
                    stage.contacts.map((contact) => (
                      <article
                        key={contact.contact_key}
                        className={cn(
                          'rounded-lg border border-wa-border/80 bg-gray-900/60 px-3 py-3',
                          'shadow-sm hover:border-wa-green/40 transition-colors',
                        )}
                      >
                        <p className="text-sm font-medium truncate">
                          {contact.name || contact.phone}
                        </p>
                        <p className="text-[11px] text-wa-muted truncate mt-0.5">
                          {contact.phone}
                        </p>
                        {contact.channel_name && (
                          <p className="text-[11px] text-wa-muted truncate mt-1">
                            {contact.channel_name}
                          </p>
                        )}
                        {contact.active_conversations > 0 && (
                          <Badge variant="info" className="text-[10px] mt-2">
                            {contact.active_conversations} conversa(s) ativa(s)
                          </Badge>
                        )}
                      </article>
                    ))
                  )}
                </div>
              </section>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
