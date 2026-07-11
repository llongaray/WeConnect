import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface NavSectionProps {
  label: string
  children: ReactNode
  className?: string
}

export default function NavSection({ label, children, className }: NavSectionProps) {
  return (
    <div className={cn('mb-4', className)}>
      <p className="px-4 mb-1 text-[10px] font-semibold uppercase tracking-wider text-wa-muted">
        {label}
      </p>
      <div className="space-y-0.5">{children}</div>
    </div>
  )
}
