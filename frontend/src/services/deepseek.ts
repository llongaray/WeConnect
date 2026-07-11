import api from './api'
import type {
  ChatAssistantMessage,
  CurrentFlowContext,
  DeepSeekConfig,
  GenerateBotFlowResponse,
} from '@/types'

export async function fetchDeepSeekConfig(): Promise<DeepSeekConfig> {
  const { data } = await api.get<DeepSeekConfig>('/deepseek/')
  return data
}

export async function saveDeepSeekToken(apiKey: string): Promise<DeepSeekConfig> {
  const { data } = await api.patch<DeepSeekConfig>('/deepseek/', { api_key: apiKey })
  return data
}

export async function generateBotFlow(
  messages: ChatAssistantMessage[],
  currentFlow?: CurrentFlowContext | null,
): Promise<GenerateBotFlowResponse> {
  const { data } = await api.post<GenerateBotFlowResponse>('/deepseek/generate-flow/', {
    messages,
    current_flow: currentFlow ?? undefined,
  })
  return data
}
