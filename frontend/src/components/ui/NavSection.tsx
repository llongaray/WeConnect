import type { ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'

interface NavSectionProps {
  label: string
  open: boolean
  onToggle: () => void
  collapsible?: boolean
  collapsedSidebar?: boolean
  sectionId: string
  children: ReactNode
  className?: string
}

export default function NavSection({
  label,
  open,
  onToggle,
  collapsible = true,
  collapsedSidebar = false,
  sectionId,
  children,
  className,
}: NavSectionProps) {
  if (collapsedSidebar) {
    return (
      <div className={cn('mb-2 space-y-0.5', className)}>
        {children}
      </div>
    )
  }

  const contentId = `nav-section-${sectionId}`

  return (
    <div className={cn('mb-3', className)}>
      {collapsible ? (
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          aria-controls={contentId}
          className="flex w-full items-center justify-between px-3 py-1.5 mb-1 rounded-md text-[10px] font-semibold uppercase tracking-wider text-wa-muted hover:text-gray-300 hover:bg-wa-dark/40 transition-colors"
        >
          <span>{label}</span>
          <ChevronDown
            className={cn('w-3.5 h-3.5 transition-transform duration-200', open && 'rotate-180')}
          />
        </button>
      ) : (
        <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-wider text-wa-muted">
          {label}
        </p>
      )}

      <div
        id={contentId}
        className={cn(
          'grid transition-[grid-template-rows] duration-200 ease-out',
          open || !collapsible ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]',
        )}
      >
        <div className="overflow-hidden">
          <div className="space-y-0.5">{children}</div>
        </div>
      </div>
    </div>
  )
}
