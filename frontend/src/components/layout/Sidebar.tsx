import { NavLink } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { logout } from '@/services/auth'
import { navCategories } from '@/config/navigation'
import NavSection from '@/components/ui/NavSection'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

interface SidebarProps {
  onNavigate?: () => void
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  const user = useAuthStore((s) => s.user)
  const isAdmin = useAuthStore((s) => s.isAdmin())

  const displayName = user?.first_name || user?.username || 'Usuário'

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all duration-200',
      'hover:translate-x-0.5 hover:bg-wa-panel/80',
      isActive ? 'nav-item-active font-medium' : 'text-gray-300',
    )

  const visibleCategories = navCategories
    .filter((cat) => !cat.adminOnly || isAdmin)
    .map((cat) => ({
      ...cat,
      items: cat.items.filter((item) => !item.adminOnly || isAdmin),
    }))
    .filter((cat) => cat.items.length > 0)

  return (
    <aside className="w-64 bg-wa-panel border-r border-wa-border flex flex-col shrink-0">
      <div className="p-4 border-b border-wa-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-wa-green/20 flex items-center justify-center">
            <span className="text-wa-green font-bold text-sm">MC</span>
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-bold text-wa-green truncate">MoneyConnect</h1>
            <p className="text-[10px] text-wa-muted">CRM WhatsApp</p>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-4 p-2 rounded-lg bg-wa-dark/50">
          <Avatar name={displayName} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate">{displayName}</p>
            <Badge
              variant={
                user?.role === 'admin'
                  ? 'info'
                  : user?.role === 'supervisor'
                    ? 'warning'
                    : 'default'
              }
              className="mt-0.5 text-[10px]"
            >
              {user?.role === 'admin'
                ? 'Administrador'
                : user?.role === 'supervisor'
                  ? 'Supervisor'
                  : 'Atendente'}
            </Badge>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 overflow-y-auto">
        {visibleCategories.map((category) => (
          <NavSection key={category.id} label={category.label}>
            {category.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={linkClass}
                  onClick={onNavigate}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {item.label}
                </NavLink>
              )
            })}
          </NavSection>
        ))}
      </nav>

      <div className="p-3 border-t border-wa-border">
        <Button
          variant="ghost"
          onClick={logout}
          className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-900/20"
        >
          <LogOut className="w-4 h-4" />
          Sair
        </Button>
      </div>
    </aside>
  )
}
