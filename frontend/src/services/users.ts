import api from './api'
import type { PaginatedResponse, User } from '@/types'

export interface UserQueryParams {
  search?: string
  role?: User['role'] | ''
  company_id?: number
  scope?: 'platform'
}

export async function fetchUsers(params?: UserQueryParams) {
  const { data } = await api.get<PaginatedResponse<User>>('/users/', { params })
  return data
}

export async function createUser(payload: Record<string, unknown>) {
  const { data } = await api.post<User>('/users/', payload)
  return data
}

export async function updateUser(id: number, payload: Record<string, unknown>) {
  const { data } = await api.patch<User>(`/users/${id}/`, payload)
  return data
}

export async function deleteUser(id: number) {
  await api.delete(`/users/${id}/`)
}
