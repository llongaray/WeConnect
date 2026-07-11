# MoneyConnect — CRM WhatsApp

CRM de atendimento WhatsApp com **Django REST + SQLite3**, **React + Vite** e suporte **multi-canal**:

- **WhatsApp Normal** — Evolution API (Baileys) + QR Code
- **WhatsApp Business** — Evolution API (Baileys) + QR Code com app Business
- **API Oficial Meta** — Meta Cloud API (sem Evolution)

## Funcionalidades (v1)

- Múltiplos canais WhatsApp ativos simultaneamente
- Inbox de conversas com chat em tempo quasi-real (WebSocket)
- Contatos sincronizados via webhook (Evolution ou Meta)
- Envio de texto e mídia (imagem, áudio, vídeo, documento)
- Multi-atendentes: perfis **admin** e **atendente**, atribuição de conversas
- Admin: CRUD de usuários e gestão de canais

## Pré-requisitos

- Python 3.11+
- Node.js 20+
- Docker e Docker Compose (apenas para canais Evolution)

## 1. Evolution API (Docker) — canais Normal e Business

Necessário **somente** se for usar canais `evolution_normal` ou `evolution_business`.

```powershell
cd docker
copy evolution.env.example evolution.env
# Edite evolution.env — AUTHENTICATION_API_KEY deve ser igual ao EVOLUTION_API_KEY do backend
docker compose up -d
```

Verifique: http://localhost:8080

## 2. Backend Django

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
python manage.py migrate
python manage.py create_admin
```

Inicie o servidor ASGI (WebSocket):

```powershell
python -m daphne -b 0.0.0.0 -p 8000 moneyconnect.asgi:application
```

## 3. Frontend React

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Acesse: http://localhost:5173

## Canais WhatsApp

### Criar canal (Admin → Canais)

1. Clique em **+ Novo canal**
2. Informe o nome
3. Escolha o tipo:
   - **WhatsApp Normal** → Evolution Baileys (QR Code)
   - **WhatsApp Business** → QR Code com app WhatsApp Business no celular
   - **API Oficial Meta** → credenciais manuais (sem Docker Evolution)

### Webhooks por canal

Cada canal tem URL de webhook única, gerada automaticamente:

| Tipo | URL |
|------|-----|
| Evolution Normal/Business | `http://host.docker.internal:8000/api/webhooks/evolution/{channel_id}/` |
| Meta Cloud API | `http://seu-dominio/api/webhooks/meta/{channel_id}/` |

Para Meta: configure o **Verify Token** igual ao informado na criação do canal.

### Credenciais Meta (API Oficial)

Na criação do canal, informe:

- `Phone Number ID`
- `Access Token`
- `Verify Token` (webhook)
- `WABA ID` (opcional)

OAuth / Embedded Signup será implementado na fase 2.

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `EVOLUTION_API_URL` | URL da Evolution API (padrão: `http://localhost:8080`) |
| `EVOLUTION_API_KEY` | Chave `apikey` — **mesma** em `docker/evolution.env` |
| `EVOLUTION_WEBHOOK_BASE_URL` | Base das URLs de webhook por canal |
| `META_APP_ID` / `META_APP_SECRET` | Meta App (fase 2 OAuth) |
| `META_GRAPH_API_VERSION` | Versão da Graph API (padrão: `v21.0`) |
| `REDIS_HOST` / `REDIS_PORT` | Redis para Django Channels (produção) |

## Fluxo de teste E2E

1. Suba Docker (Evolution + Postgres + Redis) — se usar canal Evolution
2. Suba backend (`daphne`) e frontend (`npm run dev`)
3. Login como admin
4. **Admin → Canais → Novo canal** — escolha o tipo e conecte
5. Envie mensagem de outro celular para o número conectado
6. Conversa aparece na Inbox com badge do canal
7. Atendente clica **Assumir** e responde

## Estrutura

```
MoneyConnect/
├── docker/          # Evolution API + PostgreSQL + Redis
├── backend/         # Django REST + Channels
│   ├── moneyconnect/    # Projeto Django
│   └── apps/
│       ├── whatsapp/    # Canais + providers
│       └── chat/        # Conversas + mensagens
└── frontend/        # React + Vite + Tailwind
```

## API principal

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/login/` | Login JWT |
| GET | `/api/v1/channels/` | Listar canais |
| POST | `/api/v1/channels/` | Criar canal |
| POST | `/api/v1/channels/{id}/connect/` | Conectar canal |
| GET | `/api/v1/conversations/` | Listar conversas (`?channel=id`) |
| GET/POST | `/api/v1/conversations/{id}/messages/` | Mensagens |
| PATCH | `/api/v1/conversations/{id}/assign/` | Atribuir conversa |
| POST | `/api/webhooks/evolution/{channel_id}/` | Webhook Evolution |
| GET/POST | `/api/webhooks/meta/{channel_id}/` | Webhook Meta |

WebSocket: `ws://localhost:8000/ws/chat/?token={jwt}`

## Referências

- [Evolution API — Documentação](https://docs.evolutionfoundation.com.br/evolution-api)
- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
