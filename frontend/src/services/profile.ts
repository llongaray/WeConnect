import api from './api'
import type { User } from '@/types'

export interface ProfileUpdatePayload {
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
}

export async function fetchProfile() {
  const { data } = await api.get<User>('/profile/')
  return data
}

export async function updateProfile(payload: ProfileUpdatePayload) {
  const { data } = await api.patch<User>('/profile/', payload)
  return data
}
