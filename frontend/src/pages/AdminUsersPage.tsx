import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2, UserPlus, Users } from 'lucide-react'
import { createUser, deleteUser, fetchUsers, updateUser } from '@/services/chat'
import type { User } from '@/types'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Select from '@/components/ui/Select'
import { SkeletonList } from '@/components/ui/Skeleton'

export default function AdminUsersPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    username: '',
    password: '',
    first_name: '',
    role: 'atendente',
  })
  const [editing, setEditing] = useState<User | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setForm({ username: '', password: '', first_name: '', role: 'atendente' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      updateUser(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setEditing(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const users = data?.results || []

  return (
    <div className="h-full p-6 overflow-y-auto">
      <PageHeader
        title="Gerenciar Usuários"
        description="Crie e gerencie atendentes e administradores."
      />

      <Card padding="lg" className="mb-8 max-w-2xl border-wa-green/20">
        <div className="flex items-center gap-2 mb-4">
          <UserPlus className="w-5 h-5 text-wa-green" />
          <h3 className="font-medium">Novo usuário</h3>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            createMutation.mutate(form)
          }}
          className="grid grid-cols-1 sm:grid-cols-2 gap-3"
        >
          <Input
            placeholder="Usuário"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <Input
            type="password"
            placeholder="Senha"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <Input
            placeholder="Nome"
            value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
          />
          <Select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="atendente">Atendente</option>
            <option value="supervisor">Supervisor</option>
            <option value="admin">Administrador</option>
          </Select>
          <Button
            type="submit"
            loading={createMutation.isPending}
            className="sm:col-span-2"
          >
            Criar usuário
          </Button>
        </form>
      </Card>

      {isLoading && <SkeletonList count={4} />}

      {!isLoading && users.length === 0 && (
        <EmptyState
          icon={Users}
          title="Nenhum usuário"
          description="Crie o primeiro usuário usando o formulário acima."
        />
      )}

      <div className="space-y-3 max-w-2xl">
        {users.map((user, index) => (
          <Card
            key={user.id}
            className="animate-fade-in"
            style={{ animationDelay: `${index * 40}ms` }}
          >
            {editing?.id === user.id ? (
              <form
                className="flex flex-wrap gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  updateMutation.mutate({
                    id: user.id,
                    payload: {
                      first_name: editing.first_name,
                      role: editing.role,
                    },
                  })
                }}
              >
                <Input
                  value={editing.first_name}
                  onChange={(e) => setEditing({ ...editing, first_name: e.target.value })}
                  className="flex-1 min-w-[120px]"
                />
                <Select
                  value={editing.role}
                  onChange={(e) =>
                    setEditing({ ...editing, role: e.target.value as User['role'] })
                  }
                  className="w-auto"
                >
                  <option value="atendente">Atendente</option>
                  <option value="supervisor">Supervisor</option>
                  <option value="admin">Admin</option>
                </Select>
                <Button type="submit" loading={updateMutation.isPending}>
                  Salvar
                </Button>
                <Button type="button" variant="secondary" onClick={() => setEditing(null)}>
                  Cancelar
                </Button>
              </form>
            ) : (
              <div className="flex justify-between items-center gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <Avatar name={user.first_name || user.username} size="sm" />
                  <div className="min-w-0">
                    <p className="font-medium truncate">{user.first_name || user.username}</p>
                    <p className="text-sm text-wa-muted">@{user.username}</p>
                  </div>
                  <Badge
                    variant={
                      user.role === 'admin'
                        ? 'info'
                        : user.role === 'supervisor'
                          ? 'warning'
                          : 'default'
                    }
                  >
                    {user.role === 'admin'
                      ? 'Admin'
                      : user.role === 'supervisor'
                        ? 'Supervisor'
                        : 'Atendente'}
                  </Badge>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="secondary"
                    onClick={() => setEditing(user)}
                    className="px-3 py-1 text-sm"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                    Editar
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => {
                      if (confirm('Excluir este usuário?')) deleteMutation.mutate(user.id)
                    }}
                    loading={deleteMutation.isPending}
                    className="px-3 py-1 text-sm"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Excluir
                  </Button>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
