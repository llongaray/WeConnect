import api from './api'
import type { Channel, CreateChannelPayload, PaginatedResponse } from '@/types'

export async function fetchChannels() {
  const { data } = await api.get<PaginatedResponse<Channel> | Channel[]>('/channels/')
  if (Array.isArray(data)) return data
  return data.results
}

export async function createChannel(payload: CreateChannelPayload) {
  const body: CreateChannelPayload = { name: payload.name, channel_type: payload.channel_type }
  if (payload.channel_type === 'meta_cloud') {
    body.phone_number_id = payload.phone_number_id
    body.access_token = payload.access_token
    body.verify_token = payload.verify_token
    body.waba_id = payload.waba_id
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

export async function disconnectChannel(id: number) {
  const { data } = await api.post<Channel>(`/channels/${id}/disconnect/`)
  return data
}
