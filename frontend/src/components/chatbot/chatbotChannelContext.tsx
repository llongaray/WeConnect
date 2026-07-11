import { createContext, useContext } from 'react'

export interface ChannelTeamOption {
  id: number
  name: string
}

export const ChatbotChannelContext = createContext<{
  channelTeams: ChannelTeamOption[]
}>({
  channelTeams: [],
})

export function useChatbotChannel() {
  return useContext(ChatbotChannelContext)
}
