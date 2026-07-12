---
name: weconnect-brand
description: >-
  Guia de marca WeConnect / Aray para UI no frontend. Use ao criar ou alterar
  componentes, páginas, estilos Tailwind ou CSS no projeto WeConnect.
---

# WeConnect — guia de marca (Aray)

## Quando usar

Aplique esta skill ao trabalhar em:

- Componentes React em `frontend/src/`
- `tailwind.config.js`, `index.css`
- Textos de produto, login, rodapés e home
- Qualquer decisão de cor, fonte ou naming visual

## Nomenclatura

| Termo | Uso |
|-------|-----|
| **WeConnect** | Nome do produto (CRM WhatsApp) |
| **Aray Soluções Tecnológicas** | Empresa desenvolvedora |
| Crédito padrão | `WeConnect · produto Aray Soluções Tecnológicas © 2026` |

**Não usar:** MoneyConnect, verde WhatsApp `#25D366`, identidade visual sem referência Aray.

## Paleta de cores

### Tokens principais (namespace `aray.*`)

| Token | Hex | Tailwind legado | Uso |
|-------|-----|-----------------|-----|
| primary | `#00A3FF` | `wa-green` | Botões, links, nav ativo, título WeConnect |
| primary-dark | `#0047AB` | — | Gradientes, hover escuro |
| accent | `#FFB800` | `wa-accent` | Destaques secundários, badges warning, glow dourado |
| bg-dark | `#020617` | `wa-dark` | Fundo principal |
| bg-panel | `#0A1628` | `wa-panel` | Sidebar, header, cards |
| bg-chat | `#050A14` | `wa-chat` | Área de conversas |
| bubble-out | `#0B4F8A` | `wa-bubble` | Mensagens enviadas |
| bubble-in | `#0F1D32` | `wa-bubbleIn` | Mensagens recebidas |
| text-muted | `#94A3B8` | `wa-muted` | Legendas, placeholders |
| border | `#1E3A5F` | `wa-border` | Divisores, bordas |

### Regras de uso

- **Primary (azul):** ações principais, navegação ativa, marca WeConnect
- **Accent (dourado):** alertas não críticos, destaques secundários, glow de fundo no login
- **Success:** `emerald-*` ou `sky-*` para estados de sucesso (não verde WhatsApp)
- **Danger:** manter `red-*` para erros e exclusão

## Tipografia

- **Fonte:** Inter (`font-sans`)
- Carregada em `frontend/index.html` via Google Fonts
- Pesos: 400 (corpo), 500 (labels), 600 (títulos), 700 (display)

```tsx
// Títulos de produto
<h1 className="text-2xl font-bold text-wa-green">WeConnect</h1>

// Legendas
<p className="text-sm text-wa-muted">CRM WhatsApp</p>
```

## Componentes padrão

### Botão primário

```tsx
<Button variant="primary">Salvar</Button>
// bg-wa-green (azul Aray) + shadow-glow-green
```

### Botão accent (opcional)

```tsx
<Button variant="accent">Destaque</Button>
// bg-wa-accent (dourado)
```

### Nav ativo

Classes em `index.css`: `.nav-item-active` — fundo `wa-green/15`, texto `wa-green`, barra lateral azul.

### Login

- Logo: `/branding/logo-aray.png`
- Título: **WeConnect** (não MoneyConnect)
- Rodapé com crédito Aray © 2026
- Glow de fundo: azul + dourado (`wa-green/10` + `wa-accent/10`)

### Header / Sidebar

- Logo WeConnect (`logo-weconnect.png`) + texto **WeConnect**
- Subtítulo sidebar: `Aray Soluções Tecnológicas`

## Assets

| Arquivo | Caminho (repo) | Uso |
|---------|----------------|-----|
| Logo WeConnect | `branding/logo-weconnect.png` → `frontend/public/branding/logo-weconnect.png` | Shell do produto |
| Favicon | `branding/favicon.ico` (+ PNGs) → `frontend/public/` | Aba do navegador |
| Logo Aray | `branding/logo-aray.png` → `frontend/public/branding/logo-aray.png` | Seção empresa na home |
| Banner Aray | `branding/banner-aray.png` → `frontend/public/branding/banner-aray.png` | Home institucional |

Fonte de verdade dos PNG: pasta `branding/` na raiz do repositório.

## O que evitar

- Verde WhatsApp `#25D366` / `#00A884`
- Badge "WC" no lugar do logo Aray em shell principal
- Nome **MoneyConnect** em UI visível ao usuário
- Cores hardcoded `green-*` para elementos de marca (usar `wa-green` ou `sky-*`)
- Introduzir nova paleta sem atualizar este guia e `docs/brand/WEConnect_BRAND.md`

## Referência completa

Ver também [docs/brand/WEConnect_BRAND.md](../../docs/brand/WEConnect_BRAND.md) no repositório.
