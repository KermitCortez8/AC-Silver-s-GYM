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

Construir e iniciar frontend y backend:

```bash
docker compose up --build
```

La red usa el nombre de interfaz fijo `br-acsgym`, de modo que las reglas del
firewall del host no queden apuntando a una interfaz eliminada al recrear la red.

Si ya existía una red creada con una versión anterior, aplica el nuevo nombre una
sola vez con `docker compose down` (sin `-v`) y vuelve a iniciar. Los volúmenes se
conservan.

El healthcheck del frontend comprueba también `/api/health` a través de Nginx.
Si falla, revisar `docker compose logs --tail=50 frontend backend`. Un timeout
`while connecting to upstream` indica un problema de conexión entre contenedores;
`while reading response header` indica que el backend no respondió a tiempo.
La coexistencia de un filtro antiguo con política `FORWARD DROP` y las reglas
modernas de Docker puede bloquear conexiones incluso si ambos contenedores están
activos ([documentación de Docker](https://docs.docker.com/engine/network/firewall-nftables/)).

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
