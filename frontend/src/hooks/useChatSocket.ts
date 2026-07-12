import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getActiveCompanyId } from '@/lib/companyContext'
import { useAuthStore } from '@/store/authStore'

function resolveWsBase(): string {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
}

export function useChatSocket() {
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isPlatformScoped = useAuthStore((s) => s.isSuperUser || s.isWeconnectSupport)
  const selectedCompanyId = useAuthStore((s) => s.selectedCompanyId)
  const requiresTotpSetup = useAuthStore((s) => s.requiresTotpSetup)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const authenticatedRef = useRef(false)

  const connect = useCallback(() => {
    if (!user || requiresTotpSetup) return

    const companyId = getActiveCompanyId()
    if (isPlatformScoped && !companyId) return

    authenticatedRef.current = false
    const query = companyId ? `?company_id=${companyId}` : ''
    const ws = new WebSocket(`${resolveWsBase()}/ws/chat/${query}`)
    wsRef.current = ws

    ws.onopen = () => {
      if (isPlatformScoped && companyId) {
        ws.send(JSON.stringify({ type: 'auth', company_id: companyId }))
      }
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)

        if (payload.event === 'auth.ok') {
          authenticatedRef.current = true
          retryRef.current = 0
          return
        }

        if (!authenticatedRef.current) {
          return
        }

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
      authenticatedRef.current = false
      const delay = Math.min(1000 * 2 ** retryRef.current, 30000)
      retryRef.current += 1
      setTimeout(connect, delay)
    }
  }, [user, isPlatformScoped, selectedCompanyId, requiresTotpSetup, queryClient])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])
}
