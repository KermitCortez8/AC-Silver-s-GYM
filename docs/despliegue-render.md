# Paso 1: API en Render conectada a Supabase

## Arquitectura

La base de datos permanece en Supabase. Render ejecuta FastAPI y se conecta
a la API REST de Supabase mediante HTTPS. No se crea una base Render Postgres
ni se copian los datos del gimnasio.

## Git Flow

1. Implementar la configuración en `feature/render-backend`, desde `develop`.
2. Validarla y hacer merge con `--no-ff` a `develop`.
3. Publicar ambas ramas y desplegar `develop` en el entorno de integración
   de Render. Verificar `/health` antes de continuar con el frontend.
4. Preparar Vercel en otra feature desde `develop` e integrarla después de
   validar los cambios.
5. Con ambos servicios probados, preparar una nueva `release/<version>` desde
   `develop`. Tras la aceptación, integrar en `main`, crear un nuevo tag y
   reintegrar en `develop`. El tag publicado `v1.1.0` permanece intacto.

Este servicio es el entorno de integración de la review. Su rama es `develop`
y sus despliegues son manuales. El despliegue de una release se hace desde su
rama durante la aceptación y desde `main` tras el cierre. Si se cambia la rama
de este servicio, actualizar también `branch` en `render.yaml` para que una
sincronización del Blueprint no deshaga el cambio.

## Crear el servicio con el Blueprint

Después de publicar los cambios en GitHub:

1. En Render, seleccionar **New > Blueprint** y conectar el repositorio
   `KermitCortez8/AC-Silver-s-GYM`.
2. Seleccionar `develop` como rama del Blueprint y `render.yaml` como archivo.
3. Revisar el servicio `ac-silvers-gym-api-review`, plan **Free**.
4. Completar los dos valores solicitados:

   | Variable | Valor |
   | --- | --- |
   | `SUPABASE_URL` | URL HTTPS del proyecto Supabase usado para la demo |
   | `SUPABASE_SERVICE_ROLE_KEY` | Clave privada `service_role` del mismo proyecto |

   Copiarlos desde la configuración del proyecto o el archivo local
   `backend/.env`. No pegarlos en chats ni subir el `.env` a Git.
5. Render genera `AUTH_SECRET_KEY` automáticamente. Conservarla entre
   despliegues para mantener la validez de las sesiones.
6. Crear el Blueprint y esperar el despliegue inicial. Para cambios posteriores,
   usar **Manual Deploy > Deploy latest commit** después de comprobar el CI.

El archivo configura Python 3.12, carpeta `backend`, instalación con
`pip install -r requirements.txt`, inicio con
`uvicorn app.main:app --host 0.0.0.0 --port $PORT` y health check `/health`.

Si el servicio ya existe, configurar esos valores en su panel en lugar de crear
otro servicio. Elegir `develop`, deshabilitar auto-deploy y establecer las tres
variables de conexión y sesión; generar una clave de sesión si aún no existe:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Verificar la conexión

Abrir `https://<dominio-asignado>.onrender.com/health`. Resultado esperado:

```json
{"status":"healthy","database":"connected"}
```

También comprobar `/docs`. La ruta `/` solo confirma que la API responde;
`/health` ejecuta la dependencia que consulta Supabase. Esta comprobación no
valida todas las operaciones de escritura ni sustituye las pruebas del MVP.

- **503:** revisar logs, URL y clave del mismo proyecto, esquema y migraciones.
- **Falta una tabla:** las migraciones son incrementales y necesitan el esquema
  base; no basta con crear un proyecto Supabase vacío.
- **Falta una columna de pago:** revisar la migración `001`; para asistencia,
  revisar además `005`. Aplicar las migraciones pendientes en orden sobre la
  base de prueba, después de revisar sus instrucciones.
- **Error de arranque:** comprobar carpeta `backend`, Python 3.12 y el módulo
  `app.main:app` del comando de inicio.

Preparar cuentas de prueba con contraseña para la primera comprobación de
autenticación. Google y Stripe necesitan variables adicionales si forman parte
de la demostración; no se activan solo con este Blueprint.

## Siguiente paso: Vercel

Una vez que `/health` responda correctamente, usar la URL del backend seguida
de `/api` como `VITE_AUTH_API_BASE_URL` en Vercel. Cuando se conozca el dominio
del frontend, agregar en Render:

```dotenv
CORS_ORIGINS=https://<dominio-frontend>.vercel.app
FRONTEND_PUBLIC_URL=https://<dominio-frontend>.vercel.app
```

Guardar y volver a desplegar. No configurar un dominio ficticio ni `*` como
origen. La conexión Render–Supabase puede verificarse antes de tener el frontend.

## Límites de la demo gratuita

Render Free suspende el servicio después de 15 minutos sin tráfico entrante;
la siguiente solicitud puede tardar alrededor de un minuto en reactivarlo.
Abrir `/health` antes de la review y esperar la respuesta correcta.

El código de correos usa Gmail SMTP por el puerto 465, bloqueado en Render Free.
Dejar sin configurar `GMAIL_EMAIL` y `GMAIL_APP_PASSWORD` en esta modalidad.
Las notificaciones requieren adaptar el proveedor o usar un servicio que
permita SMTP. Los archivos locales no son persistentes; los datos del MVP se
conservan en Supabase.

## Referencias

- [Blueprint de Render](https://render.com/docs/blueprint-spec)
- [Python en Render](https://render.com/docs/python-version)
- [Carpetas de servicios](https://render.com/docs/monorepo-support)
- [Limitaciones del plan Free](https://render.com/docs/free)
