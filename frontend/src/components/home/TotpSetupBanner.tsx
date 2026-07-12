import { Link } from 'react-router-dom'
import { ShieldCheck, Smartphone } from 'lucide-react'
import Button from '@/components/ui/Button'

export default function TotpSetupBanner() {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3">
      <div className="flex items-center gap-3 min-w-0">
        <ShieldCheck className="w-5 h-5 text-amber-400 shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-amber-200">Configure o 2FA para liberar o CRM</p>
          <p className="text-xs text-wa-muted truncate">
            Use Google Authenticator, Microsoft Authenticator ou Authy.
          </p>
        </div>
      </div>
      <Link to="/profile" className="shrink-0">
        <Button className="px-3 py-1.5 text-xs">
          <Smartphone className="w-4 h-4 mr-1.5" />
          Configurar 2FA
        </Button>
      </Link>
    </div>
  )
}
