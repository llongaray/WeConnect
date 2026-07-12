# Certificados TLS para produção

Coloque aqui (perfil prod):

- `fullchain.pem`
- `privkey.pem`

## Opção A — Certbot via Docker (recomendado)

Com nginx prod rodando e DNS apontando para o servidor:

```powershell
cd docker
# Primeira emissão (substitua domínio e e-mail)
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  -d seu-dominio.com --email admin@seu-dominio.com --agree-tos --no-eff-email

# Copiar links simbólicos para nomes fixos usados pelo nginx
# (Linux/macOS — no Windows copie manualmente de live/seu-dominio.com/)
```

O serviço `certbot` no `docker-compose.prod.yml` renova automaticamente a cada 12h.

O nginx prod expõe `/.well-known/acme-challenge/` na porta 80 para validação HTTP-01.

## Opção B — Certificado manual

```bash
certbot certonly --standalone -d seu-dominio.com
```

Copie de `/etc/letsencrypt/live/seu-dominio.com/` para este diretório.

## Allowlist do Django Admin

Edite `docker/nginx.admin-allow.conf` com IPs de confiança antes de expor `/admin/` em produção.
