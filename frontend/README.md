# Frontend Vue

Frontend web del sistema AC Silver's GYM construido con  Vue y Javascript
## Requisitos

## Desarrollo

```bash
npm install
npm run dev
```

  

  

## Autenticación

- Si defines `VITE_AUTH_API_BASE_URL`, el login valida la credencial con tu backend.
- Si no hay backend, la app usa Google Identity Services directo desde el navegador.
- También puedes usar el login de demo para explorar la app.
- En desarrollo, el valor recomendado es `/api` para que Vite proxye al backend local.
