import api from './api'
import type {
  BotFlow,
  CreateBotFlowPayload,
  PaginatedResponse,
  UpdateBotFlowPayload,
} from '@/types'

export async function fetchBotFlows(channelId?: number): Promise<BotFlow[]> {
  const params = channelId ? { channel: channelId } : {}
  const { data } = await api.get<PaginatedResponse<BotFlow>>('/bot-flows/', { params })
  return data.results ?? []
}

export async function fetchBotFlow(id: number): Promise<BotFlow> {
  const { data } = await api.get<BotFlow>(`/bot-flows/${id}/`)
  return data
}

export async function createBotFlow(payload: CreateBotFlowPayload): Promise<BotFlow> {
  const { data } = await api.post<BotFlow>('/bot-flows/', payload)
  return data
}

export async function updateBotFlow(id: number, payload: UpdateBotFlowPayload): Promise<BotFlow> {
  const { data } = await api.patch<BotFlow>(`/bot-flows/${id}/`, payload)
  return data
}

export async function deleteBotFlow(id: number): Promise<void> {
  await api.delete(`/bot-flows/${id}/`)
}
