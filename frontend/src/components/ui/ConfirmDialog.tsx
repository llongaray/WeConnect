import { useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import { useConfirmStore } from '@/store/confirmStore'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

export default function ConfirmDialog() {
  const {
    open,
    title,
    message,
    confirmLabel,
    cancelLabel,
    variant,
    loading,
    close,
  } = useConfirmStore()

  useEffect(() => {
    if (!open) return
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) close(false)
    }
    document.addEventListener('keydown', handleEsc)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [open, loading, close])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[10000] p-4 animate-fade-in"
      onClick={() => !loading && close(false)}
    >
      <div
        className="glass-panel rounded-card p-6 w-full max-w-md shadow-panel animate-slide-up"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="flex items-start gap-3 mb-4">
          {variant === 'danger' && (
            <div className="shrink-0 w-10 h-10 rounded-full bg-red-900/30 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
          )}
          <div className="min-w-0">
            <h3 id="confirm-dialog-title" className="text-lg font-semibold">
              {title}
            </h3>
            <p className="text-sm text-wa-muted mt-2">{message}</p>
          </div>
        </div>

        <div className="flex gap-2 justify-end mt-6">
          <Button variant="secondary" onClick={() => close(false)} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            loading={loading}
            onClick={() => close(true)}
            className={cn(variant === 'danger' && 'bg-red-700 border-red-700 text-white hover:bg-red-600')}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
