import { useEffect, useMemo, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { NavLink } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useChatSocket } from '@/hooks/useChatSocket'
import { useSidebarPreferences } from '@/hooks/useSidebarPreferences'
import { restoreSession } from '@/services/auth'
import AppHeader from '@/components/layout/AppHeader'
import Sidebar, { roleFilterCategories } from '@/components/layout/Sidebar'
import PlatformChatWidget from '@/components/platform-chat/PlatformChatWidget'
import { cn } from '@/lib/cn'

const onboardingNavClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
    isActive ? 'bg-wa-green/20 text-wa-green' : 'text-wa-muted hover:text-white',
  )

const onboardingHeaderNav = (
  <>
    <NavLink to="/onboarding" className={onboardingNavClass} end>
      Início
    </NavLink>
    <NavLink to="/profile" className={onboardingNavClass}>
      Perfil
    </NavLink>
  </>
)

export default function AppLayout() {
  const location = useLocation()
  const user = useAuthStore((s) => s.user)
  const capabilities = useAuthStore((s) => s.capabilities)
  const requiresTotpSetup = useAuthStore((s) => s.requiresTotpSetup)
  const isHydrated = useAuthStore((s) => s.isHydrated)
  const setHydrated = useAuthStore((s) => s.setHydrated)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const isProfileDuringOnboarding = requiresTotpSetup && location.pathname === '/profile'
  useChatSocket()

  const visibleCategories = useMemo(
    () => roleFilterCategories(capabilities),
    [capabilities],
  )

  const { collapsed, toggleCollapsed, toggleSection, isSectionOpen } =
    useSidebarPreferences(visibleCategories)

  useEffect(() => {
    restoreSession().finally(() => setHydrated(true))
  }, [setHydrated])

  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-wa-dark text-wa-muted">
        Carregando sessão...
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (requiresTotpSetup && !isProfileDuringOnboarding) {
    return <Navigate to="/onboarding" replace />
  }

  if (isProfileDuringOnboarding) {
    return (
      <div className="min-h-screen flex flex-col bg-wa-dark">
        <AppHeader center={onboardingHeaderNav} />
        <main className="flex-1 overflow-auto">
          <div className="max-w-5xl mx-auto px-3 sm:px-4 py-4 md:py-5 animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    )
  }

  const sidebarProps = {
    collapsed,
    onToggleCollapse: toggleCollapsed,
    isSectionOpen,
    onToggleSection: toggleSection,
  }

  return (
    <div className="flex h-screen bg-wa-dark">
      <div
        className={cn(
          'hidden lg:flex shrink-0 transition-[width] duration-200',
          collapsed ? 'w-[4.5rem]' : 'w-64',
        )}
      >
        <Sidebar {...sidebarProps} showCollapseToggle />
      </div>

      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="relative z-50 animate-slide-in-right">
            <Sidebar
              {...sidebarProps}
              collapsed={false}
              onNavigate={() => setSidebarOpen(false)}
              showCollapseToggle={false}
            />
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <AppHeader
          showMenuButton
          sidebarOpen={sidebarOpen}
          onMenuClick={() => setSidebarOpen((v) => !v)}
        />

        <main className="flex-1 overflow-hidden">
          <div className={cn('h-full animate-fade-in')}>
            <Outlet context={{ setSidebarOpen }} />
          </div>
        </main>
      </div>
      <PlatformChatWidget />
    </div>
  )
}
