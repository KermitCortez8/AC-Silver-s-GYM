# AC Silver's GYM 

Aplicacion web para Administracion de Proyectos mediante frontend (Javascript) y backend (python)

## Docker Compose

Requisitos:

- Docker Desktop o Docker Engine con Docker Compose.

Construir e iniciar frontend y backend:

```bash
docker compose up --build
```

Servicios:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentacion API: http://localhost:8000/docs

Detener los contenedores:

```bash
docker compose down
```

Los datos de `backend/db` se conservan en el volumen Docker `backend_data`. Para eliminar tambien ese volumen:

```bash
docker compose down -v
```

Variables opcionales para el build del frontend pueden definirse en un archivo `.env` en la raiz:

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_ENABLE_DEMO_LOGIN=true
VITE_SUPPORT_EMAIL=soporte@acsilversgym.com
```

## Instalacion local

```bash
# Navega a la carpeta frontend
cd frontend

# Instala dependencias
npm install

# Inicia servidor de desarrollo
npm run dev
```
```bash
# Navega a  Backend
cd backend

# Instala dependencias


py -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python -m app.main
```

