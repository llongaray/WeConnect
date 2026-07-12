# ROPA — Registro de Operações de Tratamento

## Operações principais

| Operação | Dados | Titulares | Base legal | Retenção | Sistemas |
|----------|-------|-----------|------------|----------|----------|
| Autenticação | credenciais, IP, 2FA | colaboradores | contrato / segurança | sessão + audit | Django, Redis |
| Inbox WhatsApp | mensagens, contatos, mídia | clientes finais | contrato / legítimo interesse | `data_retention_days` | PostgreSQL, disco |
| Administração tenant | CPF, e-mail, telefone | colaboradores | contrato | até exclusão | PostgreSQL |
| Auditoria | ações admin, metadados sanitizados | colaboradores | legítimo interesse | 365 dias | PostgreSQL |
| Segurança | IP, username, eventos | colaboradores | legítimo interesse | 90 dias | PostgreSQL |
| IA (DeepSeek) | prompts de fluxo | colaboradores (indireto) | contrato | não persistido além do fluxo | API externa |

## Medidas técnicas

- Row-level security por `company_id`
- Criptografia Fernet (`FIELD_ENCRYPTION_KEY`) para credenciais
- Purge automático (Celery beat): chat, audit, security events
- Sanitização de PII em audit logs

## Responsáveis

- **Controlador:** empresa cliente (tenant)
- **Operador:** provedor WeConnect / Aray
- **Encarregado:** cadastrado por empresa (`Company.dpo_name`, `Company.dpo_email`)
