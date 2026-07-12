import api from './api'
import type { AuditLog, Company, PaginatedResponse } from '@/types'

export interface AuditLogQueryParams {
  company_id?: number
  action?: string
  entity_type?: 'company' | 'user' | 'team' | ''
}

export async function fetchCompanies() {
  const { data } = await api.get<PaginatedResponse<Company> | Company[]>('/companies/')
  return Array.isArray(data) ? { results: data } : data
}

export async function fetchCompany(id: number) {
  const { data } = await api.get<Company>(`/companies/${id}/`)
  return data
}

export async function createCompany(payload: Record<string, unknown>) {
  const { data } = await api.post<Company>('/companies/', payload)
  return data
}

export async function updateCompany(id: number, payload: Record<string, unknown>) {
  const { data } = await api.patch<Company>(`/companies/${id}/`, payload)
  return data
}

export async function createCompanyGestor(companyId: number, payload: Record<string, unknown>) {
  const { data } = await api.post(`/companies/${companyId}/gestor/`, payload)
  return data
}

export async function fetchAuditLogs(params?: AuditLogQueryParams) {
  const { data } = await api.get<PaginatedResponse<AuditLog> | AuditLog[]>('/audit-logs/', { params })
  return Array.isArray(data) ? { results: data } : data
}

export interface CnpjLookupResult {
  cnpj: string
  legal_name: string
  trade_name: string
  address: string
  contact_email: string
  contact_phone: string
}

export async function lookupCompanyCnpj(cnpj: string) {
  const { data } = await api.get<CnpjLookupResult>('/companies/lookup-cnpj/', {
    params: { cnpj },
  })
  return data
}
