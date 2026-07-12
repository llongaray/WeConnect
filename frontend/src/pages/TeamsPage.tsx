import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ChevronDown,
  MoreVertical,
  Plus,
  Radio,
  Trash2,
  UserPlus,
  UsersRound,
  UserX,
} from 'lucide-react'
import { fetchCompany } from '@/services/companies'
import { fetchChannels } from '@/services/channels'
import {
  addTeamMember,
  createTeam,
  deleteTeam,
  fetchTeams,
  removeTeamMember,
  setTeamDefaultChannel,
} from '@/services/teams'
import { fetchUsers } from '@/services/users'
import type { Team, User } from '@/types'
import { getActiveCompanyId, needsPlatformCompanyScope } from '@/lib/companyContext'
import { confirmDialog } from '@/lib/confirmDialog'
import { cn } from '@/lib/cn'
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

type MemberRole = 'atendente' | 'supervisor'

interface MemberDraft {
  userId: string
  role: MemberRole
}

const emptyMemberDraft: MemberDraft = { userId: '', role: 'atendente' }

function roleLabel(role: MemberRole) {
  return role === 'supervisor' ? 'Supervisor' : 'Atendente'
}

export default function TeamsPage() {
  const queryClient = useQueryClient()
  const companyId = getActiveCompanyId()
  const platformScope = needsPlatformCompanyScope()
  const hasCompanyScope = !platformScope || Boolean(companyId)

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [expandedTeamId, setExpandedTeamId] = useState<number | null>(null)
  const [openMenuId, setOpenMenuId] = useState<number | null>(null)
  const [createForm, setCreateForm] = useState({ name: '', channelId: '' })
  const [memberDrafts, setMemberDrafts] = useState<Record<number, MemberDraft>>({})

  const { data: teamsData, isLoading } = useQuery({
    queryKey: ['teams', companyId],
    queryFn: fetchTeams,
    enabled: hasCompanyScope,
  })

  const { data: channelsData } = useQuery({
    queryKey: ['channels', companyId],
    queryFn: () => fetchChannels({ companyId }),
    enabled: hasCompanyScope,
  })

  const { data: usersData } = useQuery({
    queryKey: ['users', companyId],
    queryFn: () => fetchUsers(platformScope && companyId ? { company_id: companyId } : undefined),
    enabled: hasCompanyScope,
  })

  const { data: companyData } = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompany(companyId!),
    enabled: Boolean(companyId),
  })

  const invalidateTeams = () => {
    queryClient.invalidateQueries({ queryKey: ['teams'] })
    queryClient.invalidateQueries({ queryKey: ['company'] })
  }

  const createMutation = useMutation({
    mutationFn: createTeam,
    onSuccess: () => {
      invalidateTeams()
      setCreateForm({ name: '', channelId: '' })
      setShowCreateModal(false)
    },
  })

  const addMemberMutation = useMutation({
    mutationFn: ({
      teamId,
      userId,
      role,
    }: {
      teamId: number
      userId: number
      role: MemberRole
    }) => addTeamMember(teamId, userId, role),
    onSuccess: (_, variables) => {
      invalidateTeams()
      setMemberDrafts((prev) => ({
        ...prev,
        [variables.teamId]: emptyMemberDraft,
      }))
    },
  })

  const removeMemberMutation = useMutation({
    mutationFn: ({ teamId, userId }: { teamId: number; userId: number }) =>
      removeTeamMember(teamId, userId),
    onSuccess: invalidateTeams,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTeam,
    onSuccess: () => {
      setExpandedTeamId(null)
      invalidateTeams()
    },
  })

  const defaultChannelMutation = useMutation({
    mutationFn: ({ teamId, channelId }: { teamId: number; channelId: number }) =>
      setTeamDefaultChannel(teamId, channelId),
    onSuccess: invalidateTeams,
  })

  useEffect(() => {
    const closeMenu = () => setOpenMenuId(null)
    if (openMenuId !== null) {
      document.addEventListener('click', closeMenu)
      return () => document.removeEventListener('click', closeMenu)
    }
  }, [openMenuId])

  const teams = teamsData?.results || []
  const channels = channelsData || []
  const users = usersData?.results || []
  const usage = companyData?.usage

  const getMemberDraft = (teamId: number): MemberDraft => memberDrafts[teamId] ?? emptyMemberDraft

  const updateMemberDraft = (teamId: number, patch: Partial<MemberDraft>) => {
    setMemberDrafts((prev) => ({
      ...prev,
      [teamId]: { ...getMemberDraft(teamId), ...patch },
    }))
  }

  const availableUsersForTeam = (team: Team) => {
    const memberIds = new Set(team.memberships.map((m) => m.user.id))
    return users.filter((user: User) => !memberIds.has(user.id))
  }

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!companyId || !createForm.name.trim()) return
    createMutation.mutate({
      name: createForm.name.trim(),
      channel_ids: createForm.channelId ? [Number(createForm.channelId)] : [],
      company_id: companyId,
    })
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Equipes"
        description="Organize atendentes e supervisores por canal de atendimento."
        actions={
          <Button onClick={() => setShowCreateModal(true)} disabled={!hasCompanyScope}>
            <Plus className="w-4 h-4" />
            Nova equipe
          </Button>
        }
      />

      <UsageDashboard usage={usage} only="teams" />

      <Modal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Nova equipe"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Nome da equipe"
            placeholder="Ex: Atendimento Comercial"
            value={createForm.name}
            onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            required
          />
          <Select
            label="Canal vinculado (opcional)"
            value={createForm.channelId}
            onChange={(e) => setCreateForm({ ...createForm, channelId: e.target.value })}
          >
            <option value="">Nenhum canal</option>
            {channels.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.name}
              </option>
            ))}
          </Select>
          <div className="flex gap-2 justify-end pt-2">
            <Button type="button" variant="ghost" onClick={() => setShowCreateModal(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={createMutation.isPending} disabled={!createForm.name.trim()}>
              Criar equipe
            </Button>
          </div>
        </form>
      </Modal>

      {isLoading && <SkeletonList count={3} />}

      {!isLoading && teams.length === 0 && (
        <EmptyState
          icon={UsersRound}
          title="Nenhuma equipe"
          description="Crie equipes para organizar o atendimento por canal."
          action={
            <Button onClick={() => setShowCreateModal(true)} disabled={!hasCompanyScope}>
              <Plus className="w-4 h-4" />
              Criar equipe
            </Button>
          }
        />
      )}

      <div className="space-y-3 max-w-4xl">
        {teams.map((team: Team, index) => {
          const isExpanded = expandedTeamId === team.id
          const memberDraft = getMemberDraft(team.id)
          const availableUsers = availableUsersForTeam(team)

          return (
            <div
              key={team.id}
              className={cn(
                'relative rounded-card border bg-wa-panel transition-all duration-200 animate-fade-in',
                isExpanded ? 'border-wa-green shadow-panel' : 'border-wa-border hover:border-gray-600',
              )}
              style={{ animationDelay: `${index * 40}ms` }}
            >
              <button
                type="button"
                onClick={() => {
                  setExpandedTeamId(isExpanded ? null : team.id)
                  setOpenMenuId(null)
                }}
                className="w-full text-left p-4 pr-14"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <UsersRound className="w-4 h-4 text-wa-green shrink-0" />
                      <p className="font-medium">{team.name}</p>
                    </div>
                    <p className="text-sm text-wa-muted mt-1">
                      {team.members_count} {team.members_count === 1 ? 'membro' : 'membros'}
                    </p>
                    {team.channels.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {team.channels.map((ch) => (
                          <Badge key={ch.id} variant="info">
                            <Radio className="w-3 h-3 mr-1" />
                            {ch.name}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant={team.is_active ? 'success' : 'default'}>
                      {team.is_active ? 'Ativa' : 'Inativa'}
                    </Badge>
                    <ChevronDown
                      className={cn(
                        'w-5 h-5 text-wa-muted transition-transform duration-200',
                        isExpanded && 'rotate-180',
                      )}
                    />
                  </div>
                </div>
              </button>

              <button
                type="button"
                aria-label={`Ações da equipe ${team.name}`}
                onClick={(event) => {
                  event.stopPropagation()
                  setOpenMenuId(openMenuId === team.id ? null : team.id)
                }}
                className="absolute right-3 top-3 p-2 rounded-lg text-wa-muted hover:text-white hover:bg-gray-700 transition-colors"
              >
                <MoreVertical className="w-5 h-5" />
              </button>

              {openMenuId === team.id && (
                <div
                  className="absolute right-3 top-12 z-20 min-w-[160px] overflow-hidden rounded-lg border border-wa-border bg-gray-800 shadow-xl"
                  onClick={(event) => event.stopPropagation()}
                >
                  <button
                    type="button"
                    onClick={async () => {
                      setOpenMenuId(null)
                      const ok = await confirmDialog({
                        title: 'Excluir equipe',
                        message: `Excluir a equipe "${team.name}"? Os membros não serão removidos do sistema.`,
                        confirmLabel: 'Excluir',
                        variant: 'danger',
                      })
                      if (ok) deleteMutation.mutate(team.id)
                    }}
                    className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:bg-red-900/20"
                  >
                    <Trash2 className="w-4 h-4" />
                    Excluir
                  </button>
                </div>
              )}

              {isExpanded && (
                <div className="border-t border-wa-border px-4 py-5 space-y-5 animate-fade-in">
                  {team.channels.length > 0 && (
                    <section>
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-2">
                        Canal padrão
                      </h4>
                      <Select
                        label="Canal usado por padrão nesta equipe"
                        value=""
                        onChange={(e) => {
                          if (e.target.value) {
                            defaultChannelMutation.mutate({
                              teamId: team.id,
                              channelId: Number(e.target.value),
                            })
                          }
                        }}
                        className="max-w-sm"
                      >
                        <option value="">Selecione um canal...</option>
                        {team.channels.map((ch) => (
                          <option key={ch.id} value={ch.id}>
                            {ch.name}
                          </option>
                        ))}
                      </Select>
                    </section>
                  )}

                  <section>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-3">
                      Membros ({team.members_count})
                    </h4>

                    {team.memberships.length === 0 ? (
                      <Card padding="md" className="text-center border-dashed border-wa-border bg-wa-dark/30">
                        <p className="text-sm text-wa-muted">Nenhum membro nesta equipe ainda.</p>
                      </Card>
                    ) : (
                      <div className="space-y-2">
                        {team.memberships.map((membership) => (
                          <div
                            key={membership.id}
                            className="flex items-center justify-between gap-3 p-3 rounded-lg bg-gray-800/50 border border-wa-border/60"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <Avatar name={membership.user.first_name || membership.user.username} size="sm" />
                              <div className="min-w-0">
                                <p className="text-sm font-medium truncate">
                                  {membership.user.first_name || membership.user.username}
                                </p>
                                <p className="text-xs text-wa-muted truncate">@{membership.user.username}</p>
                              </div>
                              <Badge variant={membership.role === 'supervisor' ? 'info' : 'default'}>
                                {roleLabel(membership.role)}
                              </Badge>
                            </div>
                            <Button
                              variant="ghost"
                              className="text-xs px-2 text-wa-muted hover:text-red-400 shrink-0"
                              onClick={async () => {
                                const name = membership.user.first_name || membership.user.username
                                const ok = await confirmDialog({
                                  title: 'Remover membro',
                                  message: `Remover ${name} da equipe "${team.name}"?`,
                                  confirmLabel: 'Remover',
                                  variant: 'danger',
                                })
                                if (ok) {
                                  removeMemberMutation.mutate({
                                    teamId: team.id,
                                    userId: membership.user.id,
                                  })
                                }
                              }}
                            >
                              <UserX className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>

                  <section>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-wa-muted mb-3 flex items-center gap-2">
                      <UserPlus className="w-3.5 h-3.5" />
                      Adicionar membro
                    </h4>

                    {availableUsers.length === 0 ? (
                      <p className="text-sm text-wa-muted">
                        Todos os usuários da empresa já fazem parte desta equipe.
                      </p>
                    ) : (
                      <form
                        className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-2 items-end"
                        onSubmit={(e) => {
                          e.preventDefault()
                          if (!memberDraft.userId) return
                          addMemberMutation.mutate({
                            teamId: team.id,
                            userId: Number(memberDraft.userId),
                            role: memberDraft.role,
                          })
                        }}
                      >
                        <Select
                          label="Usuário"
                          value={memberDraft.userId}
                          onChange={(e) => updateMemberDraft(team.id, { userId: e.target.value })}
                        >
                          <option value="">Selecione...</option>
                          {availableUsers.map((user: User) => (
                            <option key={user.id} value={user.id}>
                              {user.first_name || user.username} (@{user.username})
                            </option>
                          ))}
                        </Select>
                        <Select
                          label="Papel"
                          value={memberDraft.role}
                          onChange={(e) =>
                            updateMemberDraft(team.id, {
                              role: e.target.value as MemberRole,
                            })
                          }
                          className="sm:w-44"
                        >
                          <option value="atendente">Atendente</option>
                          <option value="supervisor">Supervisor</option>
                        </Select>
                        <Button
                          type="submit"
                          loading={addMemberMutation.isPending}
                          disabled={!memberDraft.userId}
                          className="sm:mb-0"
                        >
                          Adicionar
                        </Button>
                      </form>
                    )}
                  </section>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
