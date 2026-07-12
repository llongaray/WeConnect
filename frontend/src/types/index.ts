export interface CompanySummary {
  id: number
  code: string
  trade_name: string
}

export interface CompanyLimits {
  max_supervisors: number
  max_atendentes: number
  max_teams: number
  max_channels: number
}

export interface CompanyUsage {
  supervisors: number
  atendentes: number
  gestores: number
  teams: number
  channels: number
  limits: CompanyLimits
}

export interface Company {
  id: number
  code: string
  legal_name: string
  trade_name: string
  cnpj: string
  address: string
  contact_email: string
  billing_email: string
  contact_phone: string
  billing_phone: string
  is_active: boolean
  max_supervisors: number
  max_atendentes: number
  max_teams: number
  max_channels: number
  usage: CompanyUsage
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: number
  actor: number | null
  actor_name: string
  company: number | null
  action: string
  entity_type: string
  entity_id: string
  entity_label: string
  metadata: Record<string, unknown>
  ip_address: string | null
  created_at: string
}

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  cpf: string
  phone: string
  role: 'gestor' | 'supervisor' | 'atendente'
  is_active: boolean
  is_superuser?: boolean
  is_staff?: boolean
  company: CompanySummary | null
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
  company_id?: number
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

export type ChannelType =
  | 'evolution_normal'
  | 'evolution_business'
  | 'meta_cloud'
  | 'meta_messenger'
  | 'meta_instagram'

export interface MetaCredentials {
  phone_number_id?: string
  access_token?: string
  verify_token?: string
  waba_id?: string
}

export interface MetaMessagingCredentials {
  app_id?: string
  app_secret?: string
  page_id?: string
  page_access_token?: string
  verify_token?: string
  instagram_business_account_id?: string
  page_name?: string
  instagram_username?: string
}

export interface Channel {
  id: number
  name: string
  channel_type: ChannelType
  channel_type_label: string
  status: 'connecting' | 'open' | 'close'
  phone: string
  qrcode_base64: string
  is_active: boolean
  is_archived?: boolean
  company_id: number
  webhook_url: string
  webhook_header?: string | null
  meta_credentials?: MetaCredentials | null
  meta_messaging_credentials?: MetaMessagingCredentials | null
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

export type ConversationCategory = 'novo' | 'aguardando' | 'conversando' | 'finalizado'

export interface ContactTag {
  id: number
  name: string
  color: string
}

export interface Tag {
  id: number
  name: string
  color: string
  funnel_order: number
  is_active: boolean
  contacts_count?: number
  created_at: string
  updated_at: string
}

export interface FunnelStageContact {
  contact_key: string
  name: string
  phone: string
  channel_name: string
  active_conversations: number
}

export interface FunnelStage {
  tag: Pick<Tag, 'id' | 'name' | 'color' | 'funnel_order'>
  contacts_count: number
  contacts: FunnelStageContact[]
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
  category?: ConversationCategory
  contact_tags?: ContactTag[]
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
  app_id?: string
  app_secret?: string
  page_id?: string
  page_access_token?: string
  instagram_business_account_id?: string
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

export type AIProviderType = 'deepseek' | 'openai' | 'anthropic' | 'gemini'
export type AIProviderStatus = 'connected' | 'disconnected' | 'error'

export interface AIProviderConfig {
  provider_type: AIProviderType
  label: string
  base_url: string
  chat_model: string
  reasoner_model: string
  chat_endpoint: string
  balance_endpoint: string
  company_id: number
  status: AIProviderStatus
  is_default: boolean
  configured: boolean
  api_key_set: boolean
  api_key_masked: string
  last_validated_at: string | null
  last_error: string
  updated_at: string | null
}

/** @deprecated Use AIProviderConfig */
export type DeepSeekStatus = AIProviderStatus

/** @deprecated Use AIProviderConfig */
export interface DeepSeekConfig extends AIProviderConfig {}

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

export interface PlatformOperator {
  id: number
  username: string
  first_name: string
  last_name: string
  display_name: string
}

export interface PlatformRoom {
  id: number
  kind: 'group' | 'direct'
  name: string
  slug: string | null
  display_name: string
  unread_count: number
  last_message_at: string | null
  peer: Pick<PlatformOperator, 'id' | 'username' | 'first_name' | 'last_name'> | null
  created_at: string
}

export interface PlatformMessage {
  id: number
  room: number
  sender: User
  content: string
  message_type: 'text' | 'image' | 'audio' | 'file'
  media_file: string | null
  mentioned_usernames: string[]
  created_at: string
}

export interface PlatformUnreadSummary {
  unread_messages: number
  unread_mentions: number
  total: number
}
