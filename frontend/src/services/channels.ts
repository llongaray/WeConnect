import api from './api'
import { getCompanyQueryParams } from '@/lib/companyContext'
import type { Channel, CreateChannelPayload, PaginatedResponse } from '@/types'

export async function fetchChannels(options?: {
  companyId?: number | null
  includeInactive?: boolean
  includeArchived?: boolean
}) {
  const params: Record<string, string | number> = {}
  if (options?.companyId) {
    params.company_id = options.companyId
  } else {
    Object.assign(params, getCompanyQueryParams())
  }
  if (options?.includeInactive) params.include_inactive = 'true'
  if (options?.includeArchived) params.include_archived = 'true'

  const { data } = await api.get<PaginatedResponse<Channel> | Channel[]>('/channels/', { params })
  if (Array.isArray(data)) return data
  return data.results ?? []
}

export async function deactivateChannel(id: number) {
  const { data } = await api.post<Channel>(`/channels/${id}/deactivate/`)
  return data
}

export async function archiveChannel(id: number) {
  const { data } = await api.post<Channel>(`/channels/${id}/archive/`)
  return data
}

export async function restoreChannel(id: number, reactivate = true) {
  const { data } = await api.post<Channel>(`/channels/${id}/restore/`, { reactivate })
  return data
}

export async function createChannel(payload: CreateChannelPayload & { company_id?: number }) {
  const body: CreateChannelPayload & { company_id?: number } = {
    name: payload.name,
    channel_type: payload.channel_type,
    company_id: payload.company_id,
  }
  if (payload.channel_type === 'meta_cloud') {
    body.phone_number_id = payload.phone_number_id
    body.access_token = payload.access_token
    body.verify_token = payload.verify_token
    body.waba_id = payload.waba_id
  }
  if (payload.channel_type === 'meta_messenger' || payload.channel_type === 'meta_instagram') {
    body.app_id = payload.app_id
    body.app_secret = payload.app_secret
    body.page_id = payload.page_id
    body.page_access_token = payload.page_access_token
    body.verify_token = payload.verify_token
    if (payload.channel_type === 'meta_instagram') {
      body.instagram_business_account_id = payload.instagram_business_account_id
    }
  }
  const { data } = await api.post<Channel>('/channels/', body)
  return data
}

export async function deleteChannel(id: number) {
  await api.delete(`/channels/${id}/`)
}

export async function fetchChannelStatus(id: number) {
  const { data } = await api.get<Channel>(`/channels/${id}/status_detail/`)
  return data
}

export async function connectChannel(id: number, reset = false) {
  const { data } = await api.post<Channel>(`/channels/${id}/connect/`, { reset })
  return data
}

export async function revealChannelCredentials(
  id: number,
  stepUp: { password?: string; totp_code?: string },
) {
  const { data } = await api.post<Record<string, string>>(`/channels/${id}/reveal-credentials/`, stepUp)
  return data
}

export async function revealWebhookSecret(
  id: number,
  stepUp: { password?: string; totp_code?: string },
) {
  const { data } = await api.post<{
    webhook_secret: string
    webhook_url: string
    webhook_header: string
  }>(`/channels/${id}/reveal-webhook-secret/`, stepUp)
  return data
}

export async function disconnectChannel(id: number) {
  const { data } = await api.post<Channel>(`/channels/${id}/disconnect/`)
  return data
}
