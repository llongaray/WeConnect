import { useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useChatSocket } from '@/hooks/useChatSocket'
import Sidebar from '@/components/layout/Sidebar'
import { cn } from '@/lib/cn'

export default function AppLayout() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  useChatSocket()

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="flex h-screen bg-wa-dark">
      {/* Sidebar desktop */}
      <div className="hidden lg:flex">
        <Sidebar />
      </div>

      {/* Sidebar mobile drawer */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="relative z-50 animate-slide-in-right">
            <Sidebar onNavigate={() => setSidebarOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header mobile */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-wa-panel border-b border-wa-border shrink-0">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="p-2 rounded-lg hover:bg-wa-dark transition-colors"
            aria-label="Menu"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="font-semibold text-wa-green">MoneyConnect</span>
        </header>

        <main className="flex-1 overflow-hidden">
          <div className={cn('h-full animate-fade-in')}>
            <Outlet context={{ setSidebarOpen }} />
          </div>
        </main>
      </div>
    </div>
  )
}
