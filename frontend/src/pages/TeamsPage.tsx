import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, UsersRound } from 'lucide-react'
import { fetchChannels } from '@/services/channels'
import {
  addTeamMember,
  createTeam,
  deleteTeam,
  fetchTeams,
  removeTeamMember,
  setTeamDefaultChannel,
} from '@/services/teams'
import { fetchUsers } from '@/services/chat'
import type { Team } from '@/types'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Select from '@/components/ui/Select'
import { SkeletonList } from '@/components/ui/Skeleton'

export default function TeamsPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ name: '', channelId: '' })
  const [memberForm, setMemberForm] = useState({
    teamId: 0,
    userId: '',
    role: 'atendente' as 'atendente' | 'supervisor',
  })

  const { data: teamsData, isLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: fetchTeams,
  })

  const { data: channelsData } = useQuery({
    queryKey: ['channels'],
    queryFn: fetchChannels,
  })

  const { data: usersData } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  const createMutation = useMutation({
    mutationFn: createTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      setForm({ name: '', channelId: '' })
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
      role: 'atendente' | 'supervisor'
    }) => addTeamMember(teamId, userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  })

  const removeMemberMutation = useMutation({
    mutationFn: ({ teamId, userId }: { teamId: number; userId: number }) =>
      removeTeamMember(teamId, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTeam,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  })

  const defaultChannelMutation = useMutation({
    mutationFn: ({ teamId, channelId }: { teamId: number; channelId: number }) =>
      setTeamDefaultChannel(teamId, channelId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  })

  const teams = teamsData?.results || []
  const channels = channelsData || []
  const users = usersData?.results || []

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      name: form.name,
      channel_ids: form.channelId ? [Number(form.channelId)] : [],
    })
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Equipes"
        description="Organize atendentes e supervisores por canal de atendimento."
      />

      <Card padding="lg" className="mb-8 max-w-2xl border-wa-green/20">
        <div className="flex items-center gap-2 mb-4">
          <Plus className="w-5 h-5 text-wa-green" />
          <h3 className="font-medium">Nova equipe</h3>
        </div>
        <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            placeholder="Nome da equipe"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <Select
            value={form.channelId}
            onChange={(e) => setForm({ ...form, channelId: e.target.value })}
          >
            <option value="">Canal (opcional)</option>
            {channels.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.name}
              </option>
            ))}
          </Select>
          <Button type="submit" loading={createMutation.isPending} className="sm:col-span-2">
            Criar equipe
          </Button>
        </form>
      </Card>

      {isLoading && <SkeletonList count={3} />}

      {!isLoading && teams.length === 0 && (
        <EmptyState
          icon={UsersRound}
          title="Nenhuma equipe"
          description="Crie equipes para organizar o atendimento por canal."
        />
      )}

      <div className="space-y-4 max-w-3xl">
        {teams.map((team: Team) => (
          <Card key={team.id}>
            <div className="flex justify-between items-start gap-3 mb-4">
              <div>
                <h3 className="font-semibold text-lg">{team.name}</h3>
                <p className="text-sm text-wa-muted">{team.members_count} membros</p>
                <div className="flex gap-1 mt-2 flex-wrap">
                  {team.channels.map((ch) => (
                    <Badge key={ch.id} variant="info">
                      {ch.name}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button
                variant="danger"
                className="text-xs"
                onClick={() => {
                  if (confirm(`Excluir equipe ${team.name}?`)) deleteMutation.mutate(team.id)
                }}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>

            {team.channels.length > 0 && (
              <div className="mb-4">
                <label className="text-xs text-wa-muted block mb-1">Canal padrão</label>
                <Select
                  value=""
                  onChange={(e) => {
                    if (e.target.value) {
                      defaultChannelMutation.mutate({
                        teamId: team.id,
                        channelId: Number(e.target.value),
                      })
                    }
                  }}
                  className="text-sm max-w-xs"
                >
                  <option value="">Definir como padrão...</option>
                  {team.channels.map((ch) => (
                    <option key={ch.id} value={ch.id}>
                      {ch.name}
                    </option>
                  ))}
                </Select>
              </div>
            )}

            <div className="space-y-2 mb-4">
              {team.memberships.map((m) => (
                <div key={m.id} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-gray-800/50">
                  <div className="flex items-center gap-2">
                    <Avatar name={m.user.first_name || m.user.username} size="sm" />
                    <div>
                      <p className="text-sm">{m.user.first_name || m.user.username}</p>
                      <p className="text-xs text-wa-muted">@{m.user.username}</p>
                    </div>
                    <Badge variant={m.role === 'supervisor' ? 'info' : 'default'}>
                      {m.role === 'supervisor' ? 'Supervisor' : 'Atendente'}
                    </Badge>
                  </div>
                  <Button
                    variant="secondary"
                    className="text-xs px-2"
                    onClick={() => removeMemberMutation.mutate({ teamId: team.id, userId: m.user.id })}
                  >
                    Remover
                  </Button>
                </div>
              ))}
            </div>

            <form
              className="flex flex-wrap gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                if (!memberForm.userId) return
                addMemberMutation.mutate({
                  teamId: team.id,
                  userId: Number(memberForm.userId),
                  role: memberForm.role,
                })
              }}
            >
              <Select
                value={memberForm.userId}
                onChange={(e) => setMemberForm({ ...memberForm, userId: e.target.value })}
                className="flex-1 min-w-[140px] text-sm"
              >
                <option value="">Adicionar membro...</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.first_name || u.username}
                  </option>
                ))}
              </Select>
              <Select
                value={memberForm.role}
                onChange={(e) =>
                  setMemberForm({
                    ...memberForm,
                    role: e.target.value as 'atendente' | 'supervisor',
                  })
                }
                className="w-auto text-sm"
              >
                <option value="atendente">Atendente</option>
                <option value="supervisor">Supervisor (equipe)</option>
              </Select>
              <Button type="submit" loading={addMemberMutation.isPending} className="text-sm">
                Adicionar
              </Button>
            </form>
          </Card>
        ))}
      </div>
    </div>
  )
}
