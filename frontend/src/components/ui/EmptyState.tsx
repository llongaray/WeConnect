import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/cn'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  className?: string
  action?: React.ReactNode
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  className,
  action,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center p-8 animate-fade-in',
        className,
      )}
    >
      <div className="w-16 h-16 rounded-full bg-wa-panel border border-wa-border flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-wa-muted" />
      </div>
      <h3 className="text-lg font-medium text-gray-200 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-wa-muted max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
