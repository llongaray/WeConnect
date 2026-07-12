import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { CompanySummary, User } from '@/types'
import { defaultCapabilities, type Capabilities } from '@/lib/capabilities'

export type AccessMode = 'setup_only' | 'full'

export interface SessionFlags {
  requiresTotpSetup?: boolean
  totpEnabled?: boolean
  accessMode?: AccessMode
  requiresPrivacyAcceptance?: boolean
  capabilities?: Capabilities
  isWeconnectSupport?: boolean
}

interface AuthState {
  user: User | null
  isSuperUser: boolean
  isWeconnectSupport: boolean
  capabilities: Capabilities
  selectedCompanyId: number | null
  setupToken: string | null
  isHydrated: boolean
  requiresTotpSetup: boolean
  totpEnabled: boolean
  accessMode: AccessMode
  requiresPrivacyAcceptance: boolean
  setAuth: (user: User, isSuperUser?: boolean, session?: SessionFlags) => void
  setSessionFlags: (flags: SessionFlags) => void
  setSetupToken: (token: string | null) => void
  setSelectedCompanyId: (companyId: number | null) => void
  setHydrated: (value: boolean) => void
  logout: () => void
  hasCapability: (key: keyof Capabilities) => boolean
  isPlatformAdmin: () => boolean
  isGestor: () => boolean
  isSupervisor: () => boolean
  canManageTenant: () => boolean
  hasCompanyScope: () => boolean
  isAdmin: () => boolean
  canTransfer: () => boolean
  getCompanyContext: () => CompanySummary | null
}

function resolveSuperUser(user: User | null, explicit?: boolean) {
  return Boolean(explicit ?? user?.is_superuser)
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isSuperUser: false,
      isWeconnectSupport: false,
      capabilities: defaultCapabilities,
      selectedCompanyId: null,
      setupToken: null,
      isHydrated: false,
      requiresTotpSetup: false,
      totpEnabled: false,
      accessMode: 'full',
      requiresPrivacyAcceptance: false,
      setAuth: (user, isSuperUser, session) => {
        const superUser = resolveSuperUser(user, isSuperUser)
        const support = session?.isWeconnectSupport ?? Boolean(user.is_staff && !superUser)
        set({
          user: { ...user, is_superuser: superUser },
          isSuperUser: superUser,
          isWeconnectSupport: support,
          capabilities: session?.capabilities ?? get().capabilities,
          selectedCompanyId: superUser || support
            ? get().selectedCompanyId
            : (user.company?.id ?? null),
          requiresTotpSetup: session?.requiresTotpSetup ?? get().requiresTotpSetup,
          totpEnabled: session?.totpEnabled ?? get().totpEnabled,
          accessMode: session?.accessMode ?? get().accessMode,
          requiresPrivacyAcceptance:
            session?.requiresPrivacyAcceptance ?? get().requiresPrivacyAcceptance,
        })
      },
      setSessionFlags: (flags) =>
        set({
          requiresTotpSetup: flags.requiresTotpSetup ?? get().requiresTotpSetup,
          totpEnabled: flags.totpEnabled ?? get().totpEnabled,
          accessMode: flags.accessMode ?? get().accessMode,
          requiresPrivacyAcceptance:
            flags.requiresPrivacyAcceptance ?? get().requiresPrivacyAcceptance,
          capabilities: flags.capabilities ?? get().capabilities,
          isWeconnectSupport: flags.isWeconnectSupport ?? get().isWeconnectSupport,
        }),
      setSetupToken: (token) => set({ setupToken: token }),
      setSelectedCompanyId: (companyId) => set({ selectedCompanyId: companyId }),
      setHydrated: (value) => set({ isHydrated: value }),
      logout: () =>
        set({
          user: null,
          isSuperUser: false,
          isWeconnectSupport: false,
          capabilities: defaultCapabilities,
          selectedCompanyId: null,
          setupToken: null,
          requiresTotpSetup: false,
          totpEnabled: false,
          accessMode: 'full',
          requiresPrivacyAcceptance: false,
        }),
      hasCapability: (key) => Boolean(get().capabilities[key]),
      isPlatformAdmin: () => get().isSuperUser,
      isGestor: () => !get().isSuperUser && !get().isWeconnectSupport && get().user?.role === 'gestor',
      isSupervisor: () => get().user?.role === 'supervisor',
      canManageTenant: () => get().hasCapability('manage_tenant'),
      hasCompanyScope: () => {
        const state = get()
        if (state.user?.company?.id) return true
        return (state.isSuperUser || state.isWeconnectSupport) && Boolean(state.selectedCompanyId)
      },
      isAdmin: () => {
        const state = get()
        if (state.isSuperUser) return true
        if (state.user?.role === 'gestor') return true
        if (state.isWeconnectSupport && state.hasCompanyScope()) return true
        return false
      },
      canTransfer: () => get().hasCapability('transfer_conversations'),
      getCompanyContext: () => {
        const state = get()
        if (state.user?.company) return state.user.company
        return null
      },
    }),
    {
      name: 'weconnect-auth',
      partialize: (state) => ({
        selectedCompanyId: state.selectedCompanyId,
        setupToken: state.setupToken,
        ...(state.setupToken
          ? {
              user: state.user,
              isSuperUser: state.isSuperUser,
              isWeconnectSupport: state.isWeconnectSupport,
              capabilities: state.capabilities,
              requiresTotpSetup: state.requiresTotpSetup,
              totpEnabled: state.totpEnabled,
              accessMode: state.accessMode,
              requiresPrivacyAcceptance: state.requiresPrivacyAcceptance,
            }
          : {}),
      }),
    },
  ),
)
