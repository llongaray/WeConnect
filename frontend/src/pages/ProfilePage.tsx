import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  Copy,
  KeyRound,
  Mail,
  Phone,
  ShieldCheck,
  User,
} from 'lucide-react'
import {
  confirmTotpSetup,
  fetchTotpStatus,
  setupTotpSession,
} from '@/services/auth'
import { fetchProfile, updateProfile } from '@/services/profile'
import { useAuthStore } from '@/store/authStore'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Skeleton from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'

function roleLabel(role?: string, isSuperUser?: boolean) {
  if (isSuperUser) return 'Superuser'
  if (role === 'gestor') return 'Gestor'
  if (role === 'supervisor') return 'Supervisor'
  return 'Atendente'
}

const totpSteps = [
  { id: 1, title: 'Gerar QR Code', description: 'Clique no botão abaixo' },
  { id: 2, title: 'Escanear', description: 'Use Google Authenticator ou similar' },
  { id: 3, title: 'Confirmar', description: 'Informe o código de 6 dígitos' },
]

export default function ProfilePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const setSessionFlags = useAuthStore((s) => s.setSessionFlags)
  const setAuth = useAuthStore((s) => s.setAuth)
  const requiresTotpSetup = useAuthStore((s) => s.requiresTotpSetup)
  const totpEnabledStore = useAuthStore((s) => s.totpEnabled)
  const storeUser = useAuthStore((s) => s.user)

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
  })
  const [qrCode, setQrCode] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [totpError, setTotpError] = useState('')
  const [profileError, setProfileError] = useState('')
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [qrLoading, setQrLoading] = useState(false)
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: fetchProfile,
    enabled: !requiresTotpSetup,
  })

  const { data: totpStatus } = useQuery({
    queryKey: ['totp-status'],
    queryFn: fetchTotpStatus,
    enabled: !requiresTotpSetup,
  })

  const activeProfile = profile ?? storeUser

  const totpActive = totpEnabledStore || totpStatus?.enabled
  const hasBackupCodes = backupCodes.length > 0
  const showProtectedState = totpActive && !requiresTotpSetup && !hasBackupCodes
  const showSetupFlow = requiresTotpSetup || !totpActive || hasBackupCodes
  const displayName = activeProfile?.first_name || activeProfile?.username || 'Usuário'
  const totpStep = hasBackupCodes ? 4 : !qrCode ? 1 : totpCode.trim() ? 3 : 2

  useEffect(() => {
    if (profile) {
      setForm({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        phone: profile.phone || '',
      })
    }
  }, [profile])

  const profileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: (data) => {
      const state = useAuthStore.getState()
      setAuth(data, state.isSuperUser, {
        requiresTotpSetup: state.requiresTotpSetup,
        totpEnabled: state.totpEnabled,
        accessMode: state.accessMode,
      })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      setProfileError('')
      setProfileSuccess(true)
      setTimeout(() => setProfileSuccess(false), 3000)
    },
    onError: () => setProfileError('Não foi possível salvar o perfil.'),
  })

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault()
    profileMutation.mutate(form)
  }

  const handleGenerateQr = async () => {
    setQrLoading(true)
    setTotpError('')
    try {
      const data = await setupTotpSession()
      setQrCode(data.qr_code_base64)
    } catch {
      setTotpError('Não foi possível gerar o QR Code. Tente novamente.')
    } finally {
      setQrLoading(false)
    }
  }

  const handleConfirmTotp = async (e: React.FormEvent) => {
    e.preventDefault()
    setConfirmLoading(true)
    setTotpError('')
    try {
      const result = await confirmTotpSetup(totpCode)
      setBackupCodes(result.backup_codes || [])
      if (result.user) {
        setAuth(result.user, Boolean(result.is_superuser), {
          requiresTotpSetup: false,
          totpEnabled: true,
          accessMode: 'full',
        })
      } else {
        setSessionFlags({
          requiresTotpSetup: false,
          totpEnabled: true,
          accessMode: 'full',
        })
      }
      queryClient.invalidateQueries({ queryKey: ['totp-status'] })
    } catch {
      setTotpError('Código inválido. Verifique o app autenticador e tente novamente.')
    } finally {
      setConfirmLoading(false)
    }
  }

  const copyBackupCodes = async () => {
    try {
      await navigator.clipboard.writeText(backupCodes.join('\n'))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard indisponível */
    }
  }

  if (isLoading) {
    return (
      <div className="h-full p-4 sm:p-6 overflow-y-auto">
        <div className="max-w-5xl mx-auto space-y-6">
          <Skeleton className="h-14 w-64" />
          <Skeleton className="h-28 w-full" />
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-80 w-full" />
            <Skeleton className="h-80 w-full" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full p-4 sm:p-6 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6">
        <PageHeader
          title="Meu perfil"
          description="Gerencie seus dados pessoais e a segurança da conta."
        />

        {requiresTotpSetup && (
          <div className="flex items-start gap-3 p-4 rounded-xl border border-amber-500/30 bg-amber-500/10">
            <ShieldCheck className="w-5 h-5 text-amber-300 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-100">Configuração de 2FA obrigatória</p>
              <p className="text-xs text-amber-200/80 mt-1">
                Para acessar o sistema completo, configure a autenticação em dois fatores abaixo.
              </p>
            </div>
          </div>
        )}

        <Card
          padding="lg"
          className="border-wa-green/20 bg-gradient-to-br from-wa-panel to-wa-dark/60"
        >
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <Avatar name={displayName} size="lg" className="w-16 h-16 text-lg" />
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold text-white truncate">{displayName}</h2>
                <Badge variant={isSuperUser || activeProfile?.role === 'gestor' ? 'info' : 'default'}>
                  {roleLabel(activeProfile?.role, isSuperUser)}
                </Badge>
                <Badge variant={totpActive ? 'success' : 'warning'}>
                  {totpActive ? '2FA ativo' : '2FA pendente'}
                </Badge>
              </div>
              <p className="text-sm text-wa-muted mt-1">@{activeProfile?.username}</p>
              {activeProfile?.email && (
                <p className="text-xs text-wa-muted mt-2 flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5" />
                  {activeProfile.email}
                </p>
              )}
            </div>
          </div>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
          <Card padding="lg" className="h-full">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                <User className="w-4 h-4 text-wa-green" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Dados pessoais</h3>
                <p className="text-xs text-wa-muted">Informações exibidas no sistema</p>
              </div>
            </div>

            {profileError && (
              <div className="mb-4 p-3 rounded-lg bg-red-900/30 border border-red-700/50 text-sm text-red-300">
                {profileError}
              </div>
            )}
            {profileSuccess && (
              <div className="mb-4 p-3 rounded-lg bg-sky-900/30 border border-sky-700/50 text-sm text-sky-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                Perfil atualizado com sucesso.
              </div>
            )}

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <Input
                label="Usuário"
                value={activeProfile?.username || ''}
                disabled
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Nome"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                />
                <Input
                  label="Sobrenome"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                />
              </div>
              <Input
                label="E-mail"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
              <Input
                label="Telefone"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="(00) 00000-0000"
              />
              <div className="pt-2 border-t border-wa-border/60">
                <Button type="submit" loading={profileMutation.isPending}>
                  Salvar alterações
                </Button>
              </div>
            </form>
          </Card>

          <Card
            padding="lg"
            className={cn(
              'h-full',
              showSetupFlow && requiresTotpSetup && 'border-wa-green/25',
            )}
          >
            <div className="flex items-center gap-2 mb-5">
              <div className="w-8 h-8 rounded-lg bg-wa-green/15 flex items-center justify-center">
                <KeyRound className="w-4 h-4 text-wa-green" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Segurança</h3>
                <p className="text-xs text-wa-muted">Autenticação em dois fatores (2FA)</p>
              </div>
            </div>

            {showProtectedState ? (
              <div className="rounded-xl border border-sky-700/40 bg-sky-900/20 p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-sky-400 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-sky-200">Conta protegida</p>
                    <p className="text-xs text-sky-300/80 mt-1 leading-relaxed">
                      A autenticação em dois fatores está ativa. No login, será solicitado o código
                      do app autenticador.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {totpError && (
                  <div className="mb-4 p-3 rounded-lg bg-red-900/30 border border-red-700/50 text-sm text-red-300">
                    {totpError}
                  </div>
                )}

                {hasBackupCodes ? (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-sky-700/40 bg-sky-900/20 p-4">
                      <p className="text-sm font-medium text-sky-200 mb-1">2FA ativado com sucesso</p>
                      <p className="text-xs text-sky-300/80">
                        Guarde os códigos de backup abaixo. Cada um pode ser usado apenas uma vez.
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                      {backupCodes.map((item) => (
                        <div
                          key={item}
                          className="p-2.5 bg-wa-dark rounded-lg border border-wa-border text-center"
                        >
                          {item}
                        </div>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={() => void copyBackupCodes()}>
                        <Copy className="w-4 h-4" />
                        {copied ? 'Copiado!' : 'Copiar códigos'}
                      </Button>
                      <Button onClick={() => navigate('/')}>Acessar o sistema</Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5">
                    <ol className="grid gap-2 sm:grid-cols-3">
                      {totpSteps.map((step) => (
                        <li
                          key={step.id}
                          className={cn(
                            'rounded-lg border p-3 transition-colors',
                            totpStep === step.id
                              ? 'border-wa-green/50 bg-wa-green/10'
                              : totpStep > step.id
                                ? 'border-wa-border/60 bg-wa-dark/40 opacity-80'
                                : 'border-wa-border/40 bg-wa-dark/20',
                          )}
                        >
                          <span
                            className={cn(
                              'inline-flex w-6 h-6 items-center justify-center rounded-full text-xs font-bold mb-2',
                              totpStep >= step.id
                                ? 'bg-wa-green text-white'
                                : 'bg-wa-border text-wa-muted',
                            )}
                          >
                            {totpStep > step.id ? '✓' : step.id}
                          </span>
                          <p className="text-xs font-medium text-white">{step.title}</p>
                          <p className="text-[11px] text-wa-muted mt-0.5">{step.description}</p>
                        </li>
                      ))}
                    </ol>

                    {!qrCode ? (
                      <Button onClick={() => void handleGenerateQr()} loading={qrLoading} className="w-full sm:w-auto">
                        Gerar QR Code
                      </Button>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex flex-col items-center p-4 rounded-xl bg-wa-dark/50 border border-wa-border">
                          <img
                            src={`data:image/png;base64,${qrCode}`}
                            alt="QR Code 2FA"
                            className="w-44 h-44 rounded-lg bg-white p-2"
                          />
                          <p className="text-xs text-wa-muted mt-3 text-center max-w-xs">
                            Escaneie com Google Authenticator, Authy ou outro app compatível.
                          </p>
                        </div>
                        <form onSubmit={handleConfirmTotp} className="space-y-4">
                          <Input
                            label="Código do autenticador"
                            value={totpCode}
                            onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            required
                            placeholder="000000"
                            autoComplete="one-time-code"
                            inputMode="numeric"
                            maxLength={6}
                            className="font-mono tracking-widest text-center text-lg"
                          />
                          <Button
                            type="submit"
                            loading={confirmLoading}
                            className="w-full"
                            disabled={totpCode.trim().length !== 6}
                          >
                            Confirmar e ativar 2FA
                          </Button>
                        </form>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </Card>
        </div>

        {(activeProfile?.phone || activeProfile?.email) && (
          <p className="text-xs text-wa-muted text-center flex items-center justify-center gap-3 flex-wrap pb-2">
            {activeProfile.email && (
              <span className="inline-flex items-center gap-1">
                <Mail className="w-3 h-3" />
                {activeProfile.email}
              </span>
            )}
            {activeProfile.phone && (
              <span className="inline-flex items-center gap-1">
                <Phone className="w-3 h-3" />
                {activeProfile.phone}
              </span>
            )}
          </p>
        )}
      </div>
    </div>
  )
}
