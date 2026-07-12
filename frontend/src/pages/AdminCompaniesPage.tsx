import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  Building2,
  Copy,
  Eye,
  Pencil,
  Plus,
  Power,
  Search,
  UserPlus,
} from 'lucide-react'
import {
  createCompany,
  createCompanyGestor,
  fetchAuditLogs,
  fetchCompanies,
  lookupCompanyCnpj,
  updateCompany,
} from '@/services/companies'
import type { Company } from '@/types'
import { formatCnpjInput, isValidCnpjLength, normalizeCnpj } from '@/lib/cnpj'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonList } from '@/components/ui/Skeleton'

const emptyCompanyForm = {
  legal_name: '',
  trade_name: '',
  cnpj: '',
  address: '',
  contact_email: '',
  billing_email: '',
  contact_phone: '',
  billing_phone: '',
  max_supervisors: 5,
  max_atendentes: 20,
  max_teams: 10,
  max_channels: 5,
}

const emptyGestorForm = {
  username: '',
  password: '',
  first_name: '',
  email: '',
  cpf: '',
  phone: '',
}

function UsageCell({ current, max }: { current: number; max: number }) {
  const ratio = max > 0 ? current / max : 0
  const variant = ratio >= 1 ? 'danger' : ratio >= 0.8 ? 'warning' : 'default'
  return <Badge variant={variant}>{current}/{max}</Badge>
}

interface CompanyFormValues {
  legal_name: string
  trade_name: string
  cnpj: string
  address: string
  contact_email: string
  billing_email: string
  contact_phone: string
  billing_phone: string
  max_supervisors: number
  max_atendentes: number
  max_teams: number
  max_channels: number
}

function FormSection({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: ReactNode
}) {
  return (
    <section className="rounded-lg border border-wa-border bg-wa-dark/30 p-4 space-y-3">
      <div>
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        {description && <p className="text-xs text-wa-muted mt-1">{description}</p>}
      </div>
      {children}
    </section>
  )
}

function CompanyFormFields({
  values,
  onChange,
}: {
  values: CompanyFormValues
  onChange: (values: CompanyFormValues) => void
}) {
  const set = (patch: Partial<CompanyFormValues>) => onChange({ ...values, ...patch })
  const [lookupError, setLookupError] = useState('')
  const [lookupLoading, setLookupLoading] = useState(false)
  const lastLookupRef = useRef('')

  const runCnpjLookup = async (cnpj: string) => {
    if (!isValidCnpjLength(cnpj)) return

    const digits = normalizeCnpj(cnpj)
    if (lastLookupRef.current === digits) return

    setLookupLoading(true)
    setLookupError('')
    try {
      const data = await lookupCompanyCnpj(cnpj)
      lastLookupRef.current = digits
      set({
        cnpj: data.cnpj,
        legal_name: data.legal_name || values.legal_name,
        trade_name: data.trade_name || values.trade_name,
        address: data.address || values.address,
        contact_email: data.contact_email || values.contact_email,
        contact_phone: data.contact_phone || values.contact_phone,
      })
    } catch (err) {
      lastLookupRef.current = ''
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        setLookupError(typeof detail === 'string' ? detail : 'Não foi possível consultar o CNPJ.')
      } else {
        setLookupError('Não foi possível consultar o CNPJ.')
      }
    } finally {
      setLookupLoading(false)
    }
  }

  useEffect(() => {
    if (!isValidCnpjLength(values.cnpj)) {
      lastLookupRef.current = ''
      return
    }

    const digits = normalizeCnpj(values.cnpj)
    if (lastLookupRef.current === digits) return

    const timer = setTimeout(() => {
      runCnpjLookup(values.cnpj)
    }, 700)

    return () => clearTimeout(timer)
  }, [values.cnpj])

  return (
    <div className="space-y-4 max-h-[65vh] overflow-y-auto pr-1">
      <FormSection
        title="Identificação"
        description="Informe o CNPJ para buscar razão social e nome fantasia automaticamente."
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-sm mb-1 text-gray-300">CNPJ</label>
            <div className="flex gap-2">
              <Input
                value={values.cnpj}
                onChange={(e) => {
                  setLookupError('')
                  set({ cnpj: formatCnpjInput(e.target.value) })
                }}
                onBlur={() => runCnpjLookup(values.cnpj)}
                placeholder="00.000.000/0000-00"
                className="flex-1"
              />
              <Button
                type="button"
                variant="secondary"
                loading={lookupLoading}
                disabled={!isValidCnpjLength(values.cnpj)}
                onClick={() => {
                  lastLookupRef.current = ''
                  runCnpjLookup(values.cnpj)
                }}
                className="shrink-0"
              >
                <Search className="w-4 h-4" />
                Buscar
              </Button>
            </div>
            {lookupLoading && (
              <p className="text-xs text-wa-muted mt-1">Consultando Receita Federal...</p>
            )}
            {lookupError && (
              <p className="text-xs text-red-400 mt-1">{lookupError}</p>
            )}
          </div>
          <Input
            label="Razão social *"
            value={values.legal_name}
            onChange={(e) => set({ legal_name: e.target.value })}
            required
          />
          <Input
            label="Nome fantasia *"
            value={values.trade_name}
            onChange={(e) => set({ trade_name: e.target.value })}
            required
          />
          <Input
            label="Endereço"
            value={values.address}
            onChange={(e) => set({ address: e.target.value })}
            placeholder="Rua, número, cidade — UF"
            className="sm:col-span-2"
          />
        </div>
      </FormSection>

      <FormSection
        title="Contato"
        description="Informações para suporte e faturamento."
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="E-mail de contato"
            type="email"
            value={values.contact_email}
            onChange={(e) => set({ contact_email: e.target.value })}
            placeholder="contato@empresa.com"
          />
          <Input
            label="E-mail financeiro"
            type="email"
            value={values.billing_email}
            onChange={(e) => set({ billing_email: e.target.value })}
            placeholder="financeiro@empresa.com"
          />
          <Input
            label="Telefone de contato"
            value={values.contact_phone}
            onChange={(e) => set({ contact_phone: e.target.value })}
            placeholder="(00) 00000-0000"
          />
          <Input
            label="Telefone financeiro"
            value={values.billing_phone}
            onChange={(e) => set({ billing_phone: e.target.value })}
            placeholder="(00) 00000-0000"
          />
        </div>
      </FormSection>

      <FormSection
        title="Licenças do plano"
        description="Defina quantos recursos esta empresa pode utilizar na plataforma."
      >
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Supervisores"
            type="number"
            min={1}
            value={values.max_supervisors}
            onChange={(e) => set({ max_supervisors: Number(e.target.value) })}
          />
          <Input
            label="Atendentes"
            type="number"
            min={1}
            value={values.max_atendentes}
            onChange={(e) => set({ max_atendentes: Number(e.target.value) })}
          />
          <Input
            label="Equipes"
            type="number"
            min={1}
            value={values.max_teams}
            onChange={(e) => set({ max_teams: Number(e.target.value) })}
          />
          <Input
            label="Canais WhatsApp"
            type="number"
            min={1}
            value={values.max_channels}
            onChange={(e) => set({ max_channels: Number(e.target.value) })}
          />
        </div>
      </FormSection>
    </div>
  )
}

export default function AdminCompaniesPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [createOpen, setCreateOpen] = useState(false)
  const [editCompany, setEditCompany] = useState<Company | null>(null)
  const [gestorCompany, setGestorCompany] = useState<Company | null>(null)
  const [auditCompany, setAuditCompany] = useState<Company | null>(null)
  const [createdCode, setCreatedCode] = useState<string | null>(null)
  const [form, setForm] = useState(emptyCompanyForm)
  const [gestorForm, setGestorForm] = useState(emptyGestorForm)
  const [feedback, setFeedback] = useState('')

  useEffect(() => {
    if (searchParams.get('criar') === '1') {
      setCreateOpen(true)
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, setSearchParams])

  const { data, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: fetchCompanies,
  })

  const { data: auditData } = useQuery({
    queryKey: ['audit-logs', auditCompany?.id],
    queryFn: () => fetchAuditLogs({ company_id: auditCompany!.id }),
    enabled: Boolean(auditCompany),
  })

  const createMutation = useMutation({
    mutationFn: createCompany,
    onSuccess: (company) => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      setCreatedCode(company.code)
      setFeedback(`Empresa criada. Código: ${company.code}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      updateCompany(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      setEditCompany(null)
      setFeedback('Empresa atualizada.')
    },
  })

  const gestorMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      createCompanyGestor(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setGestorCompany(null)
      setGestorForm(emptyGestorForm)
      setFeedback('Gestor criado com sucesso.')
    },
  })

  const companies = data?.results || []

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Empresas"
        description="Gerencie tenants, limites, status e gestores da plataforma."
        actions={
          <Button onClick={() => { setCreateOpen(true); setCreatedCode(null); setForm(emptyCompanyForm) }}>
            <Plus className="w-4 h-4" />
            Nova empresa
          </Button>
        }
      />

      {feedback && (
        <div className="mb-4 p-3 rounded-lg bg-wa-green/10 border border-wa-green/30 text-sm text-wa-green">
          {feedback}
        </div>
      )}

      {isLoading && <SkeletonList count={4} />}

      {!isLoading && companies.length === 0 && (
        <EmptyState
          icon={Building2}
          title="Nenhuma empresa"
          description="Crie a primeira empresa tenant da plataforma."
        />
      )}

      <div className="overflow-x-auto rounded-card border border-wa-border">
        <table className="w-full text-sm">
          <thead className="bg-wa-panel/80 text-wa-muted">
            <tr>
              <th className="text-left p-3">Código</th>
              <th className="text-left p-3">Nome fantasia</th>
              <th className="text-left p-3">Status</th>
              <th className="text-left p-3">Supervisores</th>
              <th className="text-left p-3">Atendentes</th>
              <th className="text-left p-3">Equipes</th>
              <th className="text-left p-3">Canais</th>
              <th className="text-left p-3">Criada em</th>
              <th className="text-right p-3">Ações</th>
            </tr>
          </thead>
          <tbody>
            {companies.map((company) => (
              <tr key={company.id} className="border-t border-wa-border hover:bg-wa-panel/40">
                <td className="p-3 font-mono text-wa-green">{company.code}</td>
                <td className="p-3">
                  <div className="font-medium">{company.trade_name}</div>
                  <div className="text-xs text-wa-muted">{company.legal_name}</div>
                </td>
                <td className="p-3">
                  <Badge variant={company.is_active ? 'success' : 'danger'}>
                    {company.is_active ? 'Ativa' : 'Inativa'}
                  </Badge>
                </td>
                <td className="p-3">
                  <UsageCell current={company.usage.supervisors} max={company.usage.limits.max_supervisors} />
                </td>
                <td className="p-3">
                  <UsageCell current={company.usage.atendentes} max={company.usage.limits.max_atendentes} />
                </td>
                <td className="p-3">
                  <UsageCell current={company.usage.teams} max={company.usage.limits.max_teams} />
                </td>
                <td className="p-3">
                  <UsageCell current={company.usage.channels} max={company.usage.limits.max_channels} />
                </td>
                <td className="p-3 text-wa-muted">
                  {new Date(company.created_at).toLocaleDateString('pt-BR')}
                </td>
                <td className="p-3">
                  <div className="flex justify-end gap-2">
                    <Button variant="secondary" className="px-2 py-1" onClick={() => setEditCompany(company)}>
                      <Pencil className="w-3.5 h-3.5" />
                    </Button>
                    <Button variant="secondary" className="px-2 py-1" onClick={() => setGestorCompany(company)}>
                      <UserPlus className="w-3.5 h-3.5" />
                    </Button>
                    <Button variant="secondary" className="px-2 py-1" onClick={() => setAuditCompany(company)}>
                      <Eye className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="secondary"
                      className="px-2 py-1"
                      onClick={() =>
                        updateMutation.mutate({
                          id: company.id,
                          payload: { is_active: !company.is_active },
                        })
                      }
                    >
                      <Power className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Nova empresa" className="max-w-2xl">
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            createMutation.mutate(form)
          }}
        >
          <CompanyFormFields values={form} onChange={setForm} />

          {createdCode && (
            <Card className="flex items-center justify-between">
              <span className="text-sm">
                Código gerado: <strong className="font-mono text-wa-green">{createdCode}</strong>
              </span>
              <Button type="button" variant="secondary" onClick={() => navigator.clipboard.writeText(createdCode)}>
                <Copy className="w-4 h-4" />
              </Button>
            </Card>
          )}

          <div className="flex gap-2 justify-end pt-2 border-t border-wa-border">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={createMutation.isPending}>
              Criar empresa
            </Button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(editCompany)} onClose={() => setEditCompany(null)} title="Editar empresa" className="max-w-2xl">
        {editCompany && (
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault()
              updateMutation.mutate({
                id: editCompany.id,
                payload: {
                  legal_name: editCompany.legal_name,
                  trade_name: editCompany.trade_name,
                  cnpj: editCompany.cnpj,
                  address: editCompany.address,
                  contact_email: editCompany.contact_email,
                  billing_email: editCompany.billing_email,
                  contact_phone: editCompany.contact_phone,
                  billing_phone: editCompany.billing_phone,
                  max_supervisors: editCompany.max_supervisors,
                  max_atendentes: editCompany.max_atendentes,
                  max_teams: editCompany.max_teams,
                  max_channels: editCompany.max_channels,
                },
              })
            }}
          >
            <CompanyFormFields
              values={{
                legal_name: editCompany.legal_name,
                trade_name: editCompany.trade_name,
                cnpj: editCompany.cnpj,
                address: editCompany.address,
                contact_email: editCompany.contact_email,
                billing_email: editCompany.billing_email,
                contact_phone: editCompany.contact_phone,
                billing_phone: editCompany.billing_phone,
                max_supervisors: editCompany.max_supervisors,
                max_atendentes: editCompany.max_atendentes,
                max_teams: editCompany.max_teams,
                max_channels: editCompany.max_channels,
              }}
              onChange={(values) =>
                setEditCompany({
                  ...editCompany,
                  ...values,
                })
              }
            />

            <div className="flex gap-2 justify-end pt-2 border-t border-wa-border">
              <Button type="button" variant="secondary" onClick={() => setEditCompany(null)}>
                Cancelar
              </Button>
              <Button type="submit" loading={updateMutation.isPending}>
                Salvar alterações
              </Button>
            </div>
          </form>
        )}
      </Modal>

      <Modal open={Boolean(gestorCompany)} onClose={() => setGestorCompany(null)} title={`Criar gestor — ${gestorCompany?.trade_name ?? ''}`}>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            if (!gestorCompany) return
            gestorMutation.mutate({ id: gestorCompany.id, payload: gestorForm })
          }}
        >
          <FormSection title="Acesso" description="Credenciais do gestor responsável pela empresa.">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input label="Usuário *" value={gestorForm.username} onChange={(e) => setGestorForm({ ...gestorForm, username: e.target.value })} required />
              <Input label="Senha *" type="password" value={gestorForm.password} onChange={(e) => setGestorForm({ ...gestorForm, password: e.target.value })} required />
            </div>
          </FormSection>
          <FormSection title="Dados pessoais" description="Informações opcionais do gestor.">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input label="Nome" value={gestorForm.first_name} onChange={(e) => setGestorForm({ ...gestorForm, first_name: e.target.value })} />
              <Input label="E-mail" type="email" value={gestorForm.email} onChange={(e) => setGestorForm({ ...gestorForm, email: e.target.value })} />
              <Input label="CPF" value={gestorForm.cpf} onChange={(e) => setGestorForm({ ...gestorForm, cpf: e.target.value })} />
              <Input label="Telefone" value={gestorForm.phone} onChange={(e) => setGestorForm({ ...gestorForm, phone: e.target.value })} />
            </div>
          </FormSection>
          <div className="flex gap-2 justify-end pt-2 border-t border-wa-border">
            <Button type="button" variant="secondary" onClick={() => setGestorCompany(null)}>Cancelar</Button>
            <Button type="submit" loading={gestorMutation.isPending}>Criar gestor</Button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(auditCompany)} onClose={() => setAuditCompany(null)} title={`Auditoria — ${auditCompany?.trade_name ?? ''}`} className="max-w-3xl">
        <div className="max-h-96 overflow-y-auto space-y-2">
          {(auditData?.results || []).map((log) => (
            <Card key={log.id} padding="sm">
              <div className="flex justify-between gap-2 text-sm">
                <span className="font-medium">{log.action} · {log.entity_type}</span>
                <span className="text-wa-muted">{new Date(log.created_at).toLocaleString('pt-BR')}</span>
              </div>
              <p className="text-xs text-wa-muted mt-1">{log.entity_label || log.entity_id} — {log.actor_name}</p>
            </Card>
          ))}
          {(auditData?.results || []).length === 0 && (
            <p className="text-sm text-wa-muted">Nenhum registro de auditoria.</p>
          )}
        </div>
      </Modal>
    </div>
  )
}
