import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { LogOut, Menu, X } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { logout } from '@/services/auth'
import CompanyScopeBar from '@/components/admin/CompanyScopeBar'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

interface AppHeaderProps {
  /** Links centrais (ex.: onboarding) */
  center?: ReactNode
  /** Botão menu mobile (AppLayout) */
  showMenuButton?: boolean
  sidebarOpen?: boolean
  onMenuClick?: () => void
  className?: string
}

function roleLabel(role?: string, isSuperUser?: boolean, isWeconnectSupport?: boolean) {
  if (isSuperUser) return 'Superuser'
  if (isWeconnectSupport) return 'Suporte WeConnect'
  if (role === 'gestor') return 'Gestor'
  if (role === 'supervisor') return 'Supervisor'
  return 'Atendente'
}

export default function AppHeader({
  center,
  showMenuButton = false,
  sidebarOpen = false,
  onMenuClick,
  className,
}: AppHeaderProps) {
  const user = useAuthStore((s) => s.user)
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const isWeconnectSupport = useAuthStore((s) => s.isWeconnectSupport)

  const displayName = user?.first_name || user?.username || 'Usuário'

  const handleLogout = () => {
    void logout().then(() => {
      window.location.href = '/login'
    })
  }

  return (
    <header
      className={cn(
        'h-12 border-b border-wa-border bg-wa-panel/95 shrink-0',
        className,
      )}
    >
      <div className="h-full px-3 sm:px-4 flex items-center gap-2 sm:gap-3 min-w-0">
        {showMenuButton && (
          <button
            onClick={onMenuClick}
            className="lg:hidden p-1.5 rounded-md hover:bg-wa-dark transition-colors shrink-0"
            aria-label="Menu"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        )}

        <div className="flex items-center gap-2 min-w-0 shrink-0">
          <img
            src="/branding/logo-weconnect.png"
            alt="WeConnect"
            className="h-7 w-auto shrink-0"
          />
          <span className="font-semibold text-sm text-wa-green truncate hidden sm:inline">
            WeConnect
          </span>
        </div>

        {center && (
          <nav className="flex items-center gap-1 shrink-0 mx-1 sm:mx-2">{center}</nav>
        )}

        <div className="flex-1 min-w-0 flex items-center justify-end gap-2 sm:gap-3">
          <CompanyScopeBar variant="header" />

          <Link
            to="/profile"
            title="Abrir perfil"
            className="flex items-center gap-2 min-w-0 shrink-0 pl-1 border-l border-wa-border/60 rounded-md px-1.5 py-1 -my-1 hover:bg-wa-dark/60 transition-colors"
          >
            <Avatar name={displayName} size="sm" />
            <div className="min-w-0 hidden md:block">
              <p className="text-xs font-medium truncate max-w-[140px]">{displayName}</p>
              <Badge
                variant={
                  isSuperUser || user?.role === 'gestor'
                    ? 'info'
                    : user?.role === 'supervisor'
                      ? 'warning'
                      : 'default'
                }
                className="text-[10px] mt-0.5"
              >
                {roleLabel(user?.role, isSuperUser, isWeconnectSupport)}
              </Badge>
            </div>
          </Link>

          <Button
            variant="ghost"
            className="px-2 py-1.5 h-8 w-8 sm:w-auto sm:px-2.5 shrink-0 text-red-400 hover:text-red-300 hover:bg-red-900/20"
            onClick={handleLogout}
            title="Sair"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden md:inline ml-1.5 text-xs">Sair</span>
          </Button>
        </div>
      </div>
    </header>
  )
}
