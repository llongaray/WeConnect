export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  role: 'admin' | 'supervisor' | 'atendente'
}

export interface TeamChannel {
  id: number
  name: string
}

export interface TeamMembership {
  id: number
  user: User
  role: 'supervisor' | 'atendente'
  created_at: string
}

export interface Team {
  id: number
  name: string
  is_active: boolean
  channels: TeamChannel[]
  memberships: TeamMembership[]
  members_count: number
  created_at: string
  updated_at: string
}

export interface ConversationEvent {
  id: number
  event_type: 'assumed' | 'transferred' | 'released' | 'closed' | 'reopened'
  actor: User | null
  from_user: User | null
  to_user: User | null
  note: string
  created_at: string
}

export interface TeamMemberOption {
  id: number
  username: string
  first_name: string
  last_name: string
  role: string
  team_role: string
}

export type ChannelType = 'evolution_normal' | 'evolution_business' | 'meta_cloud'

export interface Channel {
  id: number
  name: string
  channel_type: ChannelType
  channel_type_label: string
  status: 'connecting' | 'open' | 'close'
  phone: string
  qrcode_base64: string
  is_active: boolean
  webhook_url: string
  created_at: string
  updated_at: string
  detail?: string
}

export interface Contact {
  id: number
  external_id: string
  phone: string
  name: string
  profile_pic_url: string
  created_at: string
  updated_at: string
}

export interface Conversation {
  id: number
  channel: Channel
  contact: Contact
  team: { id: number; name: string } | null
  assigned_to: User | null
  assigned_at: string | null
  status: 'bot' | 'open' | 'closed'
  handoff_pending: boolean
  closed_at: string | null
  closed_by: User | null
  unread_count: number
  last_message_at: string | null
  last_message_preview: string
  recent_events?: ConversationEvent[]
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  conversation: number
  direction: 'in' | 'out'
  message_type: string
  content: string
  media_file: string | null
  media_url: string
  external_id: string
  status: string
  sent_by: User | null
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CursorPaginatedMessages {
  next: string | null
  previous: string | null
  results: Message[]
}

export interface CreateChannelPayload {
  name: string
  channel_type: ChannelType
  phone_number_id?: string
  access_token?: string
  verify_token?: string
  waba_id?: string
}

export type BotNodeType = 'message' | 'decision' | 'menu' | 'assign' | 'end'

export interface BotNodeData {
  content?: string
  label?: string
  options?: string[]
  team_id?: number | null
}

export interface BotFlowDefinition {
  nodes: Array<{
    id: string
    type: BotNodeType
    position: { x: number; y: number }
    data: BotNodeData
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    sourceHandle?: string
  }>
}

export interface BotFlow {
  id: number
  channel: number
  channel_name: string
  name: string
  is_active: boolean
  definition: BotFlowDefinition
  start_node_id: string
  created_at: string
  updated_at: string
}

export interface CreateBotFlowPayload {
  channel: number
  name: string
  is_active?: boolean
  definition?: BotFlowDefinition
  start_node_id?: string
}

export interface UpdateBotFlowPayload {
  name?: string
  is_active?: boolean
  definition?: BotFlowDefinition
  start_node_id?: string
}

export type DeepSeekStatus = 'connected' | 'disconnected' | 'error'

export interface DeepSeekConfig {
  base_url: string
  chat_model: string
  reasoner_model: string
  chat_endpoint: string
  balance_endpoint: string
  status: DeepSeekStatus
  api_key_set: boolean
  api_key_masked: string
  last_validated_at: string | null
  last_error: string
  updated_at: string
}

export interface ChatAssistantMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface GeneratedBotFlow {
  name: string
  start_node_id: string
  nodes: BotFlowDefinition['nodes']
  edges: BotFlowDefinition['edges']
}

export interface GenerateBotFlowResponse {
  reply: string
  flow: GeneratedBotFlow | null
  applied: boolean
}

export interface CurrentFlowContext {
  nodes: BotFlowDefinition['nodes']
  edges: BotFlowDefinition['edges']
  start_node_id: string
}
