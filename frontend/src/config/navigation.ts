import {
  Home,
  MessageSquare,
  Users,
  Radio,
  UserCog,
  Bot,
  Sparkles,
  UsersRound,
  ShieldAlert,
  Building2,
  ScrollText,
  Filter,
  Columns3,
  type LucideIcon,
} from 'lucide-react'
import type { Capabilities } from '@/lib/capabilities'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  end?: boolean
  /** Capability necessária para exibir o item */
  requiredCapability?: keyof Capabilities
}

export interface NavCategory {
  id: string
  label: string
  requiredCapability?: keyof Capabilities
  /** Link direto no topo, sem cabeçalho de seção */
  standalone?: boolean
  collapsible?: boolean
  defaultOpen?: boolean
  items: NavItem[]
}

export const navCategories: NavCategory[] = [
  {
    id: 'home',
    label: 'Início',
    standalone: true,
    items: [
      { to: '/', label: 'Início', icon: Home, end: true },
    ],
  },
  {
    id: 'omnichannel',
    label: 'Omnichannel',
    defaultOpen: true,
    requiredCapability: 'access_inbox',
    items: [
      { to: '/inbox', label: 'Chat', icon: MessageSquare, end: true, requiredCapability: 'access_inbox' },
      { to: '/funnel', label: 'Funil', icon: Columns3, requiredCapability: 'access_inbox' },
      { to: '/contacts', label: 'Contatos', icon: Users, requiredCapability: 'view_contacts' },
      { to: '/admin/channels', label: 'Canais', icon: Radio, requiredCapability: 'manage_channels' },
    ],
  },
  {
    id: 'management',
    label: 'Gerenciamento',
    requiredCapability: 'manage_tenant',
    defaultOpen: true,
    items: [
      { to: '/admin/companies', label: 'Empresas', icon: Building2, end: true, requiredCapability: 'manage_companies' },
      { to: '/admin/users', label: 'Usuários', icon: UserCog, requiredCapability: 'manage_users' },
      { to: '/admin/teams', label: 'Equipes', icon: UsersRound, requiredCapability: 'manage_teams' },
      { to: '/admin/funnel', label: 'Etapas do funil', icon: Filter, requiredCapability: 'manage_teams' },
      { to: '/admin/security', label: 'Segurança', icon: ShieldAlert, requiredCapability: 'view_security' },
      { to: '/admin/audit-logs', label: 'Auditoria', icon: ScrollText, requiredCapability: 'view_audit' },
    ],
  },
  {
    id: 'automation',
    label: 'Automação',
    requiredCapability: 'manage_automation',
    collapsible: false,
    items: [
      { to: '/admin/chatbot', label: 'Chatbot', icon: Bot, requiredCapability: 'manage_automation' },
    ],
  },
  {
    id: 'ai',
    label: 'Inteligência Artificial',
    requiredCapability: 'use_ai',
    collapsible: false,
    items: [
      { to: '/admin/ai', label: 'Inteligência Artificial', icon: Sparkles, requiredCapability: 'use_ai' },
    ],
  },
]

/** Verifica se a rota pertence a algum item da categoria */
export function categoryContainsPath(category: NavCategory, pathname: string): boolean {
  return category.items.some((item) => {
    if (item.end) return pathname === item.to
    return pathname === item.to || pathname.startsWith(`${item.to}/`)
  })
}

export function hasCapability(
  capabilities: Capabilities,
  key?: keyof Capabilities,
): boolean {
  if (!key) return true
  return Boolean(capabilities[key])
}

export function filterNavCategories(
  categories: NavCategory[],
  capabilities: Capabilities,
): NavCategory[] {
  return categories
    .filter((cat) => hasCapability(capabilities, cat.requiredCapability))
    .map((cat) => ({
      ...cat,
      items: cat.items.filter((item) => hasCapability(capabilities, item.requiredCapability)),
    }))
    .filter((cat) => cat.items.length > 0)
}
