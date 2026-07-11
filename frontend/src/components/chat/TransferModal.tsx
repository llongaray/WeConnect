import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { fetchConversationTeamMembers } from '@/services/chat'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { cn } from '@/lib/cn'

interface Props {
  open: boolean
  onClose: () => void
  conversationId: number
  onConfirm: (userId: number, note: string) => void
  loading?: boolean
  currentUserId?: number
}

export default function TransferModal({
  open,
  onClose,
  conversationId,
  onConfirm,
  loading,
  currentUserId,
}: Props) {
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [note, setNote] = useState('')

  const { data: members = [], isLoading } = useQuery({
    queryKey: ['team-members', conversationId],
    queryFn: () => fetchConversationTeamMembers(conversationId),
    enabled: open && !!conversationId,
  })

  const filtered = members.filter((m) => {
    if (m.id === currentUserId) return false
    const q = search.toLowerCase()
    const name = `${m.first_name} ${m.last_name} ${m.username}`.toLowerCase()
    return name.includes(q)
  })

  const handleClose = () => {
    setSearch('')
    setSelectedId(null)
    setNote('')
    onClose()
  }

  return (
    <Modal open={open} onClose={handleClose} title="Transferir conversa">
      <Input
        placeholder="Buscar atendente..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        icon={<Search className="w-4 h-4" />}
        className="text-sm mb-3"
      />

      <div className="max-h-48 overflow-y-auto space-y-1 mb-3">
        {isLoading && <p className="text-sm text-wa-muted">Carregando...</p>}
        {!isLoading && filtered.length === 0 && (
          <p className="text-sm text-wa-muted">Nenhum membro encontrado na equipe.</p>
        )}
        {filtered.map((member) => (
          <button
            key={member.id}
            type="button"
            onClick={() => setSelectedId(member.id)}
            className={cn(
              'w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors',
              selectedId === member.id
                ? 'border-wa-green bg-wa-green/10'
                : 'border-wa-border hover:bg-gray-800',
            )}
          >
            <span className="font-medium">{member.first_name || member.username}</span>
            <span className="text-wa-muted text-xs ml-2">@{member.username}</span>
          </button>
        ))}
      </div>

      <Input
        placeholder="Observação (opcional)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        className="text-sm mb-4"
      />

      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={handleClose}>
          Cancelar
        </Button>
        <Button
          disabled={!selectedId}
          loading={loading}
          onClick={() => selectedId && onConfirm(selectedId, note)}
        >
          Transferir
        </Button>
      </div>
    </Modal>
  )
}
