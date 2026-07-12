import { useAuthStore } from '@/store/authStore'

export function getCompanyQueryParams(): Record<string, number> {
  const state = useAuthStore.getState()
  if ((state.isSuperUser || state.isWeconnectSupport) && state.selectedCompanyId) {
    return { company_id: state.selectedCompanyId }
  }
  return {}
}

export function getActiveCompanyId(): number | null {
  const state = useAuthStore.getState()
  if (state.user?.company?.id) return state.user.company.id
  if ((state.isSuperUser || state.isWeconnectSupport) && state.selectedCompanyId) {
    return state.selectedCompanyId
  }
  return null
}

export function needsPlatformCompanyScope(): boolean {
  const state = useAuthStore.getState()
  return state.isSuperUser || state.isWeconnectSupport
}
