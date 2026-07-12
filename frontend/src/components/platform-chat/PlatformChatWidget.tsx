import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare } from 'lucide-react'
import { fetchPlatformUnread } from '@/services/platformChat'
import { usePlatformChatEnabled, usePlatformChatSocket } from '@/hooks/usePlatformChatSocket'
import PlatformChatPanel from '@/components/platform-chat/PlatformChatPanel'
import { cn } from '@/lib/cn'

export default function PlatformChatWidget() {
  const enabled = usePlatformChatEnabled()
  const [open, setOpen] = useState(false)

  usePlatformChatSocket(enabled)

  const { data: unread } = useQuery({
    queryKey: ['platform-chat-unread'],
    queryFn: fetchPlatformUnread,
    enabled,
    refetchInterval: 30000,
  })

  if (!enabled) return null

  const badgeCount = unread?.total || 0
  const mentionCount = unread?.unread_mentions || 0

  return (
    <>
      {open && (
        <div
          className="fixed bottom-24 right-6 z-50 w-[min(420px,calc(100vw-2rem))] h-[min(70vh,640px)] animate-slide-up"
          role="dialog"
          aria-label="Chat interno WeConnect"
        >
          <PlatformChatPanel onClose={() => setOpen(false)} />
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={cn(
          'fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-panel',
          'bg-wa-green text-white flex items-center justify-center',
          'hover:scale-105 active:scale-95 transition-transform',
          open && 'ring-2 ring-wa-green/40',
        )}
        title="Chat da equipe WeConnect"
        aria-label="Abrir chat da equipe WeConnect"
      >
        <MessageSquare className="w-6 h-6" />
        {badgeCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[20px] h-5 px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">
            {badgeCount > 99 ? '99+' : badgeCount}
          </span>
        )}
        {mentionCount > 0 && (
          <span className="absolute -top-1 -left-1 w-3 h-3 rounded-full bg-amber-400 border-2 border-wa-dark" title="Menções urgentes" />
        )}
      </button>
    </>
  )
}
