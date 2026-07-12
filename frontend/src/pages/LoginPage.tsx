import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchLoginPrecheck,
  login,
  loginTotp,
  LoginError,
} from '@/services/auth'
import { useAuthStore } from '@/store/authStore'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'

declare global {
  interface Window {
    turnstile?: {
      render: (el: HTMLElement, options: Record<string, unknown>) => string
      reset: (widgetId: string) => void
      remove: (widgetId: string) => void
    }
  }
}

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [trustDevice, setTrustDevice] = useState(true)
  const [pendingToken, setPendingToken] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [requiresCaptcha, setRequiresCaptcha] = useState(false)
  const [turnstileSiteKey, setTurnstileSiteKey] = useState('')
  const captchaRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string | null>(null)
  const captchaTokenRef = useRef('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!username || username.length < 2) return
    const timer = setTimeout(async () => {
      try {
        const precheck = await fetchLoginPrecheck(username)
        setRequiresCaptcha(precheck.requires_captcha)
        setTurnstileSiteKey(precheck.turnstile_site_key || '')
      } catch {
        // ignora
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [username])

  useEffect(() => {
    if (!requiresCaptcha || !turnstileSiteKey || !captchaRef.current) return

    const scriptId = 'cf-turnstile-script'
    const renderWidget = () => {
      if (!window.turnstile || !captchaRef.current) return
      if (widgetIdRef.current) {
        window.turnstile.remove(widgetIdRef.current)
      }
      widgetIdRef.current = window.turnstile.render(captchaRef.current, {
        sitekey: turnstileSiteKey,
        callback: (token: string) => {
          captchaTokenRef.current = token
        },
      })
    }

    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script')
      script.id = scriptId
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
      script.async = true
      script.onload = renderWidget
      document.body.appendChild(script)
    } else {
      renderWidget()
    }

    return () => {
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current)
        widgetIdRef.current = null
      }
    }
  }, [requiresCaptcha, turnstileSiteKey])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (pendingToken) {
        await loginTotp(pendingToken, totpCode, trustDevice)
        navigate('/')
        return
      }
      await login(username, password, captchaTokenRef.current || undefined)
      if (useAuthStore.getState().requiresTotpSetup) {
        navigate('/onboarding', { replace: true })
      } else {
        navigate('/', { replace: true })
      }
    } catch (err) {
      if (err instanceof LoginError) {
        if (err.requiresTotp && err.pendingToken) {
          setPendingToken(err.pendingToken)
          setError('')
          return
        }
        setRequiresCaptcha(err.requiresCaptcha)
        setError(err.message)
      } else {
        setError('Credenciais inválidas ou acesso temporariamente bloqueado. Tente novamente mais tarde.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-wa-dark relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-wa-green/10 rounded-full blur-3xl animate-glow-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-wa-accent/10 rounded-full blur-3xl animate-glow-pulse" style={{ animationDelay: '2s' }} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="relative w-full max-w-sm glass-panel p-8 rounded-card shadow-glow-green-lg border border-wa-border/80 animate-slide-up"
      >
        <div className="flex items-center gap-3 mb-6">
          <img
            src="/branding/logo-weconnect.png"
            alt="WeConnect"
            className="h-12 w-auto shrink-0"
          />
          <div>
            <h1 className="text-2xl font-bold text-wa-green">WeConnect</h1>
            <p className="text-sm text-wa-muted">CRM WhatsApp</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-sm text-red-300 animate-fade-in">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {!pendingToken ? (
            <>
              <Input
                label="Usuário"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
              <Input
                label="Senha"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              {requiresCaptcha && turnstileSiteKey && (
                <div ref={captchaRef} className="flex justify-center" />
              )}
            </>
          ) : (
            <>
              <Input
                label="Código 2FA"
                type="text"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                required
                autoComplete="one-time-code"
                placeholder="000000"
              />
              <label className="flex items-start gap-2 text-xs text-wa-muted cursor-pointer">
                <input
                  type="checkbox"
                  checked={trustDevice}
                  onChange={(e) => setTrustDevice(e.target.checked)}
                  className="mt-0.5"
                />
                <span>
                  Confiar neste dispositivo por 30 dias (não pedir 2FA neste navegador).
                </span>
              </label>
            </>
          )}
        </div>

        <Button type="submit" loading={loading} className="w-full mt-6">
          {loading ? 'Entrando...' : pendingToken ? 'Validar 2FA' : 'Entrar'}
        </Button>

        <p className="mt-6 text-center text-[10px] text-wa-muted leading-relaxed">
          WeConnect · produto Aray Soluções Tecnológicas © 2026
        </p>
      </form>
    </div>
  )
}
