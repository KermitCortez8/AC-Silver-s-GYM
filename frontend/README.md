# Frontend Vue

Frontend web del sistema AC Silver's GYM construido con Vue 3, Vite, Pinia y Vue Router.

## Requisitos

- Node.js 18+
- Variables de entorno configuradas en un archivo `.env`

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores según tu entorno.

## Desarrollo

```bash
npm install
npm run dev
```

## Build de producción

```bash
npm run build
```

## Autenticación

- Si defines `VITE_AUTH_API_BASE_URL`, el login valida la credencial con tu backend.
- Si no hay backend, la app usa Google Identity Services directo desde el navegador.
- También puedes usar el login de demo para explorar la app.
