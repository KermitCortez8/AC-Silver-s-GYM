# AC Silver's GYM

Aplicacion web para la gestion de un gimnasio. El proyecto esta dividido en un
frontend Vue/Vite y un backend FastAPI que se conecta a Supabase para consultar
y guardar la informacion del sistema.

## Requisitos

- Node.js 22 o superior
- Python 3.12 o superior
- Docker Desktop o Docker Engine con Docker Compose 2.17 o superior, si se usara Docker
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

El backend utiliza la red `bridge` incorporada de Docker (`docker0`). El frontend
comparte esa conexión mediante `network_mode: service:backend`; Nginx consulta
la API en `127.0.0.1:8000`. Los puertos 5173 y 8000 se publican en el servicio
backend porque ambos contenedores comparten el mismo espacio de red.
Esta configuración está versionada y no requiere reglas manuales para
`br-acsgym`, scripts de firewall ni direcciones IP fijas de contenedores.
[Referencia de Docker Compose](https://docs.docker.com/reference/compose-file/services/#network_mode).

Si vienes de la configuración anterior, ejecuta `docker compose down` sin `-v`
y luego `docker compose up --build -d`. Esto recrea los contenedores conservando
los volúmenes. Para aplicar cambios posteriores, usa `docker compose up --build -d`.

En Codespaces, abre el puerto **5173** desde la pestaña **Puertos** para acceder
a la aplicación. Las consultas a `/api` pasan por el mismo puerto.

El healthcheck del frontend comprueba también `/api/health` a través de Nginx.
`/health` y `/api/health` comprueban la carga de Supabase (con una caché de
5 segundos). Devuelven HTTP 503 si faltan credenciales o falla la base de datos;
el backend ya no cambia automáticamente a almacenamiento en memoria.
Si falla, revisar `docker compose logs --tail=50 frontend backend`. Un timeout
`while connecting to upstream` indica un problema de conexión entre contenedores;
`while reading response header` indica que el backend no respondió a tiempo.
El fallo anterior se debía a reglas antiguas con `FORWARD DROP` que permitían
`docker0`, pero bloqueaban `br-acsgym`. Esta configuración utiliza `docker0`
directamente, por lo que no depende de las excepciones temporales del host.

Servicios con Docker:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentacion API: http://localhost:8000/docs

La portada consulta `/api/gym/horarios-publicos`: muestra horarios activos,
rutinas y cupos, y los actualiza cada 30 segundos mientras la página está visible.
Si falla una consulta de horarios o planes, muestra un aviso y permite reintentar.
La sincronización de la sesión también informa qué secciones no se actualizaron.

Detener los contenedores:

```bash
docker compose down
```

Eliminar tambien los volumenes:

```bash
docker compose down -v
```
