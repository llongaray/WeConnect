import { Link } from 'react-router-dom'
import Card from '@/components/ui/Card'
import PageHeader from '@/components/ui/PageHeader'

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-wa-dark p-6 overflow-y-auto">
      <div className="max-w-3xl mx-auto space-y-6">
        <PageHeader
          title="Política de Privacidade"
          description="Transparência sobre tratamento de dados pessoais no WeConnect (LGPD)."
        />
        <Card padding="lg" className="prose prose-invert prose-sm max-w-none space-y-4 text-wa-muted">
          <section>
            <h2 className="text-white text-lg font-semibold">1. Controlador e encarregado</h2>
            <p>
              O controlador é a empresa contratante (tenant). O encarregado (DPO) é cadastrado nos dados da
              empresa na plataforma.
            </p>
          </section>
          <section>
            <h2 className="text-white text-lg font-semibold">2. Dados tratados</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Colaboradores: nome, e-mail, CPF, telefone</li>
              <li>Titulares WhatsApp: telefone, nome, mensagens e mídia</li>
              <li>Segurança: IP, logs de acesso, eventos 2FA</li>
            </ul>
          </section>
          <section>
            <h2 className="text-white text-lg font-semibold">3. Bases legais</h2>
            <p>Execução de contrato, legítimo interesse (segurança) e consentimento quando aplicável.</p>
          </section>
          <section>
            <h2 className="text-white text-lg font-semibold">4. Retenção</h2>
            <p>
              Mensagens e contatos: prazo configurado por empresa (padrão 365 dias). Eventos de segurança: 90
              dias. Auditoria: 365 dias.
            </p>
          </section>
          <section>
            <h2 className="text-white text-lg font-semibold">5. Direitos do titular</h2>
            <p>
              Gestores podem exportar ou excluir dados de contatos via painel. Titulares devem contatar o DPO da
              empresa responsável.
            </p>
          </section>
          <section>
            <h2 className="text-white text-lg font-semibold">6. Subprocessadores</h2>
            <p>Meta, Evolution API, DeepSeek, Cloudflare Turnstile e Brasil API (consulta CNPJ).</p>
          </section>
          <p className="text-xs pt-4">
            Documentação completa: repositório <code>docs/lgpd/</code>
          </p>
          <Link to="/login" className="text-wa-green hover:underline text-sm">
            Voltar ao login
          </Link>
        </Card>
      </div>
    </div>
  )
}
