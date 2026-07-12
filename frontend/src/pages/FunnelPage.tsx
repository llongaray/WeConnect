import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Filter, Pencil, Plus, Trash2 } from 'lucide-react'
import {
  createTag,
  deleteTag,
  fetchTags,
  updateTag,
} from '@/services/tags'
import type { Tag } from '@/types'
import { getActiveCompanyId, needsPlatformCompanyScope } from '@/lib/companyContext'
import { confirmDialog } from '@/lib/confirmDialog'
import { useAuthStore } from '@/store/authStore'
import CompanyScopePrompt from '@/components/admin/CompanyScopePrompt'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import PageHeader from '@/components/ui/PageHeader'
import { SkeletonList } from '@/components/ui/Skeleton'

interface TagFormState {
  name: string
  color: string
  funnel_order: string
  is_active: boolean
}

const emptyForm: TagFormState = {
  name: '',
  color: '#00A3FF',
  funnel_order: '1',
  is_active: true,
}

function nextFunnelOrder(tags: Tag[]): number {
  const orders = tags
    .map((tag) => tag.funnel_order)
    .filter((order) => order > 0)
  if (orders.length === 0) return 1
  return Math.max(...orders) + 1
}

export default function FunnelPage() {
  const queryClient = useQueryClient()
  const companyId = getActiveCompanyId()
  const platformScope = needsPlatformCompanyScope()
  const showScopePrompt = platformScope && !companyId
  const isGestor = useAuthStore((s) => s.isGestor())
  const isSuperUser = useAuthStore((s) => s.isSuperUser)
  const canManage = isGestor || isSuperUser

  const [showModal, setShowModal] = useState(false)
  const [editingTag, setEditingTag] = useState<Tag | null>(null)
  const [form, setForm] = useState<TagFormState>(emptyForm)
  const [error, setError] = useState('')

  const { data: allTags = [], isLoading: loadingTags } = useQuery({
    queryKey: ['tags', companyId, 'all'],
    queryFn: () => fetchTags(false),
    enabled: !showScopePrompt && canManage,
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        name: form.name.trim(),
        color: form.color,
        funnel_order: Number(form.funnel_order) || 0,
        is_active: form.is_active,
      }
      if (editingTag) return updateTag(editingTag.id, payload)
      return createTag(payload)
    },
    onSuccess: () => {
      setShowModal(false)
      setEditingTag(null)
      setForm(emptyForm)
      setError('')
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['tags/funnel'] })
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string; name?: string[] } } })?.response?.data
      setError(
        typeof detail?.detail === 'string'
          ? detail.detail
          : detail?.name?.[0] || 'Não foi possível salvar a tag.',
      )
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteTag(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['tags/funnel'] })
    },
  })

  if (showScopePrompt) {
    return (
      <CompanyScopePrompt
        title="Selecione uma empresa"
        description="Use o seletor de empresa no topo para configurar as etapas do funil."
      />
    )
  }

  if (!canManage) {
    return (
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <PageHeader
          title="Etapas do funil"
          description="Apenas gestores podem configurar as etapas e tags do funil."
        />
        <EmptyState
          icon={Filter}
          title="Sem permissão"
          description="Peça ao gestor da empresa para configurar as etapas do funil."
        />
      </div>
    )
  }

  const openCreate = () => {
    setEditingTag(null)
    setForm({
      ...emptyForm,
      funnel_order: String(nextFunnelOrder(allTags)),
    })
    setError('')
    setShowModal(true)
  }

  const openEdit = (tag: Tag) => {
    setEditingTag(tag)
    setForm({
      name: tag.name,
      color: tag.color,
      funnel_order: String(tag.funnel_order),
      is_active: tag.is_active,
    })
    setError('')
    setShowModal(true)
  }

  const handleDelete = async (tag: Tag) => {
    const confirmed = await confirmDialog({
      title: 'Excluir tag',
      message: `Remover a tag "${tag.name}"? As atribuições nos contatos também serão removidas.`,
      confirmLabel: 'Excluir',
      variant: 'danger',
    })
    if (confirmed) deleteMutation.mutate(tag.id)
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Etapas do funil"
        description="Crie e ordene as tags que formam as colunas do funil Kanban."
      />

      <Card className="p-4 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold">Tags da empresa</h2>
            <p className="text-sm text-wa-muted">
              Use ordem 1, 2, 3... para incluir a tag no funil. Ordem 0 fica fora do Kanban.
            </p>
          </div>
          <Button onClick={openCreate}>
            <Plus className="w-4 h-4 mr-1" />
            Nova tag
          </Button>
        </div>

        {loadingTags && <SkeletonList count={3} />}

        {!loadingTags && allTags.length === 0 && (
          <EmptyState
            icon={Filter}
            title="Nenhuma tag"
            description="Crie tags para classificar contatos e montar o funil."
          />
        )}

        {!loadingTags && allTags.length > 0 && (
          <div className="space-y-2">
            {allTags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center gap-3 p-3 rounded-lg border border-wa-border bg-gray-900/40"
              >
                <span
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: tag.color }}
                />
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{tag.name}</p>
                  <p className="text-xs text-wa-muted">
                    Ordem funil: {tag.funnel_order || 'fora do funil'}
                    {typeof tag.contacts_count === 'number' && ` · ${tag.contacts_count} contato(s)`}
                  </p>
                </div>
                {!tag.is_active && <Badge variant="default">Inativa</Badge>}
                <Button variant="secondary" className="px-2" onClick={() => openEdit(tag)}>
                  <Pencil className="w-4 h-4" />
                </Button>
                <Button
                  variant="secondary"
                  className="px-2 text-red-300 hover:text-red-200"
                  onClick={() => handleDelete(tag)}
                  loading={deleteMutation.isPending}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title={editingTag ? 'Editar tag' : 'Nova tag'}
      >
        <div className="space-y-3">
          <Input
            label="Nome"
            value={form.name}
            onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            maxLength={50}
          />
          <div>
            <label className="block text-sm text-wa-muted mb-1">Cor</label>
            <input
              type="color"
              value={form.color}
              onChange={(e) => setForm((prev) => ({ ...prev, color: e.target.value }))}
              className="h-10 w-full rounded-lg border border-wa-border bg-gray-800 cursor-pointer"
            />
          </div>
          <Input
            label="Ordem no funil (0 = fora do funil)"
            type="number"
            min={0}
            value={form.funnel_order}
            onChange={(e) => setForm((prev) => ({ ...prev, funnel_order: e.target.value }))}
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))}
              className="rounded border-wa-border"
            />
            Tag ativa
          </label>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancelar
            </Button>
            <Button
              onClick={() => saveMutation.mutate()}
              loading={saveMutation.isPending}
              disabled={!form.name.trim()}
            >
              Salvar
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
