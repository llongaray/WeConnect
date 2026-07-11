import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  hover?: boolean
  padding?: 'sm' | 'md' | 'lg'
}

const paddings = {
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

export default function Card({
  children,
  hover = false,
  padding = 'md',
  className,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'bg-wa-panel rounded-card border border-wa-border',
        hover && 'transition-all duration-200 hover:-translate-y-0.5 hover:shadow-panel hover:border-gray-600',
        paddings[padding],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
