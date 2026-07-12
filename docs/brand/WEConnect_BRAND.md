# WeConnect — guia de marca Aray

Documentação de referência para designers e desenvolvedores do frontend WeConnect.

## Identidade

- **Produto:** WeConnect — CRM WhatsApp corporativo
- **Empresa:** Aray Soluções Tecnológicas
- **Crédito:** © 2026 Aray Soluções Tecnológicas

## Paleta de cores

### Cores principais

| Nome | Hex | Uso |
|------|-----|-----|
| Azul elétrico (primary) | `#00A3FF` | Botões, links, nav ativo, marca |
| Azul escuro | `#0047AB` | Gradientes, hover |
| Dourado (accent) | `#FFB800` | Destaques secundários, badges warning |
| Dourado suave | `#FFA500` | Glow secundário |

### Fundos e superfícies

| Nome | Hex | Uso |
|------|-----|-----|
| Navy escuro | `#020617` | Fundo da aplicação |
| Painel | `#0A1628` | Sidebar, header, cards |
| Chat | `#050A14` | Área de mensagens |
| Borda | `#1E3A5F` | Divisores |
| Texto muted | `#94A3B8` | Legendas |

### Chat

| Nome | Hex | Uso |
|------|-----|-----|
| Bolha enviada | `#0B4F8A` | Mensagens do atendente |
| Bolha recebida | `#0F1D32` | Mensagens do contato |

## Tipografia

- **Família:** Inter (Google Fonts)
- **Fallback:** system-ui, sans-serif
- **Pesos:** 400, 500, 600, 700

## Classes Tailwind (implementação)

O projeto usa tokens legados `wa-*` remapeados para Aray:

```
wa-green   → #00A3FF (primary azul)
wa-accent  → #FFB800 (dourado)
wa-dark    → #020617
wa-panel   → #0A1628
wa-muted   → #94A3B8
wa-border  → #1E3A5F
```

Namespace explícito `aray-*` disponível para novos componentes.

## Exemplos de combinação

### Botão primário
- Fundo: `#00A3FF`
- Texto: branco
- Sombra: glow azul suave

### Link / nav ativo
- Texto: `#00A3FF`
- Fundo ativo: `rgba(0, 163, 255, 0.15)`

### Badge informativo
- Fundo: `sky-900/40`
- Texto: `sky-300`

### Badge warning
- Fundo: `amber-900/40`
- Texto: `amber-300`

## Assets

```
branding/logo-weconnect.png   → frontend/public/branding/logo-weconnect.png  (produto)
branding/favicon.ico            → frontend/public/favicon.ico                  (favicon)
branding/favicon-*.png          → frontend/public/                             (favicon PNG)
branding/apple-touch-icon.png   → frontend/public/apple-touch-icon.png
branding/logo-aray.png        → frontend/public/branding/logo-aray.png       (empresa Aray)
branding/banner-aray.png      → frontend/public/branding/banner-aray.png     (home)
```

Ver `branding/README.md` para sincronizar alterações com o frontend.

## Skill Cursor

Agentes devem seguir [.cursor/skills/weconnect-brand/SKILL.md](../../.cursor/skills/weconnect-brand/SKILL.md) ao editar UI.

## O que não usar

- Verde WhatsApp `#25D366`
- Nome **MoneyConnect** na interface
- Paletas fora deste guia sem revisão de marca
