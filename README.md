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

## Inicio de sesión y registro con Google

El botón de Google funciona en `/login` y `/registro`. El backend verifica la
firma, el destinatario, el emisor, el vencimiento y el correo verificado de la
credencial. La cuenta queda vinculada mediante el identificador estable de
Google (`sub`) y la aplicación entrega su propia sesión firmada de una hora.
Los permisos se consultan en la base de datos.

- **Cliente nuevo:** selecciona Google, completa nombre, DNI, teléfono y plan,
  y continúa a Stripe. No necesita crear contraseña. El preregistro no inicia
  sesión: después del pago, la cuenta espera la activación del administrador.
- **Cliente registrado con Google:** entra con la misma cuenta únicamente
  después de que el administrador active su cuenta.
- **Cuenta existente con contraseña:** en Acceso, selecciona Google y confirma
  la contraseña del gimnasio una sola vez para vincularla. Después funcionan
  ambos métodos. El registro público no sobrescribe ni vincula cuentas existentes.

Las cuentas pendientes o inactivas no pueden acceder con Google ni con contraseña.
El backend comprueba el estado también al recuperar la sesión y en las rutas
protegidas, de modo que una sesión emitida antes de esta validación no permite
acceder mientras la cuenta siga pendiente. Confirmar el pago no activa la cuenta.

### 1. Crear el cliente de Google

En [Google Cloud Console — Clientes](https://console.cloud.google.com/auth/clients),
crea o selecciona un proyecto. Dentro de **Google Auth Platform**:

1. Completa **Branding / Información de la marca** con el nombre del gimnasio,
   correo de soporte y datos de contacto. Para producción, configura los enlaces
   de tu aplicación y de su política de privacidad.
2. En **Audience / Público**, usa **External / Externo** si entrarán clientes con
   cuentas personales. Mientras esté en pruebas, añade las cuentas que utilizarás
   como usuarios de prueba. Para abrir el acceso a tus clientes, publica la app
   cuando hayas completado la configuración que solicita Google.
3. En **Clients / Clientes**, crea un cliente de tipo **Web application / Aplicación web**.
4. En **Authorized JavaScript origins / Orígenes autorizados de JavaScript**, agrega
   cada origen desde el que abrirás el frontend. Ejemplos:

   ```text
   http://localhost
   http://localhost:5173
   https://NOMBRE-DEL-CODESPACE-5173.app.github.dev
   https://tu-dominio.com
   ```

   Copia el origen real desde la barra del navegador: protocolo, dominio y puerto
   si corresponde, sin `/login`, `/registro`, otras rutas ni comodines. Si Vite usa
   otro puerto, autoriza también ese origen. En Codespaces abre el puerto 5173 en
   una pestaña del navegador; si cambia el nombre del Codespace, actualiza el origen.
5. Copia el **Client ID / ID de cliente**, con formato
   `1234567890-xxxxx.apps.googleusercontent.com`.

Este flujo utiliza ventana emergente y callback JavaScript: no requiere configurar
URI de redirección, `GOOGLE_CLIENT_SECRET`, Firebase ni el proveedor Google de
Supabase Auth. Supabase se usa para almacenar las cuentas del gimnasio.
Consulta la [configuración oficial de Google Identity Services](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid)
y la [verificación de credenciales en el servidor](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token).

### 2. Configurar las variables de entorno

En **`backend/.env`**:

```dotenv
GOOGLE_CLIENT_ID=1234567890-xxxxx.apps.googleusercontent.com
AUTH_SECRET_KEY=pega-aqui-tu-clave-aleatoria
```

`GOOGLE_CLIENT_ID` sale del paso anterior. `AUTH_SECRET_KEY` es una clave privada
propia del gimnasio; no sale de Google. Genérala una sola vez con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copia el resultado completo. Conserva la misma clave en cada instancia del backend;
cambiarla cierra las sesiones existentes. Nunca uses un prefijo `VITE_` para esta
clave ni la copies al frontend. Al actualizar desde la implementación anterior,
los usuarios deben volver a iniciar sesión porque las sesiones antiguas no estaban firmadas.

Configura el **mismo Client ID** en el archivo correspondiente al frontend:

| Forma de ejecución | Archivo | Variable |
| --- | --- | --- |
| Docker Compose | `.env` de la raíz | `VITE_GOOGLE_CLIENT_ID=1234567890-xxxxx.apps.googleusercontent.com` |
| Vite con `npm run dev` | `frontend/.env` | `VITE_GOOGLE_CLIENT_ID=1234567890-xxxxx.apps.googleusercontent.com` |

Si utilizas ambas formas, completa ambos archivos. Para preparar el entorno manual
puedes copiar `frontend/.env.example` a `frontend/.env` si aún no existe.
En ejecución manual, conserva `VITE_AUTH_API_BASE_URL=/api` y configura
`VITE_BACKEND_URL=http://localhost:8000`; Vite reenvía las llamadas al backend.

Conserva también `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y las variables de Stripe
ya configuradas en `backend/.env`. Para que el retorno del pago funcione, establece
`FRONTEND_PUBLIC_URL` al origen real del frontend (localhost, Codespaces o producción).
Si el navegador llama a la API en otro origen, incluye el origen del frontend en
`CORS_ORIGINS`, separado por comas de los existentes.

### 3. Aplicar la migración de Supabase

En el **SQL Editor** del mismo proyecto Supabase, ejecuta el contenido de
[`backend/migrations/003_add_google_identity.sql`](backend/migrations/003_add_google_identity.sql).
Agrega `google_sub` y un índice único a `CLIENTES` y `USUARIO`; conserva las cuentas
existentes. No omitas este paso: la aplicación rechaza guardar una vinculación
si la columna no está disponible. También deben estar aplicadas las migraciones
anteriores del proyecto para pagos y horarios.

### 4. Reiniciar y comprobar

Con Docker, desde la raíz:

```bash
docker compose up --build -d
```

En ejecución manual, actualiza las dependencias del backend con
`pip install -r requirements.txt` desde `backend/` y reinícialo; reinicia también
`npm run dev` en `frontend/`. Vite incorpora las variables al arrancar o compilar:
con Docker, reiniciar sin reconstruir no actualiza el Client ID del frontend.

Abre `/registro`, selecciona una cuenta de prueba de Google, completa los datos y
continúa al pago. Activa la cuenta desde la administración y luego comprueba
`/login` con esa misma cuenta. Para una cuenta
anterior, usa su contraseña cuando se solicite vincular Google.

Si aparece **origin is not allowed**, revisa los orígenes del cliente de Google;
si aparece **invalid_client**, revisa el ID y el tipo Aplicación web. Si el backend
indica credencial inválida, verifica que ambos IDs coincidan y vuelve a seleccionar
la cuenta. Si no carga el botón, usa **Reintentar Google** y comprueba que el navegador
permita cargar `accounts.google.com` y abrir la ventana de Google.

## Correos de membresía con Gmail

El preregistro envía su confirmación de compra **cuando Stripe verifica que el pago
está completado y pagado**, tanto desde el webhook como al regresar del checkout.
Incluye cliente, código, plan, duración, promoción, importe en PEN, método, fecha y
referencia de pago. Aclara que la cuenta sigue pendiente de activación administrativa.
Un registro que todavía no ha pagado no recibe una confirmación de pago.

En **Clientes → Activar**, el administrador debe confirmar el modal
**«¿Estás seguro de la activación?» → «Sí, activar»**. Al guardar la activación se
envía un segundo correo con la vigencia y el enlace de acceso. Cancelar no cambia
la cuenta ni envía mensajes. El destinatario es el correo guardado del cliente:
para el preregistro con Google, es el correo verificado de esa cuenta de Google.

El backend envía mediante `smtp.gmail.com:465` con TLS y verificación del
certificado. Funciona desde Codespaces con una cuenta Gmail del gimnasio y puede
enviar a los correos de los clientes sin comprar un dominio propio.
[Configuración SMTP de Google](https://developers.google.com/workspace/gmail/imap/imap-smtp).

### Qué es una contraseña de aplicación

Es una clave de **16 caracteres** que genera Google para autorizar una aplicación
a acceder a tu cuenta. Aquí permite que el backend se autentique en Gmail y envíe
las notificaciones. Se genera en la cuenta **remitente del gimnasio**; los clientes
solo reciben los mensajes y no deben generar claves. Es independiente del inicio
de sesión con Google ya integrado en la web.

Para generarla, la cuenta debe tener activada la verificación en dos pasos.
Puedes revocarla sin cambiar tu contraseña habitual; Google también la revoca
cuando cambias la contraseña de la cuenta. Guarda esta clave únicamente en el
backend. [Documentación de Google](https://support.google.com/accounts/answer/185833?hl=es).

### Configuración

1. Inicia sesión con la cuenta Gmail que enviará los correos del gimnasio.
2. En [Seguridad de tu cuenta de Google](https://myaccount.google.com/security),
   activa **Verificación en dos pasos**.
3. Abre [Contraseñas de aplicaciones](https://myaccount.google.com/apppasswords),
   escribe `Silver Gym` como nombre y crea la contraseña. Copia la clave de
   16 caracteres que muestra Google. Si no aparece la opción, comprueba que
   la verificación en dos pasos esté activada; algunas cuentas administradas,
   cuentas con Protección Avanzada o configuradas solo con llaves de seguridad
   pueden tenerla restringida.
4. Agrega estas variables únicamente a **`backend/.env`**, conservando las existentes:

   ```dotenv
   GMAIL_EMAIL=correo-del-gimnasio@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   FRONTEND_PUBLIC_URL=https://tu-codespace-5173.app.github.dev
   ```

   Reemplaza los ejemplos por la cuenta remitente, su contraseña de aplicación y
   la URL real de tu web. La clave de ejemplo no funciona. Puedes pegar los
   16 caracteres sin espacios; el backend también acepta los grupos separados
   por espacios que muestra Google. Usa esta clave especial, no tu contraseña
   habitual de Google. No la incluyas en `VITE_*`, en el frontend ni en Git.

   `FRONTEND_PUBLIC_URL` sirve para el enlace `/login` y el retorno de Stripe.
   En local puedes usar `http://localhost:5173`; en Codespaces copia la URL
   pública del puerto **5173**, sin `/login` ni `/registro`. Si esta variable
   ya existe, actualízala sin duplicarla. El remitente se toma siempre de
   `GMAIL_EMAIL`; el nombre mostrado es `Silver Gym Surco` y puedes personalizarlo
   con `EMAIL_FROM_NAME`. Los identificadores de Google del login se conservan.
5. Si todavía no la aplicaste, en **Supabase → SQL Editor** ejecuta
   [`backend/migrations/004_membership_email_notifications.sql`](backend/migrations/004_membership_email_notifications.sql).
   Deben estar aplicadas también las migraciones anteriores. La nueva tabla es
   privada: el backend usa `SUPABASE_SERVICE_ROLE_KEY` para escribir y procesar
   los envíos; la clave anónima no tiene acceso a ella.
6. Reinicia el backend y actualiza el frontend. Con Docker:

   ```bash
   docker compose up --build -d
   ```

Con ejecución manual, reinicia el proceso del backend. Si vienes de la versión
con Resend, las variables `RESEND_API_KEY`, `EMAIL_FROM` y `EMAIL_REPLY_TO` ya no
se utilizan y puedes quitarlas de tu `.env`. La cola existente sigue funcionando
sin una migración adicional; los correos pendientes salen desde la cuenta Gmail
configurada y los ya enviados conservan su estado.

### Reintentos y comprobación

Configura Gmail y aplica la migración **antes de recibir nuevos pagos**. Si faltan
las variables, el pago y la activación funcionan, pero se informa que el servicio
de correo no está configurado; no se crean envíos históricos automáticamente.

La tabla `membership_email_notifications` conserva un envío por membresía y
evento (`payment` o `activation`), con el contenido, intentos y estado.
Por compatibilidad, la columna `resend_id` conserva su nombre y ahora almacena
el `Message-ID` del correo de Gmail.
El backend procesa la cola mientras está encendido, reintenta los fallos con
espera creciente y recupera envíos interrumpidos. Un correo registrado como
enviado no vuelve a enviarse ante webhooks o activaciones repetidas. Los reintentos
conservan un `Message-ID` estable para identificar el mismo evento. SMTP no ofrece
la idempotencia de Resend: si Gmail acepta el correo pero la conexión se pierde
antes de recibir la confirmación, o falla la base de datos antes de guardar el
resultado, un reintento podría producir un duplicado.

Si el envío falla después de activar, la cuenta permanece activa y la interfaz
lo informa. **Notificar activación** permite solicitar el correo de nuevo después
de configurar el servicio, sin cambiar la vigencia; si ya se envió, no lo duplica.
Los trabajos en espera mantienen los datos de la compra y usan el remitente Gmail
actual, por lo que puedes corregir la configuración sin recrear las compras.
Si no se puede guardar el correo del pago, el webhook responde 503 para que
Stripe repita la confirmación; el pago guardado no se revierte.

Prueba con un pago de Stripe en modo test: debe llegar la confirmación y la cuenta
debe seguir bloqueada. En administración, cancela primero el modal y comprueba
que nada cambie; luego confirma y verifica el correo de activación y el acceso.
Revisa **Enviados** en la cuenta Gmail remitente y la bandeja de entrada o spam del
destinatario. El estado enviado significa que Gmail aceptó el mensaje para su
entrega. Si hay un error, revisa `last_error` en la cola o los logs del backend.
Los errores de autenticación requieren revisar la cuenta y la contraseña de
aplicación; si Google la revocó, genera otra y reinicia el backend. Gmail puede
limitar temporalmente los envíos al alcanzar las cuotas de la cuenta.
