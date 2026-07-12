import { Bot, Building2, ExternalLink, MessageSquare, ShieldCheck } from 'lucide-react'
import Card from '@/components/ui/Card'

const features = [
  {
    icon: MessageSquare,
    title: 'Omnichannel WhatsApp',
    description: 'Atendimento unificado com Evolution API e Meta Cloud API em um só lugar.',
  },
  {
    icon: Bot,
    title: 'Automação e chatbot',
    description: 'Fluxos automatizados com Celery e integração com IA para escalar o atendimento.',
  },
  {
    icon: Building2,
    title: 'Multi-empresa',
    description: 'Gestão de equipes, canais e usuários com isolamento seguro por tenant.',
  },
  {
    icon: ShieldCheck,
    title: 'Segurança',
    description: '2FA, criptografia de credenciais, auditoria e controles de acesso por perfil.',
  },
]

export default function HomePresentation() {
  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-xl border border-wa-border">
        <img
          src="/branding/banner-aray.png"
          alt="Aray Soluções Tecnológicas"
          className="w-full h-auto object-cover max-h-48 sm:max-h-56 md:max-h-64"
        />
      </section>

      <section className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <img
          src="/branding/logo-aray.png"
          alt="Logo Aray"
          className="h-16 w-auto shrink-0"
        />
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-white">Aray Soluções Tecnológicas</h1>
          <p className="text-sm text-wa-muted mt-1">
            Desenvolvimento de software sob medida para empresas que precisam de soluções
            corporativas confiáveis, escaláveis e seguras.
          </p>
          <a
            href="https://instagram.com/aray_solucoes"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 mt-2 text-xs text-wa-green hover:underline"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            @aray_solucoes
          </a>
        </div>
      </section>

      <Card padding="lg" className="border-wa-green/25 bg-gradient-to-br from-wa-panel to-wa-dark/80">
        <div className="flex items-center gap-3 mb-3">
          <img
            src="/branding/logo-weconnect.png"
            alt="WeConnect"
            className="h-10 w-auto shrink-0"
          />
          <div>
            <h2 className="text-lg font-semibold text-wa-green">WeConnect</h2>
            <p className="text-xs text-wa-muted">CRM WhatsApp corporativo · 2026</p>
          </div>
        </div>
        <p className="text-sm text-gray-300 leading-relaxed">
          O WeConnect é a plataforma de atendimento WhatsApp desenvolvida pela Aray Soluções
          Tecnológicas. Centralize conversas, contatos e canais; distribua demandas entre equipes;
          automatize respostas com chatbot e use inteligência artificial para acelerar a operação —
          tudo com segurança e controle multi-empresa.
        </p>
      </Card>

      <section>
        <h3 className="text-sm font-semibold text-wa-muted uppercase tracking-wide mb-3">
          Recursos principais
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {features.map(({ icon: Icon, title, description }) => (
            <Card key={title} padding="md" hover className="border-wa-border/80">
              <div className="flex gap-3">
                <div className="w-9 h-9 rounded-lg bg-wa-green/15 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-wa-green" />
                </div>
                <div className="min-w-0">
                  <h4 className="text-sm font-medium text-white">{title}</h4>
                  <p className="text-xs text-wa-muted mt-1 leading-relaxed">{description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <p className="text-xs text-wa-muted text-center pt-2">
        © 2026 Aray Soluções Tecnológicas · WeConnect
      </p>
    </div>
  )
}
