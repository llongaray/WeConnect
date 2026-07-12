export interface Capabilities {
  manage_companies: boolean
  view_audit: boolean
  view_security: boolean
  manage_tenant: boolean
  manage_users: boolean
  manage_teams: boolean
  manage_channels: boolean
  manage_automation: boolean
  use_ai: boolean
  view_contacts: boolean
  manage_lgpd: boolean
  access_inbox: boolean
  transfer_conversations: boolean
  reopen_conversations: boolean
}

export const defaultCapabilities: Capabilities = {
  manage_companies: false,
  view_audit: false,
  view_security: false,
  manage_tenant: false,
  manage_users: false,
  manage_teams: false,
  manage_channels: false,
  manage_automation: false,
  use_ai: false,
  view_contacts: false,
  manage_lgpd: false,
  access_inbox: false,
  transfer_conversations: false,
  reopen_conversations: false,
}
