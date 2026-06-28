# AC Silver's GYM 

Aplicacion web para Administracion de Proyectos mediante frontend (Javascript) y backend (python)

## Conexion con Supabase

La arquitectura recomendada para este repo es:

```txt
Supabase -> Backend FastAPI -> Frontend Vue
```

El frontend consume el backend local con `frontend/.env`:

```env
VITE_AUTH_MODE=backend
VITE_AUTH_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

Las credenciales de Supabase van solo en `backend/.env`:

```env
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

Antes de iniciar la app, ejecuta el schema de Supabase que tienes para estas tablas: `CLIENTES`, `MEMBRESIA`, `PLANES_MEMBRESIA`, `USUARIO`, `INVENTARIO`, `TIENDA_PRODUCTOS`, `VENTAS`, `DETALLE_VENTA`, `ASISTENCIA`, `CATALOGO_RUTINA` y `HORARIO`.

Ejecuta tambien los `GRANT` de `supabase/schema.sql` para `service_role`; si no, PostgREST devolvera `permission denied` aunque las credenciales sean correctas y las tablas existan. Si usas `SUPABASE_ANON_KEY` en vez de `SUPABASE_SERVICE_ROLE_KEY`, tambien necesitas los `GRANT` y politicas RLS para `anon`.

Si ya ejecutaste el schema base y solo necesitas persistencia para configuracion, horarios de servicio, matriculas, tickets y movimientos de inventario, ejecuta `supabase/persistence_modules.sql` en el SQL Editor de Supabase.

## Instalacion y  Despligue

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

python -m venv .venv / py -m venv .venv
source .venv/bin/activate  /  .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

