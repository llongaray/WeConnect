import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Headphones, Pencil, Plus, ShieldCheck, Trash2, Users } from 'lucide-react'
import { fetchCompany } from '@/services/companies'
import { createUser, deleteUser, fetchUsers, updateUser, type UserQueryParams } from '@/services/users'
import { getActiveCompanyId, needsPlatformCompanyScope } from '@/lib/companyContext'
import { confirmDialog } from '@/lib/confirmDialog'
import type { User } from '@/types'
import { useAuthStore } from '@/store/authStore'
import UsageDashboard from '@/components/admin/UsageDashboard'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import PageHeader from '@/components/ui/PageHeader'
import Select from '@/components/ui/Select'
import { SkeletonList } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'

type UsersTab = 'collaborators' | 'platform'
type PlatformType = 'superuser' | 'support'

const emptyForm = {
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  cpf: '',
  phone: '',
  role: 'atendente' as User['role'],
}

const platformTypeOptions: Array<{
  value: PlatformType
  label: string
  description: string
  icon: typeof ShieldCheck
}> = [
  {
    value: 'superuser',
    label: 'Superuser',
    description: 'Acesso total à plataforma, incluindo auditoria e segurança.',
    icon: ShieldCheck,
  },
  {
    value: 'support',
    label: 'Suporte WeConnect',
    description: 'Gerencia empresas e operações, sem acesso a auditoria e segurança. Exige 2FA.',
    icon: Headphones,
  },
]

function isSupportUser(user: Pick<User, 'is_staff' | 'is_superuser'>) {
  return Boolean(user.is_staff && !user.is_superuser)
}

function roleLabel(role: User['role'], user?: Pick<User, 'is_staff' | 'is_superuser'>) {
  if (user?.is_superuser) return 'Superuser'
  if (user && isSupportUser(user)) return 'Suporte WeConnect'
  if (role === 'gestor') return 'Gestor'
  if (role === 'supervisor') return 'Supervisor'
  return 'Atendente'
}

function roleBadgeVariant(user: User): 'info' | 'warning' | 'default' {
  if (user.is_superuser) return 'info'
  if (isSupportUser(user)) return 'warning'
  if (user.role === 'gestor') return 'info'
  if (user.role === 'supervisor') return 'warning'
  return 'default'
}

function getErrorMessage(err: unknown) {
  const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data
  if (!data) return 'Não foi possível salvar o usuário.'
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  if (Array.isArray(firstValue) && firstValue[0]) return String(firstValue[0])
  if (typeof firstValue === 'string') return firstValue
  return 'Não foi possível salvar o usuário.'
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient()
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const isGestor = useAuthStore((s) => s.isGestor())
  const selectedCompanyId = useAuthStore((s) => s.selectedCompanyId)
  const platformScope = needsPlatformCompanyScope()
  const [activeTab, setActiveTab] = useState<UsersTab>('collaborators')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<User['role'] | ''>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)
  const [platformType, setPlatformType] = useState<PlatformType>('superuser')
  const [form, setForm] = useState(emptyForm)
  const [feedback, setFeedback] = useState('')
  const [error, setError] = useState('')

  const companyId = getActiveCompanyId()
  const isPlatformTab = isSuperUser && activeTab === 'platform'

  const queryParams = useMemo<UserQueryParams>(() => {
    if (isPlatformTab) {
      return {
        scope: 'platform',
        ...(search ? { search } : {}),
      }
    }

    return {
      ...(search ? { search } : {}),
      ...(roleFilter ? { role: roleFilter } : {}),
      ...(platformScope && selectedCompanyId ? { company_id: selectedCompanyId } : {}),
    }
  }, [isPlatformTab, search, roleFilter, platformScope, selectedCompanyId])

  const canFetchUsers = isPlatformTab || !platformScope || Boolean(companyId)

  const { data, isLoading } = useQuery({
    queryKey: ['users', queryParams],
    queryFn: () => fetchUsers(queryParams),
    enabled: canFetchUsers,
  })

  const { data: companyData } = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompany(companyId!),
    enabled: Boolean(companyId) && !isPlatformTab,
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        cpf: form.cpf,
        phone: form.phone,
        role: form.role,
      }

      if (isPlatformTab) {
        if (!editing) {
          payload.platform_type = platformType
          if (platformType === 'superuser') {
            payload.is_superuser = true
          }
        }
      } else if (platformScope && companyId) {
        payload.company_id = companyId
      }

      if (form.password) payload.password = form.password
      if (editing) return updateUser(editing.id, payload)
      payload.password = form.password
      return createUser(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['company'] })
      setModalOpen(false)
      setEditing(null)
      setForm(emptyForm)
      setPlatformType('superuser')
      setFeedback(editing ? 'Usuário atualizado.' : 'Usuário criado.')
      setError('')
    },
    onError: (err: unknown) => setError(getErrorMessage(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['company'] })
      setFeedback('Usuário excluído.')
    },
  })

  const users = canFetchUsers ? data?.results || [] : []
  const usage = companyData?.usage
  const canCreate = isPlatformTab || !platformScope || Boolean(companyId)

  const openCreate = () => {
    setEditing(null)
    setPlatformType('superuser')
    setForm({
      ...emptyForm,
      role: isPlatformTab ? 'gestor' : 'atendente',
    })
    setError('')
    setModalOpen(true)
  }

  const openEdit = (user: User) => {
    setEditing(user)
    setPlatformType(user.is_superuser ? 'superuser' : 'support')
    setForm({
      username: user.username,
      password: '',
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      cpf: user.cpf,
      phone: user.phone,
      role: user.role,
    })
    setError('')
    setModalOpen(true)
  }

  const roleOptions: User['role'][] = isGestor && !isSuperUser
    ? ['atendente', 'supervisor']
    : ['atendente', 'supervisor', 'gestor']

  const emptyTitle = isPlatformTab ? 'Nenhum usuário da plataforma' : 'Nenhum usuário'
  const emptyDescription = isPlatformTab
    ? 'Cadastre superusuários ou usuários de suporte técnico WeConnect.'
    : platformScope && !companyId
      ? 'Selecione uma empresa para listar e criar usuários.'
      : 'Cadastre usuários para a empresa.'

  const modalTitle = editing
    ? 'Editar usuário'
    : isPlatformTab
      ? 'Novo usuário da plataforma'
      : 'Novo usuário'

  const modalDescription = editing
    ? isPlatformTab
      ? 'Atualize os dados do usuário da plataforma. O tipo de acesso não pode ser alterado.'
      : 'Atualize os dados do colaborador.'
    : isPlatformTab
      ? 'Escolha o tipo de acesso e preencha as credenciais do novo usuário.'
      : 'Preencha os dados do novo colaborador da empresa.'

  const submitLabel = editing
    ? 'Salvar alterações'
    : isPlatformTab
      ? platformType === 'support'
        ? 'Criar suporte'
        : 'Criar superuser'
      : 'Criar usuário'

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Usuários"
        description="Gerencie colaboradores das empresas e usuários internos da plataforma WeConnect."
        actions={
          <Button onClick={openCreate} disabled={!canCreate}>
            <Plus className="w-4 h-4" />
            {isPlatformTab ? 'Novo usuário da plataforma' : 'Novo usuário'}
          </Button>
        }
      />

      {isSuperUser && (
        <div className="flex flex-wrap gap-2 mb-6">
          <Button
            variant={activeTab === 'collaborators' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('collaborators')}
          >
            <Users className="w-4 h-4" />
            Colaboradores
          </Button>
          <Button
            variant={activeTab === 'platform' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('platform')}
          >
            <ShieldCheck className="w-4 h-4" />
            Usuários da plataforma
          </Button>
        </div>
      )}

      {!isPlatformTab && <UsageDashboard usage={usage} only="users" />}

      {feedback && (
        <div className="mb-4 p-3 rounded-lg bg-wa-green/10 border border-wa-green/30 text-sm text-wa-green">{feedback}</div>
      )}

      <Card className="mb-4 p-4">
        <div className={cn('grid grid-cols-1 gap-3', isPlatformTab ? 'md:grid-cols-1' : 'md:grid-cols-3')}>
          <Input
            label="Buscar"
            placeholder="Nome, usuário ou e-mail"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {!isPlatformTab && (
            <Select label="Papel" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value as User['role'] | '')}>
              <option value="">Todos os papéis</option>
              <option value="gestor">Gestor</option>
              <option value="supervisor">Supervisor</option>
              <option value="atendente">Atendente</option>
            </Select>
          )}
        </div>
      </Card>

      {isLoading && <SkeletonList count={5} />}

      {!isLoading && users.length === 0 && (
        <EmptyState icon={isPlatformTab ? ShieldCheck : Users} title={emptyTitle} description={emptyDescription} />
      )}

      {users.length > 0 && (
        <div className="overflow-x-auto rounded-card border border-wa-border">
          <table className="w-full text-sm">
            <thead className="bg-wa-panel/80 text-wa-muted">
              <tr>
                <th className="text-left p-3">Usuário</th>
                <th className="text-left p-3">Contato</th>
                <th className="text-left p-3">Empresa</th>
                <th className="text-left p-3">Papel</th>
                <th className="text-left p-3">Status</th>
                <th className="text-right p-3">Ações</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t border-wa-border hover:bg-wa-panel/40">
                  <td className="p-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={user.first_name || user.username} size="sm" />
                      <div>
                        <div className="font-medium">{user.first_name || user.username}</div>
                        <div className="text-xs text-wa-muted">@{user.username}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-3 text-wa-muted">
                    <div>{user.email || '—'}</div>
                    <div className="text-xs">{user.phone || '—'}</div>
                  </td>
                  <td className="p-3 text-wa-muted">
                    {user.company ? `${user.company.trade_name} (${user.company.code})` : 'Plataforma'}
                  </td>
                  <td className="p-3">
                    <Badge variant={roleBadgeVariant(user)}>
                      {roleLabel(user.role, user)}
                    </Badge>
                  </td>
                  <td className="p-3">
                    <Badge variant={user.is_active ? 'success' : 'danger'}>
                      {user.is_active ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </td>
                  <td className="p-3">
                    <div className="flex justify-end gap-2">
                      <Button variant="secondary" className="px-2 py-1" onClick={() => openEdit(user)}>
                        <Pencil className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="danger"
                        className="px-2 py-1"
                        onClick={async () => {
                          const ok = await confirmDialog({
                            title: 'Excluir usuário',
                            message: `Confirma a exclusão de ${user.first_name || user.username}?`,
                            confirmLabel: 'Excluir',
                            variant: 'danger',
                          })
                          if (ok) deleteMutation.mutate(user.id)
                        }}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={modalTitle}
        description={modalDescription}
        className="max-w-2xl"
      >
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault()
            saveMutation.mutate()
          }}
        >
          {isPlatformTab && !editing && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-3">
                Tipo de acesso
              </p>
              <div className="space-y-2">
                {platformTypeOptions.map((option) => {
                  const Icon = option.icon
                  return (
                    <label
                      key={option.value}
                      className={cn(
                        'flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-all duration-200',
                        platformType === option.value
                          ? 'border-wa-green bg-wa-green/10 shadow-glow-green/20'
                          : 'border-wa-border hover:border-gray-500',
                      )}
                    >
                      <input
                        type="radio"
                        name="platform_type"
                        value={option.value}
                        checked={platformType === option.value}
                        onChange={() => setPlatformType(option.value)}
                        className="mt-1 accent-wa-green"
                      />
                      <Icon className="w-5 h-5 text-wa-green shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">{option.label}</span>
                        <p className="text-xs text-wa-muted mt-0.5">{option.description}</p>
                      </div>
                    </label>
                  )
                })}
              </div>
            </div>
          )}

          {isPlatformTab && editing && (
            <div className="p-3 rounded-lg border border-wa-border bg-gray-800/40">
              <p className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-2">Tipo de acesso</p>
              <Badge variant={editing.is_superuser ? 'info' : 'warning'}>
                {roleLabel(editing.role, editing)}
              </Badge>
            </div>
          )}

          {!editing && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-3">
                Credenciais de acesso
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Usuário"
                  placeholder="login do usuário"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                  autoComplete="off"
                />
                <Input
                  label="Senha"
                  type="password"
                  placeholder="Senha inicial"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>
          )}

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-3">
              Dados pessoais
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Nome"
                placeholder="Primeiro nome"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
              <Input
                label="Sobrenome"
                placeholder="Sobrenome"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
              <Input
                label="E-mail"
                type="email"
                placeholder="opcional"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
              <Input
                label="Telefone"
                placeholder="opcional"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
              <Input
                label="CPF"
                placeholder="opcional"
                value={form.cpf}
                onChange={(e) => setForm({ ...form, cpf: e.target.value })}
                className="sm:col-span-2"
              />
            </div>
          </div>

          {!isPlatformTab && (
            <Select
              label="Papel na empresa"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as User['role'] })}
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>{roleLabel(role)}</option>
              ))}
            </Select>
          )}

          {editing && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-3">
                Segurança
              </p>
              <Input
                label="Nova senha"
                type="password"
                placeholder="Deixe em branco para manter a atual"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                autoComplete="new-password"
              />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-300 bg-red-950/30 border border-red-500/30 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex gap-2 justify-end pt-2 border-t border-wa-border">
            <Button type="button" variant="ghost" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={saveMutation.isPending}>
              {submitLabel}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
