# AC Silver's GYM

Aplicacion-web para la ggestion de un gimnasio. El proyecto esta dividido en un
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

Para el cobro de membresías desde administración, ejecuta también
`backend/migrations/009_admin_client_stripe.sql` en el SQL Editor de Supabase.
En **Clientes > Nuevo cliente**, marca **Realizar el pago con Stripe al registrar**
para abrir Checkout, o registra sin marcarla y paga después desde los detalles.
Al volver de Stripe, el backend verifica el pago y permite activar la membresía.
El cobro desde el panel solo se ofrece para clientes con origen `ADMIN` y pago
pendiente. Los registros anteriores conservan su origen desconocido; esta
migración no los clasifica automáticamente.

Para el vencimiento automático, ejecuta
`backend/migrations/010_expire_memberships.sql` en el SQL Editor de Supabase.
La migración instala una tarea de Supabase Cron que revisa las membresías cada
minuto, cambia su estado a `VENCIDA` y deshabilita la cuenta si no tiene otra
membresía pagada y vigente. La fecha de fin incluye todo ese día en hora de Perú.
El backend también comprueba la vigencia en cada petición autenticada de un
cliente y bloquea el acceso al vencer, incluso con un token todavía válido.
La interfaz revalida las sesiones de clientes cada 30 segundos y al volver a la
pestaña, cierra la sesión vencida y muestra el motivo. Administración dispone
del filtro **Vencida**. Una membresía vencida requiere renovación; volver a
activar su pago histórico no extiende su vigencia.

Clientes, Usuarios, Planes, Horarios e Inicio cargan los recursos necesarios para
su sección y comparten respuestas recientes durante 30 segundos. El botón de
actualización fuerza una nueva consulta. Las lecturas del estado de Supabase
se ejecutan con un máximo de seis conexiones simultáneas; el estado anterior
se conserva si falla una tabla obligatoria. Las validaciones de acceso y de
vencimiento siguen aplicándose en el backend.

Inicio muestra las membresías activas, en trámite y vencidas, y los
pagos de la última membresía de cada cliente según su origen de registro.
Los enlaces del resumen abren Clientes con el filtro seleccionado. Los pagos
confirmados pendientes de activación se cuentan por separado de los pagos
pendientes; los registros antiguos sin origen o pago conocido no se clasifican
como pagados.

Para ejecutar las pruebas del backend, instala `backend/requirements-dev.txt`
y ejecuta `python -m pytest backend/tests` desde la raíz, con una
`AUTH_SECRET_KEY` de prueba de al menos 32 bytes. En `frontend`, ejecuta
`npm test` y `npm run build`.

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

### Estados de membresía y dashboard

Las membresías tienen únicamente `ACTIVO`, `VENCIDA` y `EN_TRAMITE` (mostrados como
Activo, Vencida y En trámite). El pago permanece separado como pagado o pendiente.
Registrar o renovar una membresía la deja en trámite; el pago confirmado permite
activarla y el vencimiento bloquea el acceso conservando el historial del pago.
El dashboard del administrador muestra tres KPI y gráficos con estos tres estados.

Después de la migración 010, ejecutar `backend/migrations/011_membership_states.sql`
en el SQL Editor de Supabase para normalizar los datos anteriores, restringir los
estados y actualizar la función de vencimiento programado. La migración conserva
los datos de pago y no activa cuentas pendientes.
