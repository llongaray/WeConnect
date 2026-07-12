# WeConnect — CRM WhatsApp

CRM de atendimento WhatsApp com **Django REST + PostgreSQL**, **React + Vite**, **Celery**, **Redis** e suporte **multi-canal**:

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
- Chatbot com fluxos processados em background via **Celery**

## Pré-requisitos

### Docker (recomendado)

- Docker e Docker Compose

### Desenvolvimento local (opcional)

- Python 3.11+
- Node.js 20+
- Docker e Docker Compose (somente para Evolution API, se usar canais Baileys)

---

## Início rápido com Docker

A stack completa roda em containers: frontend, backend, Celery, Redis, PostgreSQL (app + Evolution) e Evolution API.

```powershell
cd docker
copy backend.env.example backend.env
copy evolution.env.example evolution.env
```

Edite os arquivos `.env` e use a **mesma chave** em:

- `backend.env` → `EVOLUTION_API_KEY`
- `evolution.env` → `AUTHENTICATION_API_KEY`

Suba todos os serviços:

```powershell
docker compose up -d --build
```

### URLs

| Serviço | URL |
|---------|-----|
| Frontend (nginx) | http://localhost:5173 |
| Backend (Django + Daphne) | http://localhost:8000 |
| Evolution API | http://localhost:8080 |

### Login inicial

| Campo | Valor padrão (dev) |
|-------|---------------------|
| Usuário | `admin` |
| Senha | Ver `DJANGO_ADMIN_PASSWORD` em `docker/backend.env` (mín. 10 caracteres) |

Credenciais configuráveis em `docker/backend.env` (`DJANGO_ADMIN_*`). **Troque todas as chaves em produção.**

### Produção (HTTPS)

```powershell
cd docker
# Coloque certificados em docker/certs/ (fullchain.pem, privkey.pem) — ver docker/certs/README.md
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

No perfil prod, apenas nginx expõe portas 80/443; backend, postgres e redis ficam na rede interna Docker.

### Segurança (Fase 3–5)

- JWT em cookies **HttpOnly** + **CSRF double-submit** em mutações `/api/v1/`
- **2FA TOTP** com onboarding restrito: após login, acesso apenas a `/onboarding` e `/profile` até confirmar QR no app autenticador (Google Authenticator, Authy, etc.)
- Papéis obrigados via `TOTP_REQUIRED_ROLES` (padrão: `superuser,gestor`)
- **CAPTCHA** Cloudflare Turnstile após falhas de login (gratuito — configure `TURNSTILE_*`)
- Painel **Segurança** (`/admin/security`) — eventos, IDOR bloqueado e desbloqueio de IP
- Mídia de chat via endpoint autenticado com **URL assinada** (sem proxy público `/media/`)
- Credenciais Meta **mascaradas** na API; ação `reveal-credentials` com audit log
- Credenciais de canal criptografadas (`FIELD_ENCRYPTION_KEY` + rotação via `FIELD_ENCRYPTION_KEY_OLD`)
- Alertas webhook (`SECURITY_ALERT_WEBHOOK_URL`) e retenção (`purge_security_events --days=90`)
- CI: Dependabot + `pip-audit` + `bandit` + testes IDOR + `npm audit` (`.github/workflows/security.yml`)
- Produção: **Certbot** sidecar, allowlist IP em `/admin/`, `ADMIN_ENABLED=false` recomendado

#### Cloudflare Free (opcional)

Para DDoS básico e proxy DNS gratuito: crie zona no Cloudflare, aponte A/CNAME para o servidor e ative o proxy laranja. Mantenha `SECURE_HSTS_SECONDS` apenas com HTTPS válido no origin ou Full (strict) com certificado Let's Encrypt.

#### Rotação de chave de criptografia

```powershell
# 1. Gere nova chave e mova a atual para FIELD_ENCRYPTION_KEY_OLD
# 2. Atualize FIELD_ENCRYPTION_KEY no backend.env
docker compose exec backend python manage.py rotate_field_encryption_key
# 3. Remova FIELD_ENCRYPTION_KEY_OLD após validar
```

### Serviços Docker

| Container | Função | Porta host |
|-----------|--------|------------|
| `weconnect_frontend` | React (build) + nginx | 5173 |
| `weconnect_backend` | Django REST + WebSocket (Daphne) | 8000 |
| `weconnect_celery_worker` | Worker Celery (chatbot, tarefas async) | — |
| `weconnect_celery_beat` | Agendador Celery | — |
| `weconnect_postgres` | PostgreSQL do app | 5434 |
| `weconnect_evolution_api` | Evolution API | 8080 |
| `weconnect_evolution_postgres` | PostgreSQL da Evolution | 5433 |
| `weconnect_redis` | Redis (Celery, Channels, Evolution) | 6379 |

### Redis — bancos lógicos

| DB | Uso |
|----|-----|
| 0 | Celery (broker + result backend) |
| 1 | Evolution API (cache) |
| 2 | Django Channels (WebSocket) |

### Comandos úteis

```powershell
cd docker
docker compose ps
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose down
docker compose down -v   # remove volumes (apaga dados)
```

---

## Desenvolvimento local (sem Docker completo)

Use esta opção para iterar no código com hot-reload. O backend local usa **SQLite** por padrão.

### 1. Evolution API (Docker) — canais Normal e Business

Necessário **somente** se for usar canais `evolution_normal` ou `evolution_business`.

```powershell
cd docker
copy evolution.env.example evolution.env
docker compose up -d postgres redis evolution-api
```

Verifique: http://localhost:8080

### 2. Backend Django

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
python -m daphne -b 0.0.0.0 -p 8000 weconnect.asgi:application
```

Para Celery em dev local (opcional):

```powershell
# Terminal separado, com USE_CELERY=true no .env
celery -A weconnect worker -l info
```

### 3. Frontend React

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Acesse: http://localhost:5173

Guia de marca (paleta Aray, fontes, nomenclatura WeConnect): [docs/brand/WEConnect_BRAND.md](docs/brand/WEConnect_BRAND.md) e skill Cursor em `.cursor/skills/weconnect-brand/`. PNGs em [branding/](branding/).

---

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

| Ambiente | Tipo | URL base |
|----------|------|----------|
| Docker | Evolution Normal/Business | `http://backend:8000/api/webhooks/evolution/{channel_id}/` |
| Local + Evolution Docker | Evolution Normal/Business | `http://host.docker.internal:8000/api/webhooks/evolution/{channel_id}/` |
| Produção | Meta Cloud API | `https://seu-dominio/api/webhooks/meta/{channel_id}/` |
| Produção | Messenger / Instagram | `https://seu-dominio/api/webhooks/meta-messaging/{channel_id}/` |

Para Meta: configure o **Verify Token** igual ao informado na criação do canal.

### Credenciais Meta (API Oficial)

Na criação do canal, informe:

- `Phone Number ID`
- `Access Token`
- `Verify Token` (webhook)
- `WABA ID` (opcional)

OAuth / Embedded Signup será implementado na fase 2.

---

## Variáveis de ambiente

### `docker/backend.env` (stack Docker)

| Variável | Descrição |
|----------|-----------|
| `DJANGO_SECRET_KEY` | Chave secreta do Django |
| `POSTGRES_*` | Conexão com PostgreSQL do app |
| `USE_REDIS_CHANNELS` | `true` — WebSocket via Redis |
| `USE_CELERY` | `true` — chatbot e tarefas async via fila |
| `CELERY_BROKER_URL` | Redis do Celery (padrão: `redis://redis:6379/0`) |
| `REDIS_CHANNELS_URL` | Redis do Channels (padrão: `redis://redis:6379/2`) |
| `EVOLUTION_API_URL` | URL interna da Evolution (`http://evolution-api:8080`) |
| `EVOLUTION_API_KEY` | Chave `apikey` — **mesma** em `docker/evolution.env` |
| `EVOLUTION_WEBHOOK_BASE_URL` | Base dos webhooks (`http://backend:8000/api/webhooks`) |
| `DJANGO_ADMIN_*` | Usuário admin criado no primeiro start |

### `.env` na raiz (dev local)

| Variável | Descrição |
|----------|-----------|
| `EVOLUTION_API_URL` | URL da Evolution API (padrão: `http://localhost:8080`) |
| `EVOLUTION_API_KEY` | Chave `apikey` — **mesma** em `docker/evolution.env` |
| `EVOLUTION_WEBHOOK_BASE_URL` | Base das URLs de webhook por canal |
| `META_APP_ID` / `META_APP_SECRET` | Meta App (fase 2 OAuth) |
| `META_GRAPH_API_VERSION` | Versão da Graph API (padrão: `v21.0`) |
| `REDIS_HOST` / `REDIS_PORT` | Redis para Celery e Channels (dev com Docker parcial) |
| `USE_CELERY` | `true` para enfileirar chatbot no Celery |
| `POSTGRES_HOST` | Se definido, usa PostgreSQL em vez de SQLite |

---

## Fluxo de teste E2E

1. Suba a stack: `cd docker && docker compose up -d --build`
2. Acesse http://localhost:5173 e faça login como admin
3. **Admin → Canais → Novo canal** — escolha o tipo e conecte (QR Code)
4. Envie mensagem de outro celular para o número conectado
5. Conversa aparece na Inbox com badge do canal
6. Atendente clica **Assumir** e responde

---

## Estrutura

```
WeConnect/
├── docker/
│   ├── docker-compose.yml       # Stack completa
│   ├── Dockerfile.backend       # Django + Daphne + Celery
│   ├── Dockerfile.frontend      # Build React + nginx
│   ├── nginx.conf               # Proxy /api, /media, /ws
│   ├── entrypoint.backend.sh    # migrate, admin, collectstatic
│   ├── backend.env.example      # Variáveis do backend (Docker)
│   └── evolution.env.example    # Variáveis da Evolution API
├── backend/                     # Django REST + Channels + Celery
│   ├── weconnect/               # Projeto Django (pacote interno)
│   └── apps/
│       ├── accounts/            # Usuários, equipes, auth JWT
│       ├── whatsapp/            # Canais + providers (Evolution, Meta)
│       ├── chat/                # Conversas + mensagens + WebSocket
│       ├── automation/          # Chatbot + tasks Celery
│       └── integrations/        # DeepSeek, gerador de fluxos
├── frontend/                    # React + Vite + Tailwind
└── .env.example                 # Variáveis para dev local
```

---

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
| GET/POST | `/api/webhooks/meta/{channel_id}/` | Webhook Meta WhatsApp |
| GET/POST | `/api/webhooks/meta-messaging/{channel_id}/` | Webhook Messenger / Instagram |

WebSocket:

- **Docker / nginx:** `ws://localhost:5173/ws/chat/?token={jwt}`
- **Dev local (Vite):** `ws://localhost:8000/ws/chat/?token={jwt}`

---

## Referências

- [Evolution API — Documentação](https://docs.evolutionfoundation.com.br/evolution-api)
- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
