import { create } from 'zustand'

export type ConfirmVariant = 'default' | 'danger'

export interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: ConfirmVariant
}

interface ConfirmState extends ConfirmOptions {
  open: boolean
  loading: boolean
  resolve: ((value: boolean) => void) | null
  openConfirm: (options: ConfirmOptions) => Promise<boolean>
  setLoading: (loading: boolean) => void
  close: (result: boolean) => void
}

const defaultState: ConfirmOptions = {
  title: '',
  message: '',
  confirmLabel: 'Confirmar',
  cancelLabel: 'Cancelar',
  variant: 'default',
}

export const useConfirmStore = create<ConfirmState>((set, get) => ({
  ...defaultState,
  open: false,
  loading: false,
  resolve: null,

  openConfirm: (options) =>
    new Promise<boolean>((resolve) => {
      set({
        ...defaultState,
        ...options,
        open: true,
        loading: false,
        resolve,
      })
    }),

  setLoading: (loading) => set({ loading }),

  close: (result) => {
    const { resolve } = get()
    resolve?.(result)
    set({
      ...defaultState,
      open: false,
      loading: false,
      resolve: null,
    })
  },
}))
