import api from './api'
import { getCompanyQueryParams } from '@/lib/companyContext'
import type {
  AIProviderConfig,
  AIProviderType,
  ChatAssistantMessage,
  CurrentFlowContext,
  GenerateBotFlowResponse,
} from '@/types'

export async function fetchAIProviders(): Promise<AIProviderConfig[]> {
  const { data } = await api.get<AIProviderConfig[]>('/ai/providers/', {
    params: getCompanyQueryParams(),
  })
  return data
}

export async function saveAIProviderToken(
  providerType: AIProviderType,
  apiKey: string,
  isDefault?: boolean,
): Promise<AIProviderConfig> {
  const { data } = await api.patch<AIProviderConfig>(
    `/ai/providers/${providerType}/`,
    {
      api_key: apiKey,
      ...(isDefault !== undefined ? { is_default: isDefault } : {}),
      ...getCompanyQueryParams(),
    },
    { params: getCompanyQueryParams() },
  )
  return data
}

export async function setDefaultAIProvider(providerType: AIProviderType): Promise<AIProviderConfig> {
  const { data } = await api.patch<AIProviderConfig>(
    `/ai/providers/${providerType}/`,
    { is_default: true, ...getCompanyQueryParams() },
    { params: getCompanyQueryParams() },
  )
  return data
}

export async function disconnectAIProvider(providerType: AIProviderType): Promise<AIProviderConfig> {
  const { data } = await api.delete<AIProviderConfig>(`/ai/providers/${providerType}/`, {
    params: getCompanyQueryParams(),
    data: getCompanyQueryParams(),
  })
  return data
}

export async function generateBotFlow(
  messages: ChatAssistantMessage[],
  currentFlow?: CurrentFlowContext | null,
  provider?: AIProviderType,
): Promise<GenerateBotFlowResponse> {
  const { data } = await api.post<GenerateBotFlowResponse>(
    '/ai/generate-flow/',
    {
      messages,
      current_flow: currentFlow ?? undefined,
      provider,
      ...getCompanyQueryParams(),
    },
    { params: getCompanyQueryParams() },
  )
  return data
}
