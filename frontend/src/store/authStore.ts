import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setAuth: (access: string, refresh: string, user: User) => void
  setAccessToken: (token: string) => void
  logout: () => void
  isAdmin: () => boolean
  isSupervisor: () => boolean
  canTransfer: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setAuth: (access, refresh, user) =>
        set({ accessToken: access, refreshToken: refresh, user }),
      setAccessToken: (token) => set({ accessToken: token }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
      isAdmin: () => get().user?.role === 'admin',
      isSupervisor: () => get().user?.role === 'supervisor',
      canTransfer: () => {
        const role = get().user?.role
        return role === 'admin' || role === 'supervisor'
      },
    }),
    { name: 'moneyconnect-auth' },
  ),
)
