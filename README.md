# AC Silver's GYM

Aplicacion web para la gestion de un gimnasio. El proyecto esta dividido en un
frontend Vue/Vite y un backend FastAPI que se conecta a Supabase para consultar
y guardar la informacion del sistema.

## Requisitos

- Node.js 22 o superior
- Python 3.12 o superior
- Docker Desktop o Docker Engine con Docker Compose, si se usara Docker
- Credenciales de Supabase para el backend

## Activacion Manual

### Backend

 

```bash
cd backend
py -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python -m app.main
```

En Linux/macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

### Frontend
 

Instalar dependencias y levantar Vite:

```bash
cd frontend
npm install
npm run dev
```

Servicios locales:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentacion API: http://localhost:8000/docs

## Activacion con Docker

El backend toma sus variables desde `backend/.env`. Para el frontend, Docker
recibe variables `VITE_*` desde un archivo `.env` local en la raiz o desde el
entorno del sistema. Usa `.env.example`, `backend/.env.example` y
`frontend/.env.example` como plantillas, sin subir los `.env` reales al repo.

Variables opcionales para el build del frontend en `.env` de la raiz:

```env
VITE_APP_NAME=AC Silver's GYM
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_AUTH_MODE=backend
VITE_ENABLE_DEMO_LOGIN=true
VITE_SUPPORT_EMAIL=soporte@acsilversgym.com
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_LANDING_BUCKET=imageneslandingpage
VITE_SUPABASE_LANDING_FOLDER=landingpage
VITE_SUPABASE_ANON_KEY=tu-anon-key
VITE_SUPABASE_STORE_IMAGES_BUCKET=imagenestienda
```

Construir e iniciar frontend y backend:

```bash
docker compose up --build
```

Servicios con Docker:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentacion API: http://localhost:8000/docs

Detener los contenedores:

```bash
docker compose down
```

Eliminar tambien los volumenes:

```bash
docker compose down -v
```
