# AC Silver's GYM

Aplicación web para la gestión de AC Silver's GYM. Centraliza el registro de
clientes, las membresías, los horarios, el seguimiento del entrenamiento y el
control de inventario y tienda. Ofrece funciones para administración, personal,
entrenadores y clientes, con acceso según el perfil de cada usuario.

## Módulos del sistema

| Módulo | Descripción |
| --- | --- |
| Registro | Permite el preregistro público y el alta administrativa de clientes, con la continuación del proceso de pago y activación. |
| Autenticación y usuarios | Gestiona el acceso con contraseña o Google, las sesiones, los perfiles y los roles de las cuentas. |
| Clientes | Reúne el directorio, la búsqueda y la edición de datos personales, junto con la consulta de membresías y acciones de cada ficha. |
| Planes y membresías | Administra los planes, sus precios y duración, y las membresías de los clientes con sus estados y vigencia. |
| Promociones | Gestiona descuentos vinculados a planes, fechas de validez, condiciones y cupos aplicables. |
| Horarios | Organiza los horarios de servicio, su disponibilidad y los cupos de las actividades del gimnasio. |
| Matrículas | Permite inscribir o dar de baja a un cliente en un horario, comprobando su membresía y los cupos disponibles. |
| Entrenador y rutinas | Ofrece el resumen del entrenador, el catálogo de rutinas, la asignación a matrículas y el seguimiento del progreso. |
| Asistencias | Controla entradas y salidas generales o por horario, aforo, correcciones y consulta del historial del cliente. |
| Inventario | Administra artículos y equipos, categorías, ubicaciones, estado operativo, stock de reserva y movimientos de entrada, salida o ajuste. |
| Tienda | Presenta productos con imágenes, precios y disponibilidad; permite gestionar el catálogo, el carrito y el proceso de compra según el perfil. |
| Pedidos y ventas | Registra y consulta pedidos, sus estados, entregas y cancelaciones, y permite revisar las salidas por venta. |
| Pagos | Centraliza el historial de pagos de membresía, la confirmación manual o mediante Stripe y la coordinación del pago de pedidos. |
| Paneles y configuración | Muestra resúmenes y accesos según el perfil, y permite administrar parámetros operativos como las capacidades del gimnasio. |
| Sitio público | Presenta los servicios del gimnasio, información institucional, preguntas frecuentes y accesos al registro e inicio de sesión. |

Los módulos se relacionan entre sí: registro, membresías y pagos participan en
la activación del cliente; horarios, matrículas y asistencias organizan su
participación en las actividades; inventario, tienda y pedidos coordinan las
existencias y las ventas. Un módulo puede reunir varias pantallas o compartir
una vista con otros módulos.

 
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
Para 2026

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
