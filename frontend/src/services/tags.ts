import api from './api'
import type { Conversation, FunnelStage, PaginatedResponse, Tag } from '@/types'

export interface TagPayload {
  name: string
  color: string
  funnel_order: number
  is_active?: boolean
}

export async function fetchTags(activeOnly = true) {
  const { data } = await api.get<PaginatedResponse<Tag>>('/tags/', {
    params: activeOnly ? { active_only: 'true' } : { active_only: 'false' },
  })
  return data.results
}

export async function createTag(payload: TagPayload) {
  const { data } = await api.post<Tag>('/tags/', payload)
  return data
}

export async function updateTag(id: number, payload: Partial<TagPayload>) {
  const { data } = await api.patch<Tag>(`/tags/${id}/`, payload)
  return data
}

export async function deleteTag(id: number) {
  await api.delete(`/tags/${id}/`)
}

export async function fetchFunnelStages() {
  const { data } = await api.get<FunnelStage[]>('/tags/funnel/')
  return data
}

export async function assignTagToConversation(conversationId: number, tagId: number) {
  const { data } = await api.post<Conversation>(`/conversations/${conversationId}/tags/`, {
    tag_id: tagId,
  })
  return data
}

export async function removeTagFromConversation(conversationId: number, tagId: number) {
  const { data } = await api.delete<Conversation>(`/conversations/${conversationId}/tags/${tagId}/`)
  return data
}
