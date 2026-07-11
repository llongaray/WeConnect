import api from './api'
import type {
  Contact,
  Conversation,
  ConversationEvent,
  CursorPaginatedMessages,
  PaginatedResponse,
  TeamMemberOption,
  User,
} from '@/types'

export interface FetchConversationsParams {
  filter?: string
  channelId?: number
  status?: 'open' | 'closed'
}

export async function fetchConversations(params: FetchConversationsParams = {}) {
  const query: Record<string, string | number> = {}
  if (params.filter) query.filter = params.filter
  if (params.channelId) query.channel = params.channelId
  if (params.status) query.status = params.status
  const { data } = await api.get<PaginatedResponse<Conversation>>('/conversations/', { params: query })
  return data
}

export async function fetchConversation(id: number) {
  const { data } = await api.get<Conversation>(`/conversations/${id}/`)
  return data
}

export async function assumeConversation(id: number) {
  const { data } = await api.patch<Conversation>(`/conversations/${id}/assume/`)
  return data
}

export async function releaseConversation(id: number) {
  const { data } = await api.patch<Conversation>(`/conversations/${id}/release/`)
  return data
}

export async function transferConversation(id: number, assignedToId: number, note = '') {
  const { data } = await api.patch<Conversation>(`/conversations/${id}/transfer/`, {
    assigned_to_id: assignedToId,
    note,
  })
  return data
}

export async function closeConversation(id: number, farewellMessage = '') {
  const { data } = await api.patch<Conversation>(`/conversations/${id}/close/`, {
    farewell_message: farewellMessage,
  })
  return data
}

export async function reopenConversation(id: number) {
  const { data } = await api.patch<Conversation>(`/conversations/${id}/reopen/`)
  return data
}

/** @deprecated Use assumeConversation ou transferConversation */
export async function assignConversation(id: number, assignedToId?: number | null) {
  if (assignedToId == null) return assumeConversation(id)
  return transferConversation(id, assignedToId)
}

export async function fetchConversationTeamMembers(id: number) {
  const { data } = await api.get<TeamMemberOption[]>(`/conversations/${id}/team-members/`)
  return data
}

export async function fetchConversationEvents(id: number) {
  const { data } = await api.get<ConversationEvent[]>(`/conversations/${id}/events/`)
  return data
}

export async function markConversationRead(id: number) {
  const { data } = await api.patch<Conversation>(`/conversations/${id}/mark_read/`)
  return data
}

export async function fetchMessages(conversationId: number, cursor?: string) {
  const url = cursor || `/conversations/${conversationId}/messages/`
  const { data } = await api.get<CursorPaginatedMessages>(url.startsWith('http') ? cursor! : url)
  return data
}

export async function sendTextMessage(conversationId: number, content: string) {
  const { data } = await api.post(`/conversations/${conversationId}/messages/`, {
    content,
    message_type: 'text',
  })
  return data
}

export async function sendMediaMessage(
  conversationId: number,
  file: File,
  messageType: string,
  caption = '',
) {
  const form = new FormData()
  form.append('media', file)
  form.append('message_type', messageType)
  form.append('content', caption)
  const { data } = await api.post(`/conversations/${conversationId}/messages/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function fetchContacts(search?: string) {
  const { data } = await api.get<PaginatedResponse<Contact>>('/contacts/', {
    params: search ? { search } : {},
  })
  return data
}

export async function fetchUsers() {
  const { data } = await api.get<PaginatedResponse<User>>('/users/')
  return data
}

export async function createUser(payload: Record<string, unknown>) {
  const { data } = await api.post<User>('/users/', payload)
  return data
}

export async function updateUser(id: number, payload: Record<string, unknown>) {
  const { data } = await api.patch<User>(`/users/${id}/`, payload)
  return data
}

export async function deleteUser(id: number) {
  await api.delete(`/users/${id}/`)
}
