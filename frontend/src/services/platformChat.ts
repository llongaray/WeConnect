import api from './api'
import type {
  PaginatedResponse,
  PlatformMessage,
  PlatformOperator,
  PlatformRoom,
  PlatformUnreadSummary,
} from '@/types'

export async function fetchPlatformRooms() {
  const { data } = await api.get<PaginatedResponse<PlatformRoom>>('/platform-chat/rooms/')
  return data
}

export async function fetchPlatformOperators() {
  const { data } = await api.get<PlatformOperator[]>('/platform-chat/operators/')
  return data
}

export async function fetchPlatformUnread() {
  const { data } = await api.get<PlatformUnreadSummary>('/platform-chat/unread/')
  return data
}

export async function fetchPlatformMessages(roomId: number, cursor?: number | null) {
  const { data } = await api.get<{ results: PlatformMessage[]; next_cursor: number | null }>(
    `/platform-chat/rooms/${roomId}/messages/`,
    { params: cursor ? { cursor } : {} },
  )
  return data
}

export async function sendPlatformTextMessage(roomId: number, content: string) {
  const { data } = await api.post<PlatformMessage>(
    `/platform-chat/rooms/${roomId}/messages/`,
    { content },
  )
  return data
}

export async function sendPlatformMediaMessage(roomId: number, file: File, content = '') {
  const form = new FormData()
  form.append('media', file)
  if (content) form.append('content', content)
  const { data } = await api.post<PlatformMessage>(
    `/platform-chat/rooms/${roomId}/messages/`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function openPlatformDirect(username: string) {
  const { data } = await api.post<PlatformRoom>('/platform-chat/direct/', { username })
  return data
}

export async function markPlatformRoomRead(roomId: number) {
  await api.post(`/platform-chat/rooms/${roomId}/read/`)
}
