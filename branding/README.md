# Assets de marca

PNG oficiais do repositório. **Fonte de verdade** para designers; o frontend serve cópias em `frontend/public/branding/`.

| Arquivo | Uso |
|---------|-----|
| `logo-weconnect.png` | Produto WeConnect (login, header, sidebar, card na home) |
| `favicon.ico` | Favicon do app (gerado a partir de `logo-weconnect.png`) |
| `favicon-16x16.png` | Favicon PNG 16px |
| `favicon-32x32.png` | Favicon PNG 32px |
| `apple-touch-icon.png` | Ícone iOS / atalho na tela inicial |
| `logo-aray.png` | Empresa Aray Soluções Tecnológicas |
| `banner-aray.png` | Banner institucional Aray na home |

Ao alterar um asset aqui, copie para `frontend/public/branding/` antes do build:

```powershell
Copy-Item -Force branding/favicon* branding/apple-touch-icon.png frontend/public/
Copy-Item -Force branding/logo-*.png branding/banner-aray.png frontend/public/branding/
```
