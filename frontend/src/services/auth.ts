import axios from 'axios'
import type { User } from '@/types'
import type { Capabilities } from '@/lib/capabilities'
import { defaultCapabilities } from '@/lib/capabilities'
import { useAuthStore, type AccessMode } from '@/store/authStore'
import { endRequest, startRequest } from '@/lib/loadingTracker'

const authClient = axios.create({
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

export interface LoginPrecheck {
  requires_captcha: boolean
  locked: boolean
  lockout_seconds: number
  turnstile_site_key: string
}

interface AuthSessionPayload {
  user?: User
  is_superuser?: boolean
  requires_totp_setup?: boolean
  totp_enabled?: boolean
  access_mode?: AccessMode
  setup_token?: string
  requires_privacy_acceptance?: boolean
  capabilities?: Capabilities
  is_weconnect_support?: boolean
}

interface LoginResponse extends AuthSessionPayload {
  requires_totp?: boolean
  pending_token?: string
  requires_captcha?: boolean
  detail?: string
  lockout_seconds?: number
  backup_codes?: string[]
}

interface LoginErrorBody {
  detail?: string
  lockout_seconds?: number
  requires_captcha?: boolean
  requires_totp?: boolean
  requires_totp_setup?: boolean
  pending_token?: string
}

export class LoginError extends Error {
  lockoutSeconds?: number
  isRateLimited: boolean
  requiresCaptcha: boolean
  requiresTotp: boolean
  requiresTotpSetup: boolean
  pendingToken?: string

  constructor(message: string, options?: {
    lockoutSeconds?: number
    isRateLimited?: boolean
    requiresCaptcha?: boolean
    requiresTotp?: boolean
    requiresTotpSetup?: boolean
    pendingToken?: string
  }) {
    super(message)
    this.name = 'LoginError'
    this.lockoutSeconds = options?.lockoutSeconds
    this.isRateLimited = options?.isRateLimited ?? false
    this.requiresCaptcha = options?.requiresCaptcha ?? false
    this.requiresTotp = options?.requiresTotp ?? false
    this.requiresTotpSetup = options?.requiresTotpSetup ?? false
    this.pendingToken = options?.pendingToken
  }
}

function applySessionPayload(data: AuthSessionPayload) {
  if (!data.user) return
  useAuthStore.getState().setAuth(data.user, Boolean(data.is_superuser), {
    requiresTotpSetup: Boolean(data.requires_totp_setup),
    totpEnabled: Boolean(data.totp_enabled),
    accessMode: data.access_mode ?? (data.requires_totp_setup ? 'setup_only' : 'full'),
    requiresPrivacyAcceptance: Boolean(data.requires_privacy_acceptance),
    capabilities: data.capabilities ?? defaultCapabilities,
    isWeconnectSupport: Boolean(data.is_weconnect_support),
  })
  if (data.setup_token) {
    useAuthStore.getState().setSetupToken(data.setup_token)
  } else if (!data.requires_totp_setup) {
    useAuthStore.getState().setSetupToken(null)
  }
}

async function authPost<T>(path: string, body: Record<string, unknown> = {}) {
  await fetchCsrfToken()
  const token = readCsrfToken()
  return authClient.post<T>(path, body, {
    headers: token ? { 'X-CSRFToken': token } : {},
  })
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const { data } = await authClient.get<{ csrfToken: string }>('/api/auth/csrf/')
    return data.csrfToken || getCookie('csrftoken')
  } catch {
    return getCookie('csrftoken')
  }
}

export function readCsrfToken(): string | null {
  return getCookie('csrftoken')
}

export function formatLockoutMessage(seconds?: number): string {
  if (!seconds || seconds <= 0) {
    return 'Acesso temporariamente bloqueado. Tente novamente mais tarde.'
  }
  const minutes = Math.ceil(seconds / 60)
  return `Acesso temporariamente bloqueado. Tente novamente em cerca de ${minutes} minuto(s).`
}

export async function fetchLoginPrecheck(username: string): Promise<LoginPrecheck> {
  const { data } = await authClient.get<LoginPrecheck>('/api/auth/login/precheck/', {
    params: { username },
  })
  return data
}

export async function login(
  username: string,
  password: string,
  captchaToken?: string,
): Promise<LoginResponse> {
  startRequest()
  try {
    const { data, status } = await authClient.post<LoginResponse>('/api/auth/login/', {
      username,
      password,
      captcha_token: captchaToken,
    })

    if (status === 202 && data.requires_totp) {
      throw new LoginError('Informe o código 2FA.', {
        requiresTotp: true,
        pendingToken: data.pending_token,
      })
    }

    applySessionPayload(data)
    return data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const status = err.response?.status
      const body = err.response?.data as LoginErrorBody | undefined
      const detail = typeof body?.detail === 'string' ? body.detail : undefined

      if (status === 429) {
        throw new LoginError(formatLockoutMessage(body?.lockout_seconds), {
          lockoutSeconds: body?.lockout_seconds,
          isRateLimited: true,
        })
      }

      if (status === 403 && body?.requires_totp_setup) {
        throw new LoginError(
          'Serviço desatualizado. Recarregue a página (Ctrl+F5) e tente novamente. Se persistir, reconstrua os containers Docker.',
          { requiresTotpSetup: true },
        )
      }

      if (detail) {
        throw new LoginError(detail, { requiresCaptcha: body?.requires_captcha })
      }
    }
    if (err instanceof LoginError) throw err
    throw new LoginError('Credenciais inválidas ou acesso temporariamente bloqueado. Tente novamente mais tarde.')
  } finally {
    endRequest()
  }
}

export async function loginTotp(
  pendingToken: string,
  code: string,
  trustDevice = true,
): Promise<LoginResponse> {
  startRequest()
  try {
    const { data } = await authClient.post<LoginResponse>('/api/auth/login/totp/', {
      pending_token: pendingToken,
      code,
      trust_device: trustDevice,
    })
    applySessionPayload(data)
    return data
  } finally {
    endRequest()
  }
}

export async function setupTotpPending(setupToken: string) {
  const { data } = await authClient.post<{ qr_code_base64: string }>(
    '/api/auth/totp/setup-pending/',
    { setup_token: setupToken },
  )
  return data
}

export async function setupTotpSession() {
  const setupToken = useAuthStore.getState().setupToken
  if (setupToken) {
    return setupTotpPending(setupToken)
  }
  const { data } = await authClient.post<{ qr_code_base64: string }>('/api/auth/totp/setup/')
  return data
}

export async function confirmTotpSetup(code: string) {
  const setupToken = useAuthStore.getState().setupToken
  if (setupToken) {
    const { data } = await authClient.post<LoginResponse & { backup_codes: string[] }>(
      '/api/auth/totp/confirm-pending/',
      { setup_token: setupToken, code },
    )
    useAuthStore.getState().setSetupToken(null)
    applySessionPayload(data)
    return data
  }
  const { data } = await authPost<LoginResponse & { backup_codes: string[] }>(
    '/api/auth/totp/confirm/',
    { code },
  )
  applySessionPayload(data)
  return data
}

export async function fetchTotpStatus() {
  const { data } = await authClient.get<{ enabled: boolean }>('/api/auth/totp/status/')
  return data
}

export async function acceptPrivacyPolicy(): Promise<AuthSessionPayload> {
  const setupToken = useAuthStore.getState().setupToken
  if (setupToken) {
    const { data } = await authClient.post<AuthSessionPayload>(
      '/api/auth/accept-privacy-pending/',
      { setup_token: setupToken },
    )
    applySessionPayload(data)
    return data
  }
  const { data } = await authPost<AuthSessionPayload>('/api/auth/accept-privacy/')
  applySessionPayload(data)
  return data
}

export async function restoreSession(): Promise<boolean> {
  const state = useAuthStore.getState()
  // Onboarding 2FA usa setup_token sem cookie JWT ainda
  if (state.setupToken && state.user && state.requiresTotpSetup) {
    return true
  }

  try {
    await fetchCsrfToken()
    const { data } = await authClient.get<AuthSessionPayload>('/api/auth/session/')
    applySessionPayload(data)
    return true
  } catch {
    return false
  }
}

export function isPendingSetupSession(): boolean {
  const state = useAuthStore.getState()
  return Boolean(state.setupToken && state.user && state.requiresTotpSetup)
}

export function clearAuthLocal() {
  useAuthStore.getState().logout()
}

export async function logout() {
  try {
    await authPost('/api/auth/logout/')
  } catch {
    // ignora falha remota
  }
  clearAuthLocal()
}
