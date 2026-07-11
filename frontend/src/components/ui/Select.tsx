import type { SelectHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
}

export default function Select({ label, className, children, ...props }: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm mb-1 text-gray-300">{label}</label>
      )}
      <select
        className={cn(
          'w-full px-3 py-2 bg-gray-800 border border-wa-border rounded-lg text-sm',
          'focus:outline-none focus:border-wa-green focus:ring-1 focus:ring-wa-green/30',
          'transition-all duration-200 disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  )
}
