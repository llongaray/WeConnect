import { useLoadingStore } from '@/store/loadingStore'
import { cn } from '@/lib/cn'

export default function GlobalProgressBar() {
  const visible = useLoadingStore((s) => s.visible)

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-[9999] h-[3px] pointer-events-none transition-opacity duration-200',
        visible ? 'opacity-100' : 'opacity-0',
      )}
      aria-hidden={!visible}
      aria-live="polite"
    >
      <div className="h-full w-1/3 animate-progress-indeterminate bg-wa-green shadow-glow-green/50" />
    </div>
  )
}
