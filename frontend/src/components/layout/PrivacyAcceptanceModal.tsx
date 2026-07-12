import { useState } from 'react'
import { Link } from 'react-router-dom'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import { acceptPrivacyPolicy } from '@/services/auth'
import { useAuthStore } from '@/store/authStore'

export default function PrivacyAcceptanceModal() {
  const user = useAuthStore((s) => s.user)
  const requiresPrivacyAcceptance = useAuthStore((s) => s.requiresPrivacyAcceptance)
  const [checked, setChecked] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const open = Boolean(user && requiresPrivacyAcceptance)

  const handleAccept = async () => {
    if (!checked) return
    setError('')
    setLoading(true)
    try {
      await acceptPrivacyPolicy()
    } catch {
      setError('Não foi possível registrar o aceite. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => {}}
      title="Política de Privacidade"
      dismissible={false}
      className="max-w-xl"
    >
      <div className="space-y-4 text-sm text-wa-muted">
        <p>
          Olá{user?.first_name ? `, ${user.first_name}` : ''}! Este é seu primeiro acesso à plataforma.
          Antes de continuar, leia e aceite nossa Política de Privacidade (LGPD).
        </p>

        <div className="rounded-lg border border-wa-border/80 bg-wa-dark/50 p-4 space-y-3 max-h-48 overflow-y-auto text-xs">
          <p>
            <strong className="text-white">Dados tratados:</strong> colaboradores (nome, e-mail, CPF),
            titulares WhatsApp (telefone, mensagens), logs de segurança e acesso.
          </p>
          <p>
            <strong className="text-white">Finalidade:</strong> operação do CRM, atendimento via WhatsApp
            e segurança da plataforma.
          </p>
          <p>
            <strong className="text-white">Seus direitos:</strong> acesso, correção, exclusão e portabilidade
            conforme a LGPD. Contate o encarregado (DPO) da sua empresa.
          </p>
          <p>
            <strong className="text-white">Retenção:</strong> prazo configurado por empresa (padrão 365 dias
            para mensagens e contatos).
          </p>
        </div>

        <Link
          to="/privacy"
          target="_blank"
          className="inline-block text-wa-green hover:underline text-sm"
        >
          Ler política completa
        </Link>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 text-xs">
            {error}
          </div>
        )}

        <label className="flex items-start gap-2 text-xs cursor-pointer">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="mt-0.5"
          />
          <span>
            Declaro que li e aceito a{' '}
            <Link to="/privacy" target="_blank" className="text-wa-green hover:underline">
              Política de Privacidade
            </Link>
            .
          </span>
        </label>

        <Button
          type="button"
          className="w-full"
          loading={loading}
          disabled={!checked}
          onClick={handleAccept}
        >
          Aceitar e continuar
        </Button>
      </div>
    </Modal>
  )
}
