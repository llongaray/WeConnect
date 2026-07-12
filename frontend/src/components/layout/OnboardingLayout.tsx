import { useEffect } from 'react'
import { NavLink, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { restoreSession } from '@/services/auth'
import AppHeader from '@/components/layout/AppHeader'
import { cn } from '@/lib/cn'

export default function OnboardingLayout() {
  const user = useAuthStore((s) => s.user)
  const requiresTotpSetup = useAuthStore((s) => s.requiresTotpSetup)
  const isHydrated = useAuthStore((s) => s.isHydrated)
  const setHydrated = useAuthStore((s) => s.setHydrated)

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

  if (!requiresTotpSetup) {
    return <Navigate to="/" replace />
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
      isActive ? 'bg-wa-green/20 text-wa-green' : 'text-wa-muted hover:text-white',
    )

  return (
    <div className="min-h-screen flex flex-col bg-wa-dark">
      <AppHeader
        center={
          <>
            <NavLink to="/onboarding" className={navClass} end>
              Início
            </NavLink>
            <NavLink to="/profile" className={navClass}>
              Perfil
            </NavLink>
          </>
        }
      />

      <main className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto px-3 sm:px-4 py-4 md:py-5 animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
