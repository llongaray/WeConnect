import { useEffect, useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { Channel } from '@/types'
import { getChannelPlatformLabel, getChannelTypeIcon } from '@/lib/channelTypes'
import { cn } from '@/lib/cn'

interface ChannelFilterDropdownProps {
  channels: Channel[]
  selectedIds: number[]
  onChange: (ids: number[]) => void
}

export default function ChannelFilterDropdown({
  channels,
  selectedIds,
  onChange,
}: ChannelFilterDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const allSelected = selectedIds.length === 0
  const label = allSelected
    ? 'Todos os canais'
    : `${selectedIds.length} canal(is)`

  const toggleChannel = (channelId: number) => {
    if (selectedIds.includes(channelId)) {
      onChange(selectedIds.filter((id) => id !== channelId))
    } else {
      onChange([...selectedIds, channelId])
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="w-full flex items-center justify-between gap-2 px-2 py-1.5 text-xs bg-gray-800 border border-wa-border rounded-lg hover:border-wa-green transition-colors"
      >
        <span className="truncate text-left">{label}</span>
        <ChevronDown className={cn('w-3.5 h-3.5 shrink-0 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute z-30 mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-wa-border bg-gray-900 shadow-xl p-2 space-y-1">
          <label className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-800 cursor-pointer text-xs">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={() => onChange([])}
              className="rounded border-wa-border"
            />
            <span>Todos os canais</span>
          </label>
          {channels.map((channel) => {
            const Icon = getChannelTypeIcon(channel.channel_type)
            const checked = selectedIds.includes(channel.id)
            return (
              <label
                key={channel.id}
                className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-800 cursor-pointer text-xs"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleChannel(channel.id)}
                  className="rounded border-wa-border"
                />
                <Icon className="w-3.5 h-3.5 text-wa-green shrink-0" />
                <span className="truncate flex-1">{channel.name}</span>
                <span className="text-[10px] text-wa-muted shrink-0">
                  {getChannelPlatformLabel(channel.channel_type)}
                </span>
              </label>
            )
          })}
        </div>
      )}
    </div>
  )
}
