import { useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import type { Channel, Conversation } from '@/types'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import { SkeletonList } from '@/components/ui/Skeleton'
import { formatRelativeTime } from '@/lib/formatRelativeTime'
import { cn } from '@/lib/cn'
import { MessageSquare } from 'lucide-react'

interface Props {
  conversations: Conversation[]
  selectedId: number | null
  onSelect: (id: number) => void
  filter: string
  onFilterChange: (filter: string) => void
  isAdmin: boolean
  channels?: Channel[]
  channelFilter?: number | ''
  onChannelFilterChange?: (id: number | '') => void
  isLoading?: boolean
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  filter,
  onFilterChange,
  isAdmin,
  channels = [],
  channelFilter = '',
  onChannelFilterChange,
  isLoading = false,
}: Props) {
  const [search, setSearch] = useState('')

  const filters = [
    { key: 'open', label: 'Abertas' },
    { key: 'mine', label: 'Minhas' },
    { key: 'unassigned', label: 'Fila' },
    { key: 'handoff', label: 'Aguardando' },
    { key: 'closed', label: 'Fechadas' },
    ...(isAdmin ? [{ key: 'all', label: 'Todas' }] : []),
  ]

  const filteredConversations = useMemo(() => {
    if (!search.trim()) return conversations
    const q = search.toLowerCase()
    return conversations.filter(
      (c) =>
        (c.contact.name || '').toLowerCase().includes(q) ||
        c.contact.phone.includes(q),
    )
  }, [conversations, search])

  return (
    <div className="flex flex-col h-full bg-wa-panel border-r border-wa-border">
      <div className="p-3 border-b border-wa-border space-y-3">
        <h2 className="font-semibold text-title">Conversas</h2>

        <Input
          placeholder="Buscar conversa..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search className="w-4 h-4" />}
          className="text-xs"
        />

        {isAdmin && channels.length > 0 && onChannelFilterChange && (
          <select
            value={channelFilter}
            onChange={(e) =>
              onChannelFilterChange(e.target.value ? Number(e.target.value) : '')
            }
            className="w-full px-2 py-1.5 text-xs bg-gray-800 border border-wa-border rounded-lg focus:outline-none focus:border-wa-green"
          >
            <option value="">Todos os canais</option>
            {channels.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.name}
              </option>
            ))}
          </select>
        )}

        <div className="flex gap-1 flex-wrap">
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => onFilterChange(f.key)}
              className={cn(
                'px-2.5 py-1 text-xs rounded-full transition-all duration-200',
                filter === f.key
                  ? 'bg-wa-green text-white shadow-glow-green/30'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600',
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && <SkeletonList count={6} />}

        {!isLoading && filteredConversations.length === 0 && (
          <EmptyState
            icon={MessageSquare}
            title="Nenhuma conversa"
            description={
              search
                ? 'Nenhum resultado para sua busca.'
                : 'As conversas aparecerão aqui quando chegarem mensagens.'
            }
            className="py-12"
          />
        )}

        {!isLoading &&
          filteredConversations.map((conv, index) => {
            const displayName = conv.contact.name || conv.contact.phone
            return (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={cn(
                  'w-full text-left p-3 border-b border-wa-border/50 transition-all duration-200',
                  'hover:bg-gray-800/50 animate-fade-in',
                  selectedId === conv.id && 'bg-gray-800/80 border-l-2 border-l-wa-green',
                )}
                style={{ animationDelay: `${index * 40}ms` }}
              >
                <div className="flex gap-3 items-start">
                  <Avatar name={displayName} size="sm" />
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between items-start gap-2">
                      <span className="font-medium truncate text-sm">{displayName}</span>
                      {conv.unread_count > 0 && (
                        <Badge variant="unread" pulse className="shrink-0 min-w-[20px] justify-center">
                          {conv.unread_count}
                        </Badge>
                      )}
                    </div>

                    {conv.channel && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        <Badge variant="default" className="text-[10px]">
                          {conv.channel.name}
                        </Badge>
                        {conv.status === 'closed' && (
                          <Badge variant="default" className="text-[10px]">Fechada</Badge>
                        )}
                        {conv.handoff_pending && conv.status === 'open' && (
                          <Badge variant="warning" className="text-[10px]">Aguardando</Badge>
                        )}
                        {conv.team && (
                          <Badge variant="info" className="text-[10px]">{conv.team.name}</Badge>
                        )}
                      </div>
                    )}

                    <p className="text-xs text-wa-muted truncate mt-1">
                      {conv.last_message_preview || 'Sem mensagens'}
                    </p>

                    <div className="flex justify-between items-center mt-1">
                      {conv.assigned_to && (
                        <p className="text-[10px] text-gray-500 truncate">
                          {conv.assigned_to.first_name || conv.assigned_to.username}
                        </p>
                      )}
                      {conv.last_message_at && (
                        <span className="text-[10px] text-wa-muted ml-auto">
                          {formatRelativeTime(conv.last_message_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
      </div>
    </div>
  )
}
