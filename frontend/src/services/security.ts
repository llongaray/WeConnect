import api from '@/services/api'
import type { PaginatedResponse } from '@/types'

export interface SecurityEvent {
  id: number
  event_type: string
  ip_address: string | null
  username: string
  channel_id: number | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface SecurityEventQueryParams {
  event_type?: string
  ip_address?: string
  username?: string
}

export async function fetchSecurityEvents(params?: SecurityEventQueryParams) {
  const { data } = await api.get<PaginatedResponse<SecurityEvent> | SecurityEvent[]>(
    '/security-events/',
    { params },
  )
  if (Array.isArray(data)) {
    return { results: data, count: data.length }
  }
  return data
}

export async function unlockIp(payload: { ip_address?: string; username?: string }) {
  await api.post('/security-events/unlock-ip/', payload)
}
