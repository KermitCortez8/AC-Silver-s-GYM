# AC Silver's GYM

Aplicacion-web para la ggestion de un gimnasio. El proyecto esta dividido en un
frontend Vue/Vite y un backend FastAPI que se conecta a Supabase para consultar
y guardar la informacion del sistema.

## Requisitos

- Node.js 22 o superior
- Python 3.12 o superior
- Docker Desktop o Docker Engine con Docker Compose 2.17 o superior, si se usara Docker
- Credenciales de Supabase para el backend

## Integración continua y despliegue

Al fusionar un PR hacia `main`, GitHub Actions ejecuta esta secuencia:

1. Construye las imágenes Docker del backend y frontend, arranca ambos
   contenedores y verifica el backend, la web y el proxy de Nginx.
2. Ejecuta las pruebas existentes de Python, Node.js y Deno en paralelo.
3. Si todas pasan, despliega el frontend en Vercel y solicita el despliegue
   del mismo commit en Render.

Si falla Docker o alguna prueba, los despliegues no se ejecutan. La validación
usa `docker-compose.ci.yml`, sin archivos `.env` ni credenciales de producción.
Comprueba el arranque y el proxy; no comprueba una conexión real a Supabase.
El endpoint `/api/health` devuelve el 503 esperado por falta de credenciales.

Los despliegues conservan sus mecanismos actuales: Vercel compila el frontend
y Render recibe su Deploy Hook. Este workflow no publica imágenes Docker ni
cambia la configuración del servicio en Render. La aceptación del hook no
confirma que Render haya terminado el despliegue.

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

En un clon nuevo o en otro Codespace, prepara los archivos de configuración:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Completa `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en `backend/.env`.
En `.env`, completa `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` del mismo
proyecto. La clave privada se configura únicamente en `backend/.env`.
Para los pagos, configura también las variables de Stripe de `backend/.env`.
Los archivos `.env` reales no se incluyen en Git; cada Codespace necesita sus
credenciales. No sobrescribas los archivos si ya los configuraste.



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

### Error al extraer una capa de Docker

Si la construcción falla con `failed to get reader from content store`,
`content digest ... not found` o `parent snapshot ... does not exist`, Docker
puede tener referencias a capas que ya no existen en su caché. Para recuperar, ejecuta desde la raíz del proyecto:

```bash
docker builder prune --all --force
docker compose build --pull --no-cache
docker compose up -d --no-build
docker compose ps
```

 