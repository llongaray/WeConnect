import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const STORAGE_KEY = 'weconnect-cookie-consent'

export default function CookieConsentBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setVisible(true)
    }
  }, [])

  if (!visible) return null

  const accept = () => {
    localStorage.setItem(STORAGE_KEY, 'accepted')
    setVisible(false)
  }

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 p-4">
      <div className="max-w-3xl mx-auto rounded-lg border border-wa-border bg-wa-panel/95 backdrop-blur px-4 py-3 shadow-lg">
        <p className="text-sm text-wa-muted">
          Utilizamos cookies essenciais para autenticação e segurança. Scripts de terceiros (ex.: Cloudflare
          Turnstile no login) podem processar seu IP. Consulte a{' '}
          <Link to="/privacy" className="text-wa-green hover:underline">
            Política de Privacidade
          </Link>
          .
        </p>
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={accept}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-wa-green text-white hover:bg-wa-green/90"
          >
            Entendi
          </button>
        </div>
      </div>
    </div>
  )
}
