import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'unread'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  pulse?: boolean
}

const variants: Record<BadgeVariant, string> = {
  default: 'bg-gray-700 text-gray-300',
  success: 'bg-emerald-900/40 text-emerald-300',
  warning: 'bg-amber-900/40 text-amber-300',
  danger: 'bg-red-900/40 text-red-300',
  info: 'bg-sky-900/40 text-sky-300',
  unread: 'bg-wa-green text-white',
}

export default function Badge({
  variant = 'default',
  pulse = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center text-xs px-2 py-0.5 rounded-full font-medium',
        variants[variant],
        pulse && 'animate-pulse',
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
