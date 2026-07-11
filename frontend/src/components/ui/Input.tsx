import type { InputHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  icon?: ReactNode
}

export default function Input({ label, icon, className, ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm mb-1 text-gray-300">{label}</label>
      )}
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-wa-muted pointer-events-none">
            {icon}
          </span>
        )}
        <input
          className={cn(
            'w-full px-3 py-2 bg-gray-800 border border-wa-border rounded-lg text-sm',
            'focus:outline-none focus:border-wa-green focus:ring-1 focus:ring-wa-green/30',
            'transition-all duration-200 placeholder:text-wa-muted disabled:opacity-50',
            icon ? 'pl-10' : undefined,
            className,
          )}
          {...props}
        />
      </div>
    </div>
  )
}
