import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  ArrowRightLeft,
  CheckCircle,
  LogOut,
  RotateCcw,
  UserCheck,
  UserMinus,
} from 'lucide-react'
import type { Conversation } from '@/types'
import {
  assumeConversation,
  closeConversation,
  releaseConversation,
  reopenConversation,
  transferConversation,
} from '@/services/chat'
import { useAuthStore } from '@/store/authStore'
import Button from '@/components/ui/Button'
import CloseConversationModal from './CloseConversationModal'
import TransferModal from './TransferModal'

interface Props {
  conversation: Conversation
  onUpdated?: (conversation: Conversation) => void
}

function extractError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (typeof detail === 'object' && detail) return String(Object.values(detail)[0])
  }
  return 'Não foi possível concluir a ação.'
}

export default function ConversationActions({ conversation, onUpdated }: Props) {
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = useAuthStore((s) => s.isAdmin())
  const isSupervisor = useAuthStore((s) => s.isSupervisor())
  const canTransfer = useAuthStore((s) => s.canTransfer())

  const [showTransfer, setShowTransfer] = useState(false)
  const [showClose, setShowClose] = useState(false)
  const [error, setError] = useState('')

  const invalidate = (conv: Conversation) => {
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
    queryClient.setQueryData(['conversation', conv.id], conv)
    onUpdated?.(conv)
  }

  const assumeMutation = useMutation({
    mutationFn: () => assumeConversation(conversation.id),
    onSuccess: (data) => {
      setError('')
      invalidate(data)
    },
    onError: (err) => setError(extractError(err)),
  })

  const releaseMutation = useMutation({
    mutationFn: () => releaseConversation(conversation.id),
    onSuccess: (data) => {
      setError('')
      invalidate(data)
    },
    onError: (err) => setError(extractError(err)),
  })

  const transferMutation = useMutation({
    mutationFn: ({ userId, note }: { userId: number; note: string }) =>
      transferConversation(conversation.id, userId, note),
    onSuccess: (data) => {
      setError('')
      setShowTransfer(false)
      invalidate(data)
    },
    onError: (err) => setError(extractError(err)),
  })

  const closeMutation = useMutation({
    mutationFn: (farewell: string) => closeConversation(conversation.id, farewell),
    onSuccess: (data) => {
      setError('')
      setShowClose(false)
      invalidate(data)
    },
    onError: (err) => setError(extractError(err)),
  })

  const reopenMutation = useMutation({
    mutationFn: () => reopenConversation(conversation.id),
    onSuccess: (data) => {
      setError('')
      invalidate(data)
    },
    onError: (err) => setError(extractError(err)),
  })

  const isOpen = conversation.status === 'open'
  const isAssignedToMe = conversation.assigned_to?.id === user?.id
  const isUnassigned = !conversation.assigned_to
  const canAssume = isOpen && (isUnassigned || (isAdmin && !isAssignedToMe))
  const canRelease = isOpen && (isAssignedToMe || isAdmin)
  const canClose = isOpen && (isAdmin || isSupervisor || isAssignedToMe)
  const canReopen = !isOpen && canTransfer

  return (
    <>
      <div className="flex items-center gap-1.5 flex-wrap">
        {canAssume && (
          <Button
            onClick={() => assumeMutation.mutate()}
            loading={assumeMutation.isPending}
            className="text-xs px-2 py-1"
            title="Assumir conversa"
          >
            <UserCheck className="w-3.5 h-3.5" />
            Assumir
          </Button>
        )}

        {isOpen && canTransfer && (
          <Button
            variant="secondary"
            onClick={() => setShowTransfer(true)}
            className="text-xs px-2 py-1"
            title="Transferir"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            Transferir
          </Button>
        )}

        {canRelease && conversation.assigned_to && (
          <Button
            variant="secondary"
            onClick={() => releaseMutation.mutate()}
            loading={releaseMutation.isPending}
            className="text-xs px-2 py-1"
            title="Devolver à fila"
          >
            <UserMinus className="w-3.5 h-3.5" />
            Fila
          </Button>
        )}

        {canClose && (
          <Button
            variant="secondary"
            onClick={() => setShowClose(true)}
            className="text-xs px-2 py-1"
            title="Encerrar"
          >
            <LogOut className="w-3.5 h-3.5" />
            Fechar
          </Button>
        )}

        {canReopen && (
          <Button
            onClick={() => reopenMutation.mutate()}
            loading={reopenMutation.isPending}
            className="text-xs px-2 py-1"
            title="Reabrir conversa"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reabrir
          </Button>
        )}

        {isAssignedToMe && isOpen && (
          <span title="Você está atendendo">
            <CheckCircle className="w-4 h-4 text-wa-green shrink-0" />
          </span>
        )}
      </div>

      {error && <p className="text-xs text-red-400 mt-2">{error}</p>}

      <TransferModal
        open={showTransfer}
        onClose={() => setShowTransfer(false)}
        conversationId={conversation.id}
        currentUserId={user?.id}
        loading={transferMutation.isPending}
        onConfirm={(userId, note) => transferMutation.mutate({ userId, note })}
      />

      <CloseConversationModal
        open={showClose}
        onClose={() => setShowClose(false)}
        contactName={conversation.contact.name || conversation.contact.phone}
        loading={closeMutation.isPending}
        onConfirm={(farewell) => closeMutation.mutate(farewell)}
      />
    </>
  )
}
