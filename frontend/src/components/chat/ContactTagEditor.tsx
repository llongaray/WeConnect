import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Tag, X } from 'lucide-react'
import {
  assignTagToConversation,
  fetchTags,
  removeTagFromConversation,
} from '@/services/tags'
import type { Conversation } from '@/types'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

interface ContactTagEditorProps {
  conversation: Conversation
  onUpdated?: (conversation: Conversation) => void
}

export default function ContactTagEditor({ conversation, onUpdated }: ContactTagEditorProps) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: availableTags = [] } = useQuery({
    queryKey: ['tags', conversation.channel.company_id],
    queryFn: () => fetchTags(true),
    enabled: open,
  })

  const assignMutation = useMutation({
    mutationFn: (tagId: number) => assignTagToConversation(conversation.id, tagId),
    onSuccess: (data) => {
      onUpdated?.(data)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['conversation', conversation.id] })
      queryClient.invalidateQueries({ queryKey: ['tags/funnel'] })
    },
  })

  const removeMutation = useMutation({
    mutationFn: (tagId: number) => removeTagFromConversation(conversation.id, tagId),
    onSuccess: (data) => {
      onUpdated?.(data)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['conversation', conversation.id] })
      queryClient.invalidateQueries({ queryKey: ['tags/funnel'] })
    },
  })

  const currentTagIds = new Set((conversation.contact_tags || []).map((tag) => tag.id))
  const unassignedTags = availableTags.filter((tag) => !currentTagIds.has(tag.id))

  return (
    <div className="relative">
      <div className="flex flex-wrap items-center gap-1.5">
        {(conversation.contact_tags || []).map((tag) => (
          <Badge
            key={tag.id}
            variant="default"
            className="text-[10px] gap-1"
            style={{ borderColor: tag.color, color: tag.color }}
          >
            <Tag className="w-3 h-3" />
            {tag.name}
            <button
              type="button"
              onClick={() => removeMutation.mutate(tag.id)}
              className="hover:text-red-300"
              aria-label={`Remover tag ${tag.name}`}
            >
              <X className="w-3 h-3" />
            </button>
          </Badge>
        ))}
        <Button
          type="button"
          variant="secondary"
          className="px-2 py-0.5 text-[10px] h-6"
          onClick={() => setOpen((value) => !value)}
        >
          <Plus className="w-3 h-3 mr-1" />
          Tag
        </Button>
      </div>

      {open && (
        <div className="absolute z-20 mt-2 w-56 rounded-lg border border-wa-border bg-gray-900 shadow-xl p-2">
          {unassignedTags.length === 0 ? (
            <p className="text-xs text-wa-muted px-2 py-1">Nenhuma tag disponível.</p>
          ) : (
            unassignedTags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => assignMutation.mutate(tag.id)}
                className={cn(
                  'w-full text-left px-2 py-1.5 rounded text-xs hover:bg-gray-800 flex items-center gap-2',
                  assignMutation.isPending && 'opacity-60',
                )}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: tag.color }}
                />
                {tag.name}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
