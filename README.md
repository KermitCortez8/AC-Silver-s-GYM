# AC Silver's GYM

Aplicación web para gestionar clientes, membresías, pagos, horarios, asistencias,
rutinas, inventario y tienda de un gimnasio. Utiliza Vue 3/Vite/Pinia, una API
FastAPI y Supabase. Tanto el frontend como el backend están contenerizados con
Docker: cada uno tiene su Dockerfile y Docker Compose coordina ambos servicios.
Incluye pruebas automatizadas y publicación mediante GitHub Actions en Vercel y Render.

## Arquitectura

El sistema combina un backend FastAPI conectado a Supabase y un frontend
Vue 3/Vite con Pinia. Ambos se organizan en cuatro capas para separar la interfaz,
los casos de uso, las reglas de negocio y los servicios externos.

| Capa | Backend | Frontend | Responsabilidad |
| --- | --- | --- | --- |
| Presentación | `backend/presentation/` | `frontend/src/presentation/` | Rutas HTTP y permisos en la API; pantallas, componentes, navegación y estilos en la web. |
| Aplicación | `backend/application/` | `frontend/src/application/` | Coordina casos de uso, operaciones por módulo, estado, sesión y sincronización mediante contratos de servicios y repositorios. |
| Dominio | `backend/domain/` | `frontend/src/domain/` | Contiene reglas, modelos, cálculos y validaciones del negocio. |
| Infraestructura | `backend/infrastructure/` | `frontend/src/infrastructure/` | Implementa persistencia, transporte HTTP, almacenamiento e integraciones externas. |

En el **backend**, `app/main.py` inicia el servidor y `app/bootstrap.py` conecta
servicios, puertos y adaptadores. `GymService` coordina operaciones de clientes,
membresías, asistencia, horarios, inventario y tienda; las reglas se ejecutan en
el dominio. Aplicación y dominio no importan FastAPI ni implementaciones de
infraestructura. Los repositorios se encargan de persistir los cambios: matrículas
y asistencias utilizan sus RPC específicas, y las demás mutaciones soportadas
se confirman de forma atómica mediante `commit_gym_transaction`.

En el **frontend**, `src/bootstrap.js` instala los adaptadores para cada instancia
de Pinia. Las vistas delegan sus acciones en composables y servicios de aplicación;
`gymStore` mantiene una interfaz común sobre operaciones separadas por módulo.
Los repositorios de infraestructura resuelven las solicitudes HTTP. Al cambiar
de sesión se limpian los datos y cachés de negocio y se descartan respuestas
pendientes de la sesión anterior.

### Contenedores e infraestructura

[Docker Compose](docker-compose.yml) construye y ejecuta dos contenedores,
uno para el backend y otro para el frontend, a partir de sus respectivas imágenes:

- **Backend:** [Python 3.12 slim](backend/Dockerfile), dependencias de ejecución y
  Uvicorn en el puerto 8000, con usuario `appuser` sin privilegios de root.
- **Frontend:** [compilación con Node 22 y Vite](frontend/Dockerfile); la imagen
  final contiene la web estática y Nginx 1.27, ejecutado como usuario `nginx` en
  el puerto 8080. Node queda en la etapa de construcción.

Nginx y FastAPI comparten el espacio de red mediante
`network_mode: service:backend`. Ambos puertos se publican en el servicio
`backend`: `5173:8080` para la web y `8000:8000` para la API.
[Nginx](frontend/nginx.conf) sirve la SPA y reenvía `/api/` a
`http://127.0.0.1:8000`, conservando el prefijo. Evita cachear `index.html` y
cachea los recursos compilados con hash durante un año.

El volumen `backend_data` conserva `/app/db`, incluida la carpeta de imágenes
locales. Los datos de negocio permanecen en **Supabase/PostgreSQL externo**;
Compose no incluye un contenedor de base de datos ni aplica migraciones SQL.
Las imágenes pueden almacenarse en Supabase Storage, según la configuración.
Google, Stripe y Resend se integran mediante adaptadores del backend; los
recordatorios de clases usan además una Edge Function y Cron de Supabase.

| Modo | Web | API y conexión |
| --- | --- | --- |
| Desarrollo manual | Vite en `localhost:5173`. | Uvicorn en `localhost:8000`; Vite redirige `/api` al backend. |
| Docker Compose | Nginx accesible en `localhost:5173`. | Uvicorn en `localhost:8000`; Nginx redirige `/api/` por la red compartida. |
| Publicación configurada | Archivos estáticos en Vercel. | Servicio Python en Render; la web usa su URL pública terminada en `/api`. |

Los Dockerfiles tienen etapas `test` para CI. El despliegue configurado en
Vercel y Render utiliza sus runtimes propios; las imágenes Docker se usan para
Compose y validación automatizada.

La separación conserva algunos límites: `GymService` y `gymStore` siguen siendo
fachadas centrales, el dominio del backend comparte estado entre módulos, la
transacción general usa bloqueos de tablas y algunos listados aún se consultan
completos. Las pruebas de arquitectura verifican las dependencias entre capas;
los detalles, decisiones de persistencia y límites actuales están en el
[documento de arquitectura](.specify/docs/arquitectura.md).

La persistencia actual requiere las migraciones
[014](backend/migrations/014_preserve_business_fields.sql),
[015](backend/migrations/015_atomic_gym_transactions.sql) y
[016](backend/migrations/016_transaction_sequence_permissions.sql), aplicadas
sobre el esquema previo compatible antes de desplegar este backend.

## Requisitos

- Para ejecución manual: Node.js 22 o superior y Python 3.12 o superior.
- Para contenedores: Docker Desktop o Docker Engine con Docker Compose 2.17 o superior.
- Un proyecto Supabase con el esquema y las migraciones que requiere el backend.
- Deno 2 para comprobar la Edge Function y sus pruebas, si se trabaja en ese componente.

Las migraciones presuponen un esquema existente. Consultar sus dependencias en
[arquitectura](.specify/docs/arquitectura.md) y el
[DoD](.specify/docs/DoD.md); no ejecutar todos los SQL indiscriminadamente.

## Configuración del entorno

Crea o completa los siguientes archivos con los valores de tu proyecto. Los
archivos de entorno locales quedan fuera de Git. El repositorio no incluye
plantillas `.env.example` en la raíz ni en `backend/`.

**`backend/.env`**, tanto para ejecución manual como para Docker:

```dotenv
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<clave-service-role-del-proyecto>
AUTH_SECRET_KEY=<secreto-aleatorio-de-al-menos-32-bytes>
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
FRONTEND_PUBLIC_URL=http://localhost:5173
```

Sustituye los marcadores antes de arrancar. Puedes generar `AUTH_SECRET_KEY` con
`python -c "import secrets; print(secrets.token_urlsafe(48))"`. La clave
`service_role` se usa únicamente en el servidor para las operaciones y RPC
protegidas; nunca se incorpora a una variable `VITE_*`.

**`.env` en la raíz**, para los argumentos públicos de Docker Compose:

```dotenv
VITE_SUPABASE_URL=https://<proyecto>.supabase.co
VITE_SUPABASE_ANON_KEY=<clave-anon-publica-del-mismo-proyecto>
```

Compose fija `VITE_AUTH_API_BASE_URL=/api`. Para desarrollo manual, configura
**`frontend/.env`** con esas mismas dos variables públicas y añade
`VITE_AUTH_API_BASE_URL=/api`. Vite usa su proxy hacia `http://localhost:8000`;
`VITE_BACKEND_URL` permite cambiar el destino de desarrollo.

Según la función que utilices, completa también:

| Integración | Backend | Frontend |
| --- | --- | --- |
| Google | `GOOGLE_CLIENT_ID`. | El mismo ID en `VITE_GOOGLE_CLIENT_ID`. |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_MODE`. | El backend coordina el checkout y la confirmación. |
| Correo | `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`. | Los enlaces usan `FRONTEND_PUBLIC_URL` del backend. |
| Imágenes | `SUPABASE_STORE_IMAGES_BUCKET` o configuración de almacenamiento local. | URL pública de Supabase y configuración pública de buckets. |

Las variables públicas del frontend se incorporan al compilar. En Docker se
leen desde los argumentos definidos en Compose, y cambiarlas requiere
reconstruir la imagen. Las credenciales del backend se inyectan al arrancar.
El detalle de prioridades, almacenamiento, notificaciones y secretos de la Edge
Function está en [arquitectura](.specify/docs/arquitectura.md).

## Integración continua y despliegue

Los PR a `develop` y `main` ejecutan
[validación de componentes](.github/workflows/pr-validation.yml): imágenes de
prueba backend/frontend, compilación de producción, comprobaciones Deno y un
PostgreSQL 16 desechable para contratos y concurrencia. Otro
[workflow documental](.github/workflows/spec-docs.yml) verifica la integración
Spec Driven y sus documentos.

Al fusionar un PR hacia `main`,
[GitHub Actions](.github/workflows/ci-cd.yml) ejecuta esta secuencia:

1. Construye las imágenes Docker del backend y frontend, arranca ambos
   contenedores y verifica el backend, la web y el proxy de Nginx.
2. Ejecuta las pruebas de Python y Node.js dentro de los targets `test` de sus
   Dockerfiles, y las pruebas de Deno en paralelo. Las imágenes de producción
   no incluyen las dependencias ni los archivos exclusivos de pruebas.
3. Si todas pasan, despliega el frontend en Vercel y solicita el despliegue
   del mismo commit en Render.

Si falla Docker o alguna prueba, los despliegues no se ejecutan. La validación
usa `docker-compose.yml` con un archivo temporal de CI y una clave de prueba,
sin credenciales de producción.
Comprueba el arranque y el proxy; no comprueba una conexión real a Supabase.
El endpoint `/api/health` devuelve el 503 esperado por falta de credenciales.

Los despliegues conservan sus mecanismos actuales: Vercel compila el frontend
y Render recibe su Deploy Hook. Este workflow no publica imágenes Docker ni
cambia la configuración del servicio en Render. La aceptación del hook no
confirma que Render haya terminado el despliegue.

GitHub Actions necesita únicamente los secretos de despliegue
`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` y
`RENDER_DEPLOY_HOOK_URL`. Las variables de la aplicación se configuran en
Vercel (Production) y Render. Antes de compilar, `vercel pull` recupera la
configuración y las variables de producción de Vercel; el hook de Render
conserva las variables del servicio y solicita el mismo commit probado.
El proyecto de Vercel debe tener `Root Directory` en `frontend`. Configura allí
`VITE_AUTH_API_BASE_URL` con la URL de Render terminada en `/api`: los rewrites
de [vercel.json](frontend/vercel.json) sirven la SPA y no hacen proxy al backend.
En Render, configura `CORS_ORIGINS` con el origen de Vercel y
`FRONTEND_PUBLIC_URL` con la URL del frontend. [render.yaml](render.yaml) define
el runtime Python, Uvicorn y la sonda `/health`.

Los workflows no aplican migraciones ni despliegan la Edge Function o activan
Cron; estos recursos de Supabase se configuran aparte.
Mantén desactivados los despliegues automáticos por Git en ambas plataformas
para que las publicaciones dependan de este workflow.

## Ejecución manual

Prepara los archivos de entorno anteriores antes de iniciar los servicios.

### Backend

En Windows (PowerShell):

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m app.main
```

En Linux/macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.main
```

`requirements.txt` contiene las dependencias de ejecución usadas por Docker y
Render. `requirements-dev.txt` incluye esas dependencias y añade pytest, httpx y
flake8 para desarrollo y CI.

Para ejecutar las pruebas y la comprobación de errores desde `backend/`:

```bash
python -m pytest tests/ -q
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Frontend

En otra terminal, instalar dependencias y levantar Vite:

```bash
cd frontend
npm ci
npm run dev
```

Servicios locales:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentación API: http://localhost:8000/docs

## Ejecución con Docker

Desde la raíz, después de configurar `.env` y `backend/.env`:

```bash
docker compose up --build --detach --wait
docker compose ps
```

- Web y proxy de la API: http://localhost:5173
- API directa: http://localhost:8000
- Documentación de la API: http://localhost:8000/docs

El frontend espera a que el backend esté saludable. La sonda `/health` comprueba
acceso a Supabase y la del frontend consulta también `/api/health` a través de
Nginx. Un 503 indica que la comprobación de la base no está disponible; `GET /`
solo confirma que el proceso HTTP responde. Los dos servicios usan
`restart: unless-stopped`.

Para revisar los logs y detener los servicios conservando el volumen:

```bash
docker compose logs --tail=100 backend frontend
docker compose down
```

Compose no monta el código fuente. Tras modificarlo, vuelve a ejecutar
`docker compose up --build --detach --wait`. `docker compose down -v` elimina
también `backend_data` y sus archivos locales, incluidas las imágenes que se
hayan guardado allí; no elimina la base externa de Supabase.

### Error al extraer una capa de Docker

Si la construcción falla con `failed to get reader from content store`,
`content digest ... not found` o `parent snapshot ... does not exist`, puede
haber referencias de caché a capas inexistentes. Para reconstruir sin usar esa
caché, ejecuta desde la raíz:

```bash
docker compose build --pull --no-cache
docker compose up --detach --wait --no-build
docker compose ps
```

## Asistencia general del gimnasio

La vista de Asistencias incluye «Por horarios», «Gimnasio general» e «Historial».
Las visitas generales requieren una cuenta activada y una membresía pagada y
vigente, y permiten registrar nuevas visitas el mismo día al cerrar la anterior.
Ambos tipos de asistencia comparten el aforo y la regla de una sola entrada
abierta por cliente. El cliente consulta sus visitas en su calendario e historial.

Antes de usar el registro general, ejecuta
[`backend/migrations/013_general_attendance.sql`](backend/migrations/013_general_attendance.sql)
en el SQL Editor de Supabase, después de la migración `005_harden_attendance.sql`.
No se crea una tabla nueva: se reutiliza `ASISTENCIA`, con `servicio = 'gimnasio'`
y matrícula/horario nulos. La migración actualiza la función `guardar_asistencia`
y conserva los registros, la auditoría y los permisos existentes. Puede ejecutarse
de nuevo sin duplicar datos. Luego publica el backend y frontend actualizados.
