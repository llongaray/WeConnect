import type { ConversationEvent } from '@/types'
import { formatRelativeTime } from '@/lib/formatRelativeTime'

const EVENT_LABELS: Record<ConversationEvent['event_type'], string> = {
  assumed: 'assumiu a conversa',
  transferred: 'transferiu',
  released: 'devolveu à fila',
  closed: 'encerrou',
  reopened: 'reabriu',
}

interface Props {
  events: ConversationEvent[]
}

export default function ConversationTimeline({ events }: Props) {
  if (!events.length) return null

  return (
    <div className="px-4 py-2 bg-wa-panel/50 border-b border-wa-border">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-wa-muted mb-2">
        Histórico
      </p>
      <div className="space-y-1 max-h-24 overflow-y-auto">
        {events.map((ev) => (
          <p key={ev.id} className="text-xs text-wa-muted">
            <span className="text-gray-300">
              {ev.actor?.first_name || ev.actor?.username || 'Sistema'}
            </span>{' '}
            {EVENT_LABELS[ev.event_type]}
            {ev.to_user && (
              <>
                {' '}
                para{' '}
                <span className="text-gray-300">
                  {ev.to_user.first_name || ev.to_user.username}
                </span>
              </>
            )}
            <span className="ml-2 opacity-60">{formatRelativeTime(ev.created_at)}</span>
          </p>
        ))}
      </div>
    </div>
  )
}
