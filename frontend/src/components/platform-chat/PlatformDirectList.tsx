import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { fetchPlatformOperators, fetchPlatformRooms, openPlatformDirect } from '@/services/platformChat'
import type { PlatformRoom } from '@/types'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

interface Props {
  selectedRoomId: number | null
  onSelectRoom: (room: PlatformRoom) => void
}

export default function PlatformDirectList({ selectedRoomId, onSelectRoom }: Props) {
  const queryClient = useQueryClient()
  const [pickerOpen, setPickerOpen] = useState(false)

  const { data: roomsData } = useQuery({
    queryKey: ['platform-chat-rooms'],
    queryFn: fetchPlatformRooms,
  })

  const { data: operators = [] } = useQuery({
    queryKey: ['platform-chat-operators'],
    queryFn: fetchPlatformOperators,
    enabled: pickerOpen,
  })

  const directRooms = (roomsData?.results || []).filter((room) => room.kind === 'direct')

  const openMutation = useMutation({
    mutationFn: (username: string) => openPlatformDirect(username),
    onSuccess: (room) => {
      queryClient.invalidateQueries({ queryKey: ['platform-chat-rooms'] })
      onSelectRoom(room)
      setPickerOpen(false)
    },
  })

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="p-3 border-b border-wa-border flex items-center justify-between">
        <p className="text-sm font-medium">Conversas privadas</p>
        <Button variant="secondary" className="px-2 py-1 text-xs" onClick={() => setPickerOpen((v) => !v)}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          Nova
        </Button>
      </div>

      {pickerOpen && (
        <div className="max-h-40 overflow-y-auto border-b border-wa-border">
          {operators.map((op) => (
            <button
              key={op.id}
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-wa-panel/70"
              onClick={() => openMutation.mutate(op.username)}
            >
              <span className="font-medium">{op.display_name}</span>
              <span className="text-wa-muted ml-2">@{op.username}</span>
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {directRooms.length === 0 && (
          <p className="text-xs text-wa-muted p-4 text-center">
            Abra uma conversa privada com alguém da equipe.
          </p>
        )}
        {directRooms.map((room) => (
          <button
            key={room.id}
            type="button"
            onClick={() => onSelectRoom(room)}
            className={cn(
              'w-full text-left px-3 py-3 border-b border-wa-border/50 hover:bg-wa-panel/50 transition-colors',
              selectedRoomId === room.id && 'bg-wa-green/10',
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{room.display_name}</p>
                {room.peer && (
                  <p className="text-xs text-wa-muted truncate">@{room.peer.username}</p>
                )}
              </div>
              {room.unread_count > 0 && (
                <span className="text-[10px] bg-red-500 text-white rounded-full px-1.5 py-0.5">
                  {room.unread_count}
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
