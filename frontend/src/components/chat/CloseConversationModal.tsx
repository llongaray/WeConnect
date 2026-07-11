import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'

interface Props {
  open: boolean
  onClose: () => void
  onConfirm: (farewell: string) => void
  loading?: boolean
  contactName: string
}

export default function CloseConversationModal({
  open,
  onClose,
  onConfirm,
  loading,
  contactName,
}: Props) {
  return (
    <Modal open={open} onClose={onClose} title="Encerrar conversa">
      <p className="text-sm text-wa-muted mb-4">
        Deseja encerrar a conversa com <strong className="text-gray-200">{contactName}</strong>?
        A próxima mensagem do cliente abrirá um novo atendimento.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          const form = e.target as HTMLFormElement
          const farewell = (form.elements.namedItem('farewell') as HTMLInputElement).value
          onConfirm(farewell)
        }}
        className="space-y-4"
      >
        <Input
          name="farewell"
          placeholder="Mensagem de despedida (opcional)"
          className="text-sm"
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" loading={loading} className="bg-red-600 hover:bg-red-700">
            Encerrar
          </Button>
        </div>
      </form>
    </Modal>
  )
}
