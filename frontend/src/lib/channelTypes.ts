import type { LucideIcon } from 'lucide-react'
import {
  Building2,
  Camera,
  Cloud,
  MessageCircle,
  Smartphone,
} from 'lucide-react'
import type { ChannelType, ConversationCategory } from '@/types'

export type ChannelPlatform = 'whatsapp' | 'messenger' | 'instagram'

export function getChannelPlatform(channelType: ChannelType): ChannelPlatform {
  if (channelType === 'meta_messenger') return 'messenger'
  if (channelType === 'meta_instagram') return 'instagram'
  return 'whatsapp'
}

export function getChannelPlatformLabel(channelType: ChannelType): string {
  const platform = getChannelPlatform(channelType)
  if (platform === 'messenger') return 'Messenger'
  if (platform === 'instagram') return 'Instagram'
  if (channelType === 'meta_cloud') return 'WhatsApp API'
  if (channelType === 'evolution_business') return 'WhatsApp Business'
  return 'WhatsApp'
}

export function getChannelTypeIcon(channelType: ChannelType): LucideIcon {
  switch (channelType) {
    case 'evolution_business':
      return Building2
    case 'meta_cloud':
      return Cloud
    case 'meta_messenger':
      return MessageCircle
    case 'meta_instagram':
      return Camera
    default:
      return Smartphone
  }
}

export function isMetaManualChannel(channelType: ChannelType): boolean {
  return (
    channelType === 'meta_cloud' ||
    channelType === 'meta_messenger' ||
    channelType === 'meta_instagram'
  )
}

export const channelPlatformBadgeVariant: Record<
  ChannelPlatform,
  'success' | 'info' | 'warning' | 'default'
> = {
  whatsapp: 'success',
  messenger: 'info',
  instagram: 'warning',
}

export const conversationCategoryLabels: Record<ConversationCategory, string> = {
  novo: 'Novo',
  aguardando: 'Aguardando',
  conversando: 'Conversando',
  finalizado: 'Finalizado',
}

export const conversationCategoryBadgeVariant: Record<
  ConversationCategory,
  'success' | 'info' | 'warning' | 'default'
> = {
  novo: 'info',
  aguardando: 'warning',
  conversando: 'success',
  finalizado: 'default',
}
