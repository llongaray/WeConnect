import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Paperclip, Send } from 'lucide-react'
import { fetchPlatformOperators } from '@/services/platformChat'
import type { PlatformOperator } from '@/types'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

interface Props {
  onSend: (content: string) => Promise<void>
  onSendMedia: (file: File, caption: string) => Promise<void>
  onOpenDirect?: (username: string) => void
  isDirect?: boolean
  loading?: boolean
}

export default function PlatformChatComposer({
  onSend,
  onSendMedia,
  onOpenDirect,
  isDirect = false,
  loading = false,
}: Props) {
  const [text, setText] = useState('')
  const [mentionQuery, setMentionQuery] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: operators = [] } = useQuery({
    queryKey: ['platform-chat-operators'],
    queryFn: fetchPlatformOperators,
  })

  const suggestions = useMemo(() => {
    if (mentionQuery === null) return []
    const q = mentionQuery.toLowerCase()
    return operators.filter(
      (op) => op.username.toLowerCase().includes(q) || op.display_name.toLowerCase().includes(q),
    ).slice(0, 6)
  }, [mentionQuery, operators])

  const handleTextChange = (value: string) => {
    setText(value)
    const match = value.match(/@([a-zA-Z0-9_]*)$/)
    setMentionQuery(match ? match[1] : null)
  }

  const insertMention = (operator: PlatformOperator) => {
    const next = text.replace(/@([a-zA-Z0-9_]*)$/, `@${operator.username} `)
    setText(next)
    setMentionQuery(null)
  }

  const handleSubmit = async () => {
    const content = text.trim()
    if (!content || loading) return

    if (isDirect && onOpenDirect) {
      const dmMatch = content.match(/^@([a-zA-Z0-9_]+)$/)
      if (dmMatch) {
        onOpenDirect(dmMatch[1])
        setText('')
        return
      }
    }

    await onSend(content)
    setText('')
    setMentionQuery(null)
  }

  const handleFile = async (file: File | null) => {
    if (!file || loading) return
    await onSendMedia(file, text.trim())
    setText('')
    if (fileRef.current) fileRef.current.value = ''
  }

  return (
    <div className="border-t border-wa-border p-3 bg-wa-panel/60">
      {suggestions.length > 0 && (
        <div className="mb-2 rounded-lg border border-wa-border bg-wa-dark overflow-hidden">
          {suggestions.map((op) => (
            <button
              key={op.id}
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-wa-panel/80 transition-colors"
              onClick={() => insertMention(op)}
            >
              <span className="font-medium">{op.display_name}</span>
              <span className="text-wa-muted ml-2">@{op.username}</span>
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept="image/*,audio/*,.zip"
          onChange={(e) => void handleFile(e.target.files?.[0] || null)}
        />
        <button
          type="button"
          className="p-2 rounded-lg text-wa-muted hover:text-white hover:bg-wa-dark transition-colors shrink-0"
          onClick={() => fileRef.current?.click()}
          title="Anexar imagem, áudio ou ZIP (até 100 MB)"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        <textarea
          value={text}
          onChange={(e) => handleTextChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              void handleSubmit()
            }
          }}
          rows={2}
          placeholder={isDirect ? 'Mensagem privada... (@usuario para abrir DM)' : 'Mensagem... Use @usuario para marcar'}
          className={cn(
            'flex-1 resize-none px-3 py-2 rounded-lg text-sm',
            'bg-gray-800 border border-wa-border focus:border-wa-green focus:outline-none',
          )}
        />

        <Button
          type="button"
          className="px-3 py-2 shrink-0"
          loading={loading}
          disabled={!text.trim()}
          onClick={() => void handleSubmit()}
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
