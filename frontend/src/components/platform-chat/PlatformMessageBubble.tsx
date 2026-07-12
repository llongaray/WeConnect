import type { PlatformMessage } from '@/types'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/cn'

interface Props {
  message: PlatformMessage
}

function renderContentWithMentions(content: string, mentioned: string[]) {
  if (!content) return null
  const parts = content.split(/(@[a-zA-Z0-9_]+)/g)
  return parts.map((part, index) => {
    if (part.startsWith('@')) {
      const username = part.slice(1)
      const isMention = mentioned.includes(username)
      return (
        <span
          key={`${part}-${index}`}
          className={cn(
            'font-semibold',
            isMention ? 'text-amber-300' : 'text-wa-green',
          )}
        >
          {part}
        </span>
      )
    }
    return <span key={`${part}-${index}`}>{part}</span>
  })
}

export default function PlatformMessageBubble({ message }: Props) {
  const currentUserId = useAuthStore((s) => s.user?.id)
  const isMine = message.sender.id === currentUserId
  const mediaSrc = message.media_file

  return (
    <div className={cn('flex mb-2', isMine ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[85%] px-3 py-2 text-sm shadow-sm rounded-2xl',
          isMine
            ? 'bg-wa-bubble text-white rounded-br-md'
            : 'bg-wa-bubbleIn text-gray-100 rounded-bl-md',
        )}
      >
        {!isMine && (
          <p className="text-xs font-semibold text-wa-green mb-1">
            {message.sender.first_name || message.sender.username}
            <span className="text-wa-muted font-normal ml-1">@{message.sender.username}</span>
          </p>
        )}

        {message.message_type === 'text' && (
          <p className="whitespace-pre-wrap break-words">
            {renderContentWithMentions(message.content, message.mentioned_usernames)}
          </p>
        )}

        {message.message_type === 'image' && mediaSrc && (
          <img src={mediaSrc} alt="Imagem" className="max-w-full rounded-lg mb-1" />
        )}

        {message.message_type === 'audio' && mediaSrc && (
          <audio controls src={mediaSrc} className="max-w-full" />
        )}

        {message.message_type === 'file' && mediaSrc && (
          <a href={mediaSrc} target="_blank" rel="noreferrer" className="underline text-wa-green break-all">
            {message.content || 'Arquivo ZIP'}
          </a>
        )}

        {message.message_type !== 'text' && message.content && (
          <p className="text-xs mt-1 opacity-80 whitespace-pre-wrap break-words">
            {renderContentWithMentions(message.content, message.mentioned_usernames)}
          </p>
        )}

        <div className="text-[10px] text-right mt-1 opacity-60">
          {new Date(message.created_at).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  )
}
