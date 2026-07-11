import api from './api'
import type { PaginatedResponse, Team } from '@/types'

export async function fetchTeams() {
  const { data } = await api.get<PaginatedResponse<Team>>('/teams/')
  return data
}

export async function fetchTeam(id: number) {
  const { data } = await api.get<Team>(`/teams/${id}/`)
  return data
}

export async function createTeam(payload: {
  name: string
  is_active?: boolean
  channel_ids?: number[]
}) {
  const { data } = await api.post<Team>('/teams/', payload)
  return data
}

export async function updateTeam(
  id: number,
  payload: { name?: string; is_active?: boolean; channel_ids?: number[] },
) {
  const { data } = await api.patch<Team>(`/teams/${id}/`, payload)
  return data
}

export async function deleteTeam(id: number) {
  await api.delete(`/teams/${id}/`)
}

export async function addTeamMember(teamId: number, userId: number, role: 'supervisor' | 'atendente') {
  const { data } = await api.post<Team>(`/teams/${teamId}/members/`, {
    user_id: userId,
    role,
  })
  return data
}

export async function removeTeamMember(teamId: number, userId: number) {
  const { data } = await api.delete<Team>(`/teams/${teamId}/members/${userId}/`)
  return data
}

export async function setTeamDefaultChannel(teamId: number, channelId: number) {
  const { data } = await api.patch<Team>(`/teams/${teamId}/set-default-channel/`, {
    channel_id: channelId,
  })
  return data
}
