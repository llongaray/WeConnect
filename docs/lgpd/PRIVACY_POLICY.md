# Política de Privacidade — WeConnect

**Última atualização:** julho/2026

## 1. Controlador e encarregado

O controlador dos dados tratados na plataforma WeConnect é a empresa contratante (tenant), identificada no cadastro. Cada empresa pode cadastrar seu **Encarregado (DPO)** nos dados da empresa (`dpo_name`, `dpo_email`).

## 2. Dados tratados

| Categoria | Exemplos | Finalidade |
|-----------|----------|------------|
| Colaboradores | nome, e-mail, CPF, telefone | autenticação, operação do CRM |
| Titulares WhatsApp | telefone, nome, mensagens, mídia | atendimento omnichannel |
| Segurança | IP, logs de acesso, eventos 2FA | segurança e auditoria |

## 3. Bases legais (LGPD)

- **Execução de contrato** — prestação do serviço SaaS ao cliente
- **Legítimo interesse** — segurança, prevenção a fraudes, melhoria do serviço
- **Consentimento** — quando exigido (ex.: cookies não essenciais, integrações opcionais)

## 4. Compartilhamento e subprocessadores

Consulte [SUBPROCESSORS.md](./SUBPROCESSORS.md) para a lista de provedores (Meta, Evolution API, DeepSeek, Cloudflare Turnstile).

## 5. Retenção

- Mensagens e contatos: conforme `data_retention_days` da empresa (padrão 365 dias)
- Eventos de segurança: 90 dias
- Logs de auditoria: 365 dias

## 6. Direitos do titular (Art. 18)

Gestores podem, via API/painel:

- **Exportar** dados de contato: `GET /api/v1/contacts/{id}/export-data/`
- **Excluir** dados de contato: `POST /api/v1/contacts/{id}/erase/`

Titulares devem contatar o encarregado (DPO) da empresa responsável.

## 7. Segurança

Criptografia de credenciais, isolamento multi-tenant, 2FA, URLs assinadas para mídia, auditoria administrativa.

## 8. Alterações

Alterações desta política serão comunicadas no login e nesta página.
