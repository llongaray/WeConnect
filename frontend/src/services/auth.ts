import axios from 'axios'
import type { User } from '@/types'
import { useAuthStore } from '@/store/authStore'

interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await axios.post<LoginResponse>('/api/auth/login/', { username, password })
  useAuthStore.getState().setAuth(data.access, data.refresh, data.user)
  return data
}

export function logout() {
  useAuthStore.getState().logout()
}
