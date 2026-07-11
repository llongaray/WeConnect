import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useChatSocket() {
  const queryClient = useQueryClient()
  const accessToken = useAuthStore((s) => s.accessToken)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)

  const connect = useCallback(() => {
    if (!accessToken) return

    const ws = new WebSocket(`${WS_BASE}/ws/chat/?token=${accessToken}`)
    wsRef.current = ws

    ws.onopen = () => {
      retryRef.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.event === 'message.new') {
          queryClient.invalidateQueries({ queryKey: ['conversations'] })
          const convId = payload.data?.conversation_id
          if (convId) {
            queryClient.invalidateQueries({ queryKey: ['messages', convId] })
            queryClient.invalidateQueries({ queryKey: ['conversation', convId] })
          }
        }
        if (payload.event === 'conversation.updated') {
          queryClient.invalidateQueries({ queryKey: ['conversations'] })
          const convId = payload.data?.conversation_id
          if (convId) {
            queryClient.setQueryData(['conversation', convId], payload.data?.conversation)
          }
        }
        if (payload.event === 'qrcode.updated' || payload.event === 'connection.updated') {
          queryClient.invalidateQueries({ queryKey: ['channels'] })
          queryClient.invalidateQueries({ queryKey: ['channel-status'] })
        }
      } catch {
        // ignora payload inválido
      }
    }

    ws.onclose = () => {
      const delay = Math.min(1000 * 2 ** retryRef.current, 30000)
      retryRef.current += 1
      setTimeout(connect, delay)
    }
  }, [accessToken, queryClient])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])
}
