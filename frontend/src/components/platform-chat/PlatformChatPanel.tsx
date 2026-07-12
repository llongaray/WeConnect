import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Users, X } from 'lucide-react'
import { fetchPlatformRooms, openPlatformDirect } from '@/services/platformChat'
import type { PlatformRoom } from '@/types'
import PlatformChatMessages from '@/components/platform-chat/PlatformChatMessages'
import PlatformDirectList from '@/components/platform-chat/PlatformDirectList'
import { cn } from '@/lib/cn'

type Tab = 'general' | 'direct'

interface Props {
  onClose: () => void
}

export default function PlatformChatPanel({ onClose }: Props) {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('general')
  const [selectedDirectRoom, setSelectedDirectRoom] = useState<PlatformRoom | null>(null)

  const { data: roomsData } = useQuery({
    queryKey: ['platform-chat-rooms'],
    queryFn: fetchPlatformRooms,
  })

  const generalRoom = useMemo(
    () => (roomsData?.results || []).find((room) => room.kind === 'group') || null,
    [roomsData],
  )

  const openDirectMutation = useMutation({
    mutationFn: (username: string) => openPlatformDirect(username),
    onSuccess: (room) => {
      queryClient.invalidateQueries({ queryKey: ['platform-chat-rooms'] })
      setSelectedDirectRoom(room)
      setTab('direct')
    },
  })

  useEffect(() => {
    if (!selectedDirectRoom && tab === 'direct') {
      const firstDirect = (roomsData?.results || []).find((room) => room.kind === 'direct')
      if (firstDirect) setSelectedDirectRoom(firstDirect)
    }
  }, [roomsData, selectedDirectRoom, tab])

  return (
    <div className="flex flex-col h-full bg-wa-dark border border-wa-border rounded-t-2xl shadow-panel overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-wa-border bg-wa-panel/80">
        <div>
          <p className="text-sm font-semibold">Chat WeConnect</p>
          <p className="text-xs text-wa-muted">Equipe interna em tempo real</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-wa-muted hover:text-white hover:bg-wa-dark transition-colors"
          aria-label="Fechar chat"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex gap-1 px-3 pt-2">
        <button
          type="button"
          onClick={() => setTab('general')}
          className={cn(
            'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
            tab === 'general' ? 'bg-wa-green/20 text-wa-green' : 'text-wa-muted hover:text-white',
          )}
        >
          Geral
        </button>
        <button
          type="button"
          onClick={() => setTab('direct')}
          className={cn(
            'px-3 py-1.5 rounded-md text-xs font-medium transition-colors inline-flex items-center gap-1',
            tab === 'direct' ? 'bg-wa-green/20 text-wa-green' : 'text-wa-muted hover:text-white',
          )}
        >
          <Users className="w-3.5 h-3.5" />
          Privado
        </button>
      </div>

      <div className="flex-1 min-h-0 mt-2">
        {tab === 'general' && generalRoom && (
          <PlatformChatMessages room={generalRoom} />
        )}

        {tab === 'direct' && (
          <div className="grid grid-cols-[140px_1fr] h-full min-h-0">
            <PlatformDirectList
              selectedRoomId={selectedDirectRoom?.id ?? null}
              onSelectRoom={setSelectedDirectRoom}
            />
            <div className="min-h-0 border-l border-wa-border">
              {selectedDirectRoom ? (
                <PlatformChatMessages room={selectedDirectRoom} />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-wa-muted p-4 text-center">
                  Selecione ou crie uma conversa privada.
                </div>
              )}
            </div>
          </div>
        )}

        {tab === 'general' && !generalRoom && (
          <div className="h-full flex items-center justify-center text-sm text-wa-muted">
            Carregando sala geral...
          </div>
        )}
      </div>

      {openDirectMutation.isError && (
        <p className="text-xs text-red-300 px-3 py-2 border-t border-wa-border">
          Não foi possível abrir conversa privada.
        </p>
      )}
    </div>
  )
}
