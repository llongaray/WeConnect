import { useMemo, useState } from 'react'
import { MessageSquare, Search } from 'lucide-react'
import type { Channel, Conversation, ConversationCategory } from '@/types'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import { SkeletonList } from '@/components/ui/Skeleton'
import ChannelFilterDropdown from '@/components/chat/ChannelFilterDropdown'
import { formatRelativeTime } from '@/lib/formatRelativeTime'
import { cn } from '@/lib/cn'
import {
  channelPlatformBadgeVariant,
  conversationCategoryBadgeVariant,
  conversationCategoryLabels,
  getChannelPlatform,
  getChannelPlatformLabel,
  getChannelTypeIcon,
} from '@/lib/channelTypes'

interface Props {
  conversations: Conversation[]
  selectedId: number | null
  onSelect: (id: number) => void
  filter: ConversationCategory
  onFilterChange: (filter: ConversationCategory) => void
  isAdmin: boolean
  channels?: Channel[]
  channelFilter?: number[]
  onChannelFilterChange?: (ids: number[]) => void
  isLoading?: boolean
}

const CATEGORY_FILTERS: { key: ConversationCategory; label: string }[] = [
  { key: 'conversando', label: 'Conversando' },
  { key: 'aguardando', label: 'Aguardando' },
  { key: 'novo', label: 'Novo' },
  { key: 'finalizado', label: 'Finalizado' },
]

function resolveCategory(conv: Conversation): ConversationCategory {
  if (conv.category) return conv.category
  if (conv.status === 'closed') return 'finalizado'
  if (conv.status === 'open' && conv.assigned_to) return 'conversando'
  if (
    conv.status === 'open' &&
    !conv.assigned_to &&
    (conv.handoff_pending || conv.team)
  ) {
    return 'aguardando'
  }
  return 'novo'
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  filter,
  onFilterChange,
  isAdmin,
  channels = [],
  channelFilter = [],
  onChannelFilterChange,
  isLoading = false,
}: Props) {
  const [search, setSearch] = useState('')

  const filters = CATEGORY_FILTERS

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
          <ChannelFilterDropdown
            channels={channels}
            selectedIds={channelFilter}
            onChange={onChannelFilterChange}
          />
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
            const category = resolveCategory(conv)
            const ChannelIcon = conv.channel
              ? getChannelTypeIcon(conv.channel.channel_type)
              : null

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
                      <div className="flex gap-1 mt-1 flex-wrap items-center">
                        <Badge
                          variant={conversationCategoryBadgeVariant[category]}
                          className="text-[10px]"
                        >
                          {conversationCategoryLabels[category]}
                        </Badge>
                        <Badge variant="default" className="text-[10px] gap-1">
                          {ChannelIcon && <ChannelIcon className="w-3 h-3" />}
                          {conv.channel.name}
                        </Badge>
                        <Badge
                          variant={channelPlatformBadgeVariant[getChannelPlatform(conv.channel.channel_type)]}
                          className="text-[10px]"
                        >
                          {getChannelPlatformLabel(conv.channel.channel_type)}
                        </Badge>
                        {conv.team && (
                          <Badge variant="info" className="text-[10px]">{conv.team.name}</Badge>
                        )}
                      </div>
                    )}

                    {(conv.contact_tags?.length ?? 0) > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {conv.contact_tags!.slice(0, 2).map((tag) => (
                          <span
                            key={tag.id}
                            className="text-[10px] px-1.5 py-0.5 rounded-full border"
                            style={{ borderColor: tag.color, color: tag.color }}
                          >
                            {tag.name}
                          </span>
                        ))}
                        {(conv.contact_tags?.length ?? 0) > 2 && (
                          <span className="text-[10px] text-wa-muted">
                            +{(conv.contact_tags?.length ?? 0) - 2}
                          </span>
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
