import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, MessageSquare, Paperclip, Send } from 'lucide-react'
import type { Conversation } from '@/types'
import {
  assumeConversation,
  fetchMessages,
  markConversationRead,
  sendMediaMessage,
  sendTextMessage,
} from '@/services/chat'
import { useAuthStore } from '@/store/authStore'
import MessageBubble from './MessageBubble'
import ConversationActions from './ConversationActions'
import ConversationTimeline from './ConversationTimeline'
import ContactTagEditor from './ContactTagEditor'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import EmptyState from '@/components/ui/EmptyState'
import Modal from '@/components/ui/Modal'
import { SkeletonList } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'
import {
  conversationCategoryBadgeVariant,
  conversationCategoryLabels,
  getChannelTypeIcon,
} from '@/lib/channelTypes'

interface Props {
  conversation: Conversation | null
  onBack?: () => void
  onConversationUpdated?: (conversation: Conversation) => void
}

export default function ChatPanel({ conversation, onBack, onConversationUpdated }: Props) {
  const [text, setText] = useState('')
  const [showAssumePrompt, setShowAssumePrompt] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = useAuthStore((s) => s.isAdmin())
  const isSupervisor = useAuthStore((s) => s.isSupervisor())

  const { data: messagesData, isLoading } = useQuery({
    queryKey: ['messages', conversation?.id],
    queryFn: () => fetchMessages(conversation!.id),
    enabled: !!conversation,
    refetchInterval: 10000,
  })

  const messages = [...(messagesData?.results || [])].reverse()

  useEffect(() => {
    if (conversation?.id && conversation.unread_count > 0) {
      markConversationRead(conversation.id).then(() => {
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
      })
    }
  }, [conversation?.id, conversation?.unread_count, queryClient])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const sendMutation = useMutation({
    mutationFn: (content: string) => sendTextMessage(conversation!.id, content),
    onSuccess: () => {
      setText('')
      queryClient.invalidateQueries({ queryKey: ['messages', conversation?.id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const mediaMutation = useMutation({
    mutationFn: ({ file, type }: { file: File; type: string }) =>
      sendMediaMessage(conversation!.id, file, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', conversation?.id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const assumeMutation = useMutation({
    mutationFn: () => assumeConversation(conversation!.id),
    onSuccess: (data) => {
      setShowAssumePrompt(false)
      onConversationUpdated?.(data)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  if (!conversation) {
    return (
      <div className="flex-1 w-full min-w-0 flex items-center justify-center bg-wa-chat chat-bg-pattern">
        <EmptyState
          icon={MessageSquare}
          title="Selecione uma conversa"
          description="Escolha uma conversa na lista ao lado para começar o atendimento."
        />
      </div>
    )
  }

  const displayName = conversation.contact.name || conversation.contact.phone
  const isOpen = conversation.status === 'open'
  const isAssignedToMe = conversation.assigned_to?.id === user?.id
  const category = conversation.category
    || (conversation.status === 'closed'
      ? 'finalizado'
      : conversation.status === 'open' && conversation.assigned_to
        ? 'conversando'
        : conversation.status === 'open' && !conversation.assigned_to && (conversation.handoff_pending || conversation.team)
          ? 'aguardando'
          : 'novo')
  const ChannelIcon = conversation.channel
    ? getChannelTypeIcon(conversation.channel.channel_type)
    : null

  const canSend =
    isOpen &&
    (isAdmin ||
      isSupervisor ||
      isAssignedToMe)

  const needsAssume =
    isOpen &&
    !isAdmin &&
    !isSupervisor &&
    !conversation.assigned_to

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    if (needsAssume) {
      setShowAssumePrompt(true)
      return
    }
    if (!canSend) return
    sendMutation.mutate(text.trim())
  }

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (needsAssume) {
      setShowAssumePrompt(true)
      return
    }
    if (!canSend) return
    const type = file.type.startsWith('image/')
      ? 'image'
      : file.type.startsWith('audio/')
        ? 'audio'
        : file.type.startsWith('video/')
          ? 'video'
          : 'document'
    mediaMutation.mutate({ file, type })
    e.target.value = ''
  }

  const statusBadge = () => {
    if (!isOpen) return <Badge variant="default">Fechada</Badge>
    if (conversation.handoff_pending && !conversation.assigned_to) {
      return <Badge variant="warning">Aguardando humano</Badge>
    }
    if (conversation.assigned_to) {
      return (
        <Badge variant="info">
          {conversation.assigned_to.first_name || conversation.assigned_to.username}
        </Badge>
      )
    }
    return <Badge variant="success">Na fila</Badge>
  }

  return (
    <div className="flex flex-col h-full w-full min-w-0 flex-1 bg-wa-chat">
      <header className="px-4 py-3 bg-wa-panel border-b border-wa-border shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          {onBack && (
            <button
              onClick={onBack}
              className="lg:hidden p-1.5 rounded-lg hover:bg-wa-dark transition-colors shrink-0"
              aria-label="Voltar"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <Avatar name={displayName} size="sm" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 min-w-0">
              {ChannelIcon && <ChannelIcon className="w-4 h-4 text-wa-green shrink-0" />}
              <h3 className="font-semibold truncate">{displayName}</h3>
            </div>
            <p className="text-xs text-wa-muted truncate">
              {conversation.contact.phone}
              {conversation.channel && ` · ${conversation.channel.name}`}
              {conversation.team && ` · ${conversation.team.name}`}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <Badge variant={conversationCategoryBadgeVariant[category]} className="text-[10px]">
              {conversationCategoryLabels[category]}
            </Badge>
            {statusBadge()}
          </div>
        </div>
        <div className="mt-2">
          <ContactTagEditor
            conversation={conversation}
            onUpdated={onConversationUpdated}
          />
        </div>
        <div className="mt-2 pt-2 border-t border-wa-border/60">
          <ConversationActions
            conversation={conversation}
            onUpdated={onConversationUpdated}
          />
        </div>
      </header>

      {conversation.recent_events && conversation.recent_events.length > 0 && (
        <ConversationTimeline events={conversation.recent_events} />
      )}

      <div className="flex-1 overflow-y-auto p-4 chat-bg-pattern">
        {isLoading && <SkeletonList count={4} />}
        {!isLoading &&
          messages.map((msg, index) => (
            <MessageBubble key={msg.id} message={msg} index={index} />
          ))}
        <div ref={bottomRef} />
      </div>

      {isOpen ? (
        <form
          onSubmit={handleSend}
          className="p-3 bg-wa-panel border-t border-wa-border flex gap-2 shrink-0"
        >
          <input
            ref={fileRef}
            type="file"
            className="hidden"
            onChange={handleFile}
            accept="image/*,audio/*,video/*,.pdf,.doc,.docx"
          />
          <Button
            type="button"
            variant="secondary"
            onClick={() => fileRef.current?.click()}
            disabled={!canSend && !needsAssume}
            className="px-3"
            title="Anexar mídia"
          >
            <Paperclip className="w-4 h-4" />
          </Button>
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={
              needsAssume
                ? 'Assuma a conversa para responder'
                : canSend
                  ? 'Digite uma mensagem...'
                  : 'Sem permissão para enviar'
            }
            disabled={!canSend && !needsAssume}
            className={cn(
              'flex-1 bg-gray-800 border border-wa-border rounded-lg px-3 py-2 text-sm',
              'focus:outline-none focus:border-wa-green focus:ring-1 focus:ring-wa-green/30',
              'transition-all duration-200 disabled:opacity-50',
            )}
          />
          <Button
            type="submit"
            disabled={(!canSend && !needsAssume) || sendMutation.isPending || !text.trim()}
            loading={sendMutation.isPending}
            className="px-4"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      ) : (
        <div className="p-3 bg-wa-panel border-t border-wa-border text-center text-sm text-wa-muted shrink-0">
          Conversa encerrada. Histórico somente leitura.
        </div>
      )}

      <Modal
        open={showAssumePrompt}
        onClose={() => setShowAssumePrompt(false)}
        title="Assumir conversa"
      >
        <p className="text-sm text-wa-muted mb-4">
          Você precisa assumir esta conversa antes de enviar mensagens.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setShowAssumePrompt(false)}>
            Cancelar
          </Button>
          <Button
            onClick={() => assumeMutation.mutate()}
            loading={assumeMutation.isPending}
          >
            Assumir agora
          </Button>
        </div>
      </Modal>
    </div>
  )
}
