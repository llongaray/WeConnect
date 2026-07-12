import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, MessageCircle, Phone, Search, Trash2, Users, X } from 'lucide-react'
import { eraseContactData, exportContactData, fetchContacts } from '@/services/chat'
import { useAuthStore } from '@/store/authStore'
import CompanyScopePrompt, { useRequiresCompanyScope } from '@/components/admin/CompanyScopePrompt'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'
import { getActiveCompanyId } from '@/lib/companyContext'

export default function ContactsPage() {
  const [search, setSearch] = useState('')
  const canManage = useAuthStore((s) => s.hasCapability('manage_lgpd'))
  const queryClient = useQueryClient()
  const companyId = getActiveCompanyId()
  const showScopePrompt = useRequiresCompanyScope()
  const queriesEnabled = !showScopePrompt

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', companyId, search],
    queryFn: () => fetchContacts(search || undefined),
    enabled: queriesEnabled,
  })

  const exportMutation = useMutation({
    mutationFn: exportContactData,
    onSuccess: (payload, contactId) => {
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `contato-${contactId}-lgpd.json`
      link.click()
      URL.revokeObjectURL(url)
    },
  })

  const eraseMutation = useMutation({
    mutationFn: eraseContactData,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contacts'] }),
  })

  if (showScopePrompt) {
    return (
      <CompanyScopePrompt
        title="Selecione uma empresa"
        description="Use o seletor de empresa no topo para visualizar os contatos."
      />
    )
  }

  const contacts = data?.results || []

  return (
    <div className="h-full p-4 sm:p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <PageHeader
          title="Contatos"
          description="Contatos sincronizados automaticamente via WhatsApp."
        />

        <Card padding="md" className="border-wa-border/80">
          <div className="flex flex-col sm:flex-row sm:items-end gap-3">
            <div className="flex-1 min-w-0">
              <Input
                label="Buscar contato"
                placeholder="Nome ou telefone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Search className="w-4 h-4" />}
              />
            </div>
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="inline-flex items-center gap-1 text-xs text-wa-muted hover:text-white transition-colors pb-2 sm:pb-2.5"
              >
                <X className="w-3.5 h-3.5" />
                Limpar busca
              </button>
            )}
          </div>
        </Card>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-wa-green" />
            <h3 className="text-sm font-semibold text-white">Lista de contatos</h3>
          </div>
          {!isLoading && <Badge variant="info">{contacts.length} contato(s)</Badge>}
        </div>

        {isLoading && (
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-card" />
            ))}
          </div>
        )}

        {!isLoading && contacts.length === 0 && (
          <Card padding="lg" className="border-dashed border-wa-border/80">
            <EmptyState
              icon={Users}
              title={search ? 'Nenhum contato encontrado' : 'Nenhum contato ainda'}
              description={
                search
                  ? 'Tente outro termo de busca ou limpe o filtro.'
                  : 'Os contatos aparecem automaticamente quando alguém envia mensagem pelo WhatsApp.'
              }
              action={
                !search ? (
                  <div className="flex items-center gap-2 text-xs text-wa-muted mt-2">
                    <MessageCircle className="w-4 h-4 text-wa-green" />
                    Acesse o Chat para iniciar conversas
                  </div>
                ) : undefined
              }
            />
          </Card>
        )}

        {!isLoading && contacts.length > 0 && (
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {contacts.map((contact, index) => (
              <Card
                key={contact.id}
                hover
                padding="md"
                className="animate-fade-in border-wa-border/80"
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <div className="flex items-center gap-3">
                  <Avatar name={contact.name || contact.phone} />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium truncate text-white">
                      {contact.name || 'Sem nome'}
                    </p>
                    <p className="text-sm text-wa-muted inline-flex items-center gap-1 truncate">
                      <Phone className="w-3 h-3 shrink-0" />
                      {contact.phone}
                    </p>
                  </div>
                </div>
                {contact.external_id && (
                  <p className="text-[11px] text-wa-muted mt-3 pt-3 border-t border-wa-border/50 truncate font-mono">
                    ID: {contact.external_id}
                  </p>
                )}
                {canManage && (
                  <div className="flex gap-2 mt-3 pt-3 border-t border-wa-border/50">
                    <button
                      type="button"
                      onClick={() => exportMutation.mutate(contact.id)}
                      className="inline-flex items-center gap-1 text-xs text-wa-green hover:underline"
                    >
                      <Download className="w-3 h-3" />
                      Exportar (LGPD)
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm('Excluir permanentemente os dados deste contato?')) {
                          eraseMutation.mutate(contact.id)
                        }
                      }}
                      className="inline-flex items-center gap-1 text-xs text-red-400 hover:underline"
                    >
                      <Trash2 className="w-3 h-3" />
                      Excluir
                    </button>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
