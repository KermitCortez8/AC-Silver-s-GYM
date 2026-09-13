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

## Asistencias

Antes de usar el nuevo control, abre **Supabase → SQL Editor → New query**, copia
`backend/migrations/005_harden_attendance.sql` y pulsa **Run**. Requiere las
migraciones anteriores y el esquema que ya utiliza el proyecto. Después reinicia
el backend y el frontend (en Docker: `docker compose up --build`). No necesitas
variables nuevas: el backend debe tener `SUPABASE_SERVICE_ROLE_KEY`, nunca en
una variable `VITE_`.

- Solo el rol `admin` registra entradas, salidas, correcciones y anulaciones.
  Los clientes consultan únicamente su propia asistencia; `staff` y `trainer`
  no tienen acceso al control de asistencia.
- En **Asistencias → Control de hoy**, busca por DNI de 8 dígitos. La ficha muestra
  la membresía y los horarios, colocando primero los de hoy. La entrada exige
  cuenta activada, membresía activa/pagada/vigente, matrícula activa, horario
  habilitado, día correcto y hora dentro del horario, desde el inicio hasta antes
  de la hora final. El servidor usa `America/Lima` para fechas y horas.
- Una asistencia corresponde al cliente, la matrícula y el día. No se permiten
  duplicados ni dos entradas abiertas del mismo cliente. El aforo cuenta las
  personas que siguen dentro, no todas las visitas acumuladas del día.
- **Entradas sin salida** también muestra visitas pendientes de días anteriores.
  La salida puede registrarse aunque la membresía haya vencido después de entrar;
  admite cambio de fecha, conserva la primera salida y nunca precede a la entrada.
- **Historial** filtra antes de paginar y exporta a Excel todos los resultados de
  los filtros aplicados. Las correcciones requieren motivo y conservan el autor,
  las horas anteriores y las nuevas. Una corrección documentada permite ajustar
  una visita histórica aunque después haya cambiado la matrícula o la membresía.
  La anulación conserva el registro y deja de contarlo en los indicadores.
- **Mi asistencia** es de consulta: semana con fechas reales e historial completo.
  La semana refleja las matrículas actuales; las visitas a horarios anteriores
  siguen disponibles en el historial.

La migración conserva el historial y añade auditoría y control de versiones.
Las escrituras se ejecutan en una transacción para evitar dobles registros entre
procesos; las cuentas del navegador no acceden directamente a `ASISTENCIA`.

Referencias visuales: distribución de indicadores de
[Fitness Management Dashboard, de Ibrahim](https://dribbble.com/shots/26957541-Fitness-Management-Dashboard-UI-for-Smarter-Decisions)
y claridad de las fichas de
[Mindbody Check-in](https://www.mindbodyonline.com/en-gb/business/class-check-in-app).
El diseño conserva los colores y temas de Silver's Gym; el registro lo realiza
exclusivamente el administrador.

## Correos de horarios y clases

Los recordatorios y los reintentos de confirmación de matrícula se ejecutan en
**Supabase Cron + Edge Function**, aunque Codespaces esté apagado. Sigue la
[guía de configuración de Supabase](docs/supabase-recordatorios.md): incluye las
migraciones 006/007, los secretos de Gmail, el despliegue y una comprobación que
no envía correos. La programación queda pausada hasta completar esa configuración.

- Cuando el administrador agrega una clase al horario de un cliente, se guarda
  la matrícula y su aviso en la misma transacción. Se intenta enviar inmediatamente
  y la pantalla informa si el correo salió o quedó pendiente. El correo incluye
  la clase, día semanal, horario, hora de Perú y enlace a **Mi horario**.
- Cada matrícula activa recibe un recordatorio semanal programado una hora antes
  del inicio. Supabase revisa las clases cada minuto, incluyendo las que
  empiezan después de medianoche. Solo recuerda clases de clientes activados con
  membresía pagada y vigente en la fecha de la clase.
- Antes del envío se revisan de nuevo matrícula, horario y correo del cliente.
  Se omiten clases canceladas, deshabilitadas, cambiadas o que ya comenzaron.
  Una matrícula creada cuando falta menos de una hora recibe la confirmación
  administrativa, pero no un recordatorio cuya hora de envío ya pasó.
- La cola privada `schedule_email_notifications` conserva los pendientes y usa
  una clave por matrícula/clase y una reserva temporal para evitar que dos
  procesos envíen simultáneamente el mismo aviso. Un fallo de Gmail se reintenta
  sin deshacer la matrícula. El campo `last_error` permite revisar fallos.

El backend conserva el envío inmediato cuando el administrador inscribe al
cliente, pero ya no ejecuta el bucle de recordatorios. Ambos emisores comparten
la reserva de la misma cola. Los pagos y las activaciones mantienen su integración
existente de Gmail en el backend.

Una vez activado Cron, el proyecto de Supabase debe estar operativo para procesar
los recordatorios. Tras una interrupción, se recuperan los que aún están dentro
de la hora previa; los de clases ya iniciadas se descartan. Los avisos pueden
demorarse por el tamaño de la cola, reintentos o disponibilidad de Gmail. SMTP no
ofrece confirmación idempotente: si Gmail acepta un mensaje y se pierde la
respuesta, un reintento excepcional puede repetirlo.
