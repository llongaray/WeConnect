import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchPlatformMessages,
  markPlatformRoomRead,
  sendPlatformMediaMessage,
  sendPlatformTextMessage,
} from '@/services/platformChat'
import type { PlatformRoom } from '@/types'
import PlatformChatComposer from '@/components/platform-chat/PlatformChatComposer'
import PlatformMessageBubble from '@/components/platform-chat/PlatformMessageBubble'
import { SkeletonList } from '@/components/ui/Skeleton'

interface Props {
  room: PlatformRoom
}

export default function PlatformChatMessages({ room }: Props) {
  const queryClient = useQueryClient()
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['platform-chat-messages', room.id],
    queryFn: () => fetchPlatformMessages(room.id),
    refetchInterval: 30000,
  })

  const messages = data?.results || []

  useEffect(() => {
    void markPlatformRoomRead(room.id).then(() => {
      queryClient.invalidateQueries({ queryKey: ['platform-chat-unread'] })
      queryClient.invalidateQueries({ queryKey: ['platform-chat-rooms'] })
    })
  }, [room.id, messages.length, queryClient])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const sendMutation = useMutation({
    mutationFn: (content: string) => sendPlatformTextMessage(room.id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platform-chat-messages', room.id] })
      queryClient.invalidateQueries({ queryKey: ['platform-chat-unread'] })
    },
  })

  const mediaMutation = useMutation({
    mutationFn: ({ file, caption }: { file: File; caption: string }) =>
      sendPlatformMediaMessage(room.id, file, caption),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platform-chat-messages', room.id] })
      queryClient.invalidateQueries({ queryKey: ['platform-chat-unread'] })
    },
  })

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {isLoading && <SkeletonList count={4} />}
        {!isLoading && messages.length === 0 && (
          <p className="text-sm text-wa-muted text-center py-8">
            Nenhuma mensagem ainda. Diga olá para a equipe!
          </p>
        )}
        {messages.map((message) => (
          <PlatformMessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>

      <PlatformChatComposer
        loading={sendMutation.isPending || mediaMutation.isPending}
        isDirect={room.kind === 'direct'}
        onSend={async (content) => {
          await sendMutation.mutateAsync(content)
        }}
        onSendMedia={async (file, caption) => {
          await mediaMutation.mutateAsync({ file, caption })
        }}
      />
    </div>
  )
}
