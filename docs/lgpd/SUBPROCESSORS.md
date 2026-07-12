# Subprocessadores e transferências internacionais

| Provedor | Finalidade | Dados | Localização | Contrato |
|----------|------------|-------|-------------|----------|
| **Meta (WhatsApp Cloud API)** | mensagens oficiais | telefone, conteúdo, mídia | EUA / global | DPA Meta Business |
| **Evolution API** | WhatsApp não-oficial | mensagens, contatos, QR | infraestrutura do cliente | acordo operacional |
| **DeepSeek** | geração de fluxos IA | prompts, definições de bot | China / API internacional | avaliar DPA / SCCs |
| **Cloudflare Turnstile** | CAPTCHA login | IP, fingerprint | global | DPA Cloudflare |
| **Brasil API** | consulta CNPJ | CNPJ consultado | Brasil | termos públicos |

## Obrigações do cliente (tenant)

- Informar titulares WhatsApp sobre tratamento via política própria
- Garantir base legal para mensagens recebidas
- Manter DPO atualizado na configuração da empresa

## Transferência internacional

Quando aplicável (DeepSeek, Meta, Cloudflare), o controlador deve avaliar mecanismos do Art. 33–36 LGPD (cláusulas padrão, avaliação de impacto).
