import { create } from 'zustand'

interface LoadingState {
  pendingCount: number
  visible: boolean
  increment: () => void
  decrement: () => void
  setVisible: (visible: boolean) => void
}

export const useLoadingStore = create<LoadingState>((set) => ({
  pendingCount: 0,
  visible: false,

  increment: () =>
    set((state) => ({
      pendingCount: state.pendingCount + 1,
    })),

  decrement: () =>
    set((state) => ({
      pendingCount: Math.max(0, state.pendingCount - 1),
    })),

  setVisible: (visible) => set({ visible }),
}))
