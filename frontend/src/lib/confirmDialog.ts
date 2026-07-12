import { useConfirmStore, type ConfirmOptions } from '@/store/confirmStore'

export function confirmDialog(options: ConfirmOptions): Promise<boolean> {
  return useConfirmStore.getState().openConfirm(options)
}
