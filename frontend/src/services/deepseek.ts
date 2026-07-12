export {
  fetchAIProviders,
  saveAIProviderToken,
  setDefaultAIProvider,
  disconnectAIProvider,
  generateBotFlow,
} from './aiProviders'

import { fetchAIProviders, saveAIProviderToken } from './aiProviders'

/** @deprecated Use fetchAIProviders */
export async function fetchDeepSeekConfig() {
  const providers = await fetchAIProviders()
  return providers.find((item) => item.provider_type === 'deepseek')!
}

/** @deprecated Use saveAIProviderToken */
export async function saveDeepSeekToken(apiKey: string) {
  return saveAIProviderToken('deepseek', apiKey, true)
}
