import { useLoadingStore } from '@/store/loadingStore'

const SHOW_DELAY_MS = 150
const MIN_VISIBLE_MS = 300

let showTimer: ReturnType<typeof setTimeout> | null = null
let hideTimer: ReturnType<typeof setTimeout> | null = null
let visibleSince = 0

function clearShowTimer() {
  if (showTimer) {
    clearTimeout(showTimer)
    showTimer = null
  }
}

function clearHideTimer() {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

function showBar() {
  clearShowTimer()
  useLoadingStore.getState().setVisible(true)
  visibleSince = Date.now()
}

function hideBar() {
  clearHideTimer()
  useLoadingStore.getState().setVisible(false)
  visibleSince = 0
}

function scheduleHide() {
  const { pendingCount } = useLoadingStore.getState()
  if (pendingCount > 0) return

  const { visible } = useLoadingStore.getState()
  if (!visible) return

  const elapsed = Date.now() - visibleSince
  const remaining = Math.max(0, MIN_VISIBLE_MS - elapsed)

  clearHideTimer()
  hideTimer = setTimeout(() => {
    if (useLoadingStore.getState().pendingCount === 0) {
      hideBar()
    }
  }, remaining)
}

export function startRequest() {
  const store = useLoadingStore.getState()
  store.increment()

  const { visible, pendingCount } = useLoadingStore.getState()
  if (visible || pendingCount === 0) return

  clearShowTimer()
  showTimer = setTimeout(() => {
    if (useLoadingStore.getState().pendingCount > 0) {
      showBar()
    }
  }, SHOW_DELAY_MS)
}

export function endRequest() {
  const store = useLoadingStore.getState()
  store.decrement()
  scheduleHide()
}
