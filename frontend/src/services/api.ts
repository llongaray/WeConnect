import axios from 'axios'
import { clearAuthLocal, fetchCsrfToken, isPendingSetupSession, readCsrfToken } from '@/services/auth'
import { getCompanyQueryParams } from '@/lib/companyContext'
import { endRequest, startRequest } from '@/lib/loadingTracker'

declare module 'axios' {
  export interface AxiosRequestConfig {
    meta?: {
      silent?: boolean
    }
  }
}

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

let csrfReady = false

export async function ensureCsrfReady() {
  if (!csrfReady) {
    await fetchCsrfToken()
    csrfReady = true
  }
}

api.interceptors.request.use(async (config) => {
  if (!config.meta?.silent) {
    startRequest()
  }
  const companyParams = getCompanyQueryParams()
  if (companyParams.company_id) {
    config.params = { ...config.params, ...companyParams }
  }
  const method = (config.method || 'get').toUpperCase()
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    await ensureCsrfReady()
    const token = readCsrfToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers['X-CSRFToken'] = token
    }
  }
  return config
})

let refreshing = false

api.interceptors.response.use(
  (response) => {
    if (!response.config.meta?.silent) {
      endRequest()
    }
    return response
  },
  async (error) => {
    if (!error.config?.meta?.silent) {
      endRequest()
    }

    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      // Durante onboarding 2FA ainda não há JWT; não deslogar por 401 de APIs protegidas
      if (isPendingSetupSession()) {
        return Promise.reject(error)
      }

      original._retry = true
      if (refreshing) {
        clearAuthLocal()
        return Promise.reject(error)
      }
      refreshing = true
      startRequest()
      try {
        await fetchCsrfToken()
        const csrfToken = readCsrfToken()
        await axios.post('/api/auth/refresh/', {}, {
          withCredentials: true,
          headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
        })
        endRequest()
        return api(original)
      } catch {
        endRequest()
        clearAuthLocal()
        return Promise.reject(error)
      } finally {
        refreshing = false
      }
    }
    return Promise.reject(error)
  },
)

export default api
