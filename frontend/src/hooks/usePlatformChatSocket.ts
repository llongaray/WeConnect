import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'

function resolveWsBase(): string {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
}

export function usePlatformChatSocket(enabled: boolean) {
  const queryClient = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const authenticatedRef = useRef(false)

  const connect = useCallback(() => {
    if (!enabled) return

    authenticatedRef.current = false
    const ws = new WebSocket(`${resolveWsBase()}/ws/platform-chat/`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)

        if (payload.event === 'auth.ok') {
          authenticatedRef.current = true
          retryRef.current = 0
          return
        }

        if (!authenticatedRef.current) return

        if (
          payload.event === 'message.new'
          || payload.event === 'mention.new'
          || payload.event === 'read.updated'
        ) {
          queryClient.invalidateQueries({ queryKey: ['platform-chat-rooms'] })
          queryClient.invalidateQueries({ queryKey: ['platform-chat-unread'] })
          const roomId = payload.data?.room ?? payload.data?.room_id ?? payload.data?.message?.room
          if (roomId) {
            queryClient.invalidateQueries({ queryKey: ['platform-chat-messages', roomId] })
          }
        }
      } catch {
        // ignora payload inválido
      }
    }

    ws.onclose = () => {
      authenticatedRef.current = false
      const delay = Math.min(1000 * 2 ** retryRef.current, 30000)
      retryRef.current += 1
      setTimeout(connect, delay)
    }
  }, [enabled, queryClient])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])
}

export function usePlatformChatEnabled() {
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const isWeconnectSupport = useAuthStore((s) => s.isWeconnectSupport)
  const requiresTotpSetup = useAuthStore((s) => s.requiresTotpSetup)
  const user = useAuthStore((s) => s.user)
  return Boolean(user && (isSuperUser || isWeconnectSupport) && !requiresTotpSetup)
}
