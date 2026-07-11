import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/cn'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  className?: string
  step?: number
  totalSteps?: number
}

export default function Modal({
  open,
  onClose,
  title,
  children,
  className,
  step,
  totalSteps,
}: ModalProps) {
  useEffect(() => {
    if (!open) return
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEsc)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className={cn(
          'glass-panel rounded-card p-6 w-full max-w-lg shadow-panel animate-slide-up',
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
            {step !== undefined && totalSteps !== undefined && (
              <div className="flex items-center gap-2 mt-2">
                {Array.from({ length: totalSteps }).map((_, i) => (
                  <div
                    key={i}
                    className={cn(
                      'h-1 flex-1 rounded-full transition-all duration-300',
                      i < step ? 'bg-wa-green' : i === step ? 'bg-wa-green/50' : 'bg-gray-700',
                    )}
                  />
                ))}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 text-wa-muted hover:text-white rounded-lg hover:bg-gray-700 transition-colors"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
