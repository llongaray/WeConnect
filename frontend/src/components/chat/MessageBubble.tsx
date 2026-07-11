import type { Message } from '@/types'
import { cn } from '@/lib/cn'

interface Props {
  message: Message
  index?: number
}

export default function MessageBubble({ message, index = 0 }: Props) {
  const isOut = message.direction === 'out'
  const mediaSrc = message.media_file || message.media_url

  return (
    <div
      className={cn(
        'flex mb-2 animate-slide-up',
        isOut ? 'justify-end' : 'justify-start',
      )}
      style={{ animationDelay: `${Math.min(index * 30, 150)}ms` }}
    >
      <div
        className={cn(
          'max-w-[70%] px-3 py-2 text-sm shadow-sm',
          isOut
            ? 'bg-wa-bubble text-white rounded-2xl rounded-br-md'
            : 'bg-wa-bubbleIn text-gray-100 rounded-2xl rounded-bl-md',
        )}
      >
        {message.message_type === 'text' && (
          <>
            {isOut && message.sent_by && (
              <p className="font-semibold text-sm mb-1 whitespace-pre-wrap break-words">
                {message.sent_by.first_name || message.sent_by.username}
              </p>
            )}
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </>
        )}

        {message.message_type === 'image' && mediaSrc && (
          <img src={mediaSrc} alt="Imagem" className="max-w-full rounded-lg mb-1" />
        )}

        {(message.message_type === 'audio' || message.message_type === 'video') && mediaSrc && (
          <audio controls src={mediaSrc} className="max-w-full" />
        )}

        {message.message_type === 'document' && mediaSrc && (
          <a href={mediaSrc} target="_blank" rel="noreferrer" className="underline text-wa-green">
            {message.content || 'Documento'}
          </a>
        )}

        {message.message_type !== 'text' && message.content && (
          <p className="text-xs mt-1 opacity-80">{message.content}</p>
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
