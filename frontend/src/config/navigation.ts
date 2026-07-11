import {
  MessageSquare,
  Users,
  Radio,
  UserCog,
  Bot,
  Sparkles,
  UsersRound,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  end?: boolean
  adminOnly?: boolean
}

export interface NavCategory {
  id: string
  label: string
  adminOnly?: boolean
  items: NavItem[]
}

export const navCategories: NavCategory[] = [
  {
    id: 'omnichannel',
    label: 'Omnichannel',
    items: [
      { to: '/', label: 'Chat', icon: MessageSquare, end: true },
      { to: '/contacts', label: 'Contatos', icon: Users },
      { to: '/admin/channels', label: 'Canais', icon: Radio, adminOnly: true },
    ],
  },
  {
    id: 'automation',
    label: 'Automação',
    adminOnly: true,
    items: [
      { to: '/admin/chatbot', label: 'Chatbot', icon: Bot },
    ],
  },
  {
    id: 'ai',
    label: 'Inteligência Artificial',
    adminOnly: true,
    items: [
      { to: '/admin/deepseek', label: 'DeepSeek', icon: Sparkles },
    ],
  },
  {
    id: 'admin',
    label: 'Administração',
    adminOnly: true,
    items: [
      { to: '/admin/users', label: 'Usuários', icon: UserCog },
      { to: '/admin/teams', label: 'Equipes', icon: UsersRound },
    ],
  },
]
