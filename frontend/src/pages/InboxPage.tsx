import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchConversation, fetchConversations } from '@/services/chat'
import { fetchChannels } from '@/services/channels'
import { useAuthStore } from '@/store/authStore'
import type { Conversation } from '@/types'
import ConversationList from '@/components/chat/ConversationList'
import ChatPanel from '@/components/chat/ChatPanel'
import { cn } from '@/lib/cn'

type MobileView = 'list' | 'chat'

export default function InboxPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [filter, setFilter] = useState('open')
  const [channelFilter, setChannelFilter] = useState<number | ''>('')
  const [mobileView, setMobileView] = useState<MobileView>('list')
  const [selectedOverride, setSelectedOverride] = useState<Conversation | null>(null)
  const isAdmin = useAuthStore((s) => s.isAdmin())

  const { data: channelsData } = useQuery({
    queryKey: ['channels'],
    queryFn: fetchChannels,
    enabled: isAdmin,
  })

  const listFilter = filter === 'open' ? undefined : filter

  const { data, isLoading } = useQuery({
    queryKey: ['conversations', filter, channelFilter],
    queryFn: () =>
      fetchConversations({
        filter: listFilter,
        channelId: channelFilter ? Number(channelFilter) : undefined,
        status:
          filter === 'closed' ? 'closed' : filter === 'open' ? 'open' : undefined,
      }),
    refetchInterval: 15000,
  })

  const { data: selectedFromApi } = useQuery({
    queryKey: ['conversation', selectedId],
    queryFn: () => fetchConversation(selectedId!),
    enabled: !!selectedId,
  })

  const conversations = data?.results || []
  const selected =
    selectedOverride?.id === selectedId
      ? selectedOverride
      : selectedFromApi || conversations.find((c) => c.id === selectedId) || null
  const channels = channelsData || []

  const handleSelect = (id: number) => {
    setSelectedId(id)
    setSelectedOverride(null)
    setMobileView('chat')
  }

  const handleConversationUpdated = (conv: Conversation) => {
    setSelectedOverride(conv)
  }

  return (
    <div className="flex h-full w-full min-h-0">
      <div
        className={cn(
          'w-full lg:w-80 shrink-0 h-full',
          mobileView === 'chat' ? 'hidden lg:block' : 'block',
        )}
      >
        <ConversationList
          conversations={conversations}
          selectedId={selectedId}
          onSelect={handleSelect}
          filter={filter}
          onFilterChange={setFilter}
          isAdmin={isAdmin}
          channels={channels}
          channelFilter={channelFilter}
          onChannelFilterChange={setChannelFilter}
          isLoading={isLoading}
        />
      </div>

      <div
        className={cn(
          'flex-1 h-full min-w-0 w-full flex flex-col',
          mobileView === 'list' ? 'hidden lg:flex' : 'flex',
        )}
      >
        <ChatPanel
          conversation={selected}
          onBack={() => setMobileView('list')}
          onConversationUpdated={handleConversationUpdated}
        />
      </div>
    </div>
  )
}
