import type { LucideIcon } from 'lucide-react'
import { Bot, Brain, Sparkles, Stars } from 'lucide-react'
import type { AIProviderType } from '@/types'

export interface AIProviderMeta {
  type: AIProviderType
  label: string
  description: string
  tokenLabel: string
  tokenPlaceholder: string
  docsUrl: string
  icon: LucideIcon
  accentClass: string
}

export const AI_PROVIDER_CATALOG: AIProviderMeta[] = [
  {
    type: 'deepseek',
    label: 'DeepSeek',
    description: 'Modelos deepseek-chat e deepseek-reasoner para automação de fluxos.',
    tokenLabel: 'API Token DeepSeek',
    tokenPlaceholder: 'sk-...',
    docsUrl: 'https://platform.deepseek.com/api_keys',
    icon: Sparkles,
    accentClass: 'text-sky-400',
  },
  {
    type: 'openai',
    label: 'ChatGPT',
    description: 'OpenAI GPT para geração de fluxos e assistentes conversacionais.',
    tokenLabel: 'API Key OpenAI',
    tokenPlaceholder: 'sk-...',
    docsUrl: 'https://platform.openai.com/api-keys',
    icon: Bot,
    accentClass: 'text-emerald-400',
  },
  {
    type: 'anthropic',
    label: 'Claude',
    description: 'Anthropic Claude para raciocínio e criação de fluxos complexos.',
    tokenLabel: 'API Key Anthropic',
    tokenPlaceholder: 'sk-ant-...',
    docsUrl: 'https://console.anthropic.com/settings/keys',
    icon: Brain,
    accentClass: 'text-amber-300',
  },
  {
    type: 'gemini',
    label: 'Gemini',
    description: 'Google Gemini para assistência e geração de conteúdo no funil.',
    tokenLabel: 'API Key Google AI',
    tokenPlaceholder: 'AIza...',
    docsUrl: 'https://aistudio.google.com/app/apikey',
    icon: Stars,
    accentClass: 'text-blue-300',
  },
]

export function getAIProviderMeta(type: AIProviderType): AIProviderMeta {
  return AI_PROVIDER_CATALOG.find((item) => item.type === type) ?? AI_PROVIDER_CATALOG[0]
}
