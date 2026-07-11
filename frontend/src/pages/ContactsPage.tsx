import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Users } from 'lucide-react'
import { fetchContacts } from '@/services/chat'
import Avatar from '@/components/ui/Avatar'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonList } from '@/components/ui/Skeleton'

export default function ContactsPage() {
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => fetchContacts(search || undefined),
  })

  const contacts = data?.results || []

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Contatos"
        description="Todos os contatos sincronizados via WhatsApp."
      />

      <Input
        placeholder="Buscar por nome ou telefone..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        icon={<Search className="w-4 h-4" />}
        className="max-w-md mb-6"
      />

      {isLoading && <SkeletonList count={6} />}

      {!isLoading && contacts.length === 0 && (
        <EmptyState
          icon={Users}
          title="Nenhum contato encontrado"
          description={
            search
              ? 'Tente outro termo de busca.'
              : 'Os contatos aparecerão quando receberem mensagens.'
          }
        />
      )}

      <div className="grid gap-3 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {contacts.map((contact, index) => (
          <Card
            key={contact.id}
            hover
            className="animate-fade-in"
            style={{ animationDelay: `${index * 40}ms` }}
          >
            <div className="flex items-center gap-3">
              <Avatar name={contact.name || contact.phone} />
              <div className="min-w-0 flex-1">
                <p className="font-medium truncate">{contact.name || 'Sem nome'}</p>
                <p className="text-sm text-wa-muted">{contact.phone}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2 truncate">{contact.external_id}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
