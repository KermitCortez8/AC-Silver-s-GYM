# Correos del MVP con Resend

El backend y la función `schedule-emails` envían por HTTPS a Resend. Ya no
utilizan `GMAIL_EMAIL` ni `GMAIL_APP_PASSWORD`. Las plantillas, las colas y sus
migraciones se conservan. No se requieren cambios de esquema para este cambio.

## Dominio y demostración

`ac-silvers-gym-api-review.onrender.com` es la dirección web de la API. Render
controla el DNS de `onrender.com`; esa dirección no permite configurar los
registros DNS que Resend exige para verificar un remitente.

Para la demo, usar `onboarding@resend.dev`. Con ese remitente Resend solo permite
enviar al correo de la cuenta de Resend. Registrar al cliente de demostración
con esa dirección. El programa no sustituye ni redirige destinatarios.

Para enviar a otros clientes, verificar en Resend un dominio propio y poner una
dirección de ese dominio en `EMAIL_FROM` (solo la dirección, sin nombre ni `<>`).

## Configurar Render

1. Crear una API key de Resend con permiso de envío.
2. En el servicio existente, abrir **Environment** y agregar manualmente:

   ```dotenv
   RESEND_API_KEY=re_TU_CLAVE_PRIVADA
   EMAIL_FROM=onboarding@resend.dev
   EMAIL_FROM_NAME=Silver Gym Surco
   FRONTEND_PUBLIC_URL=https://TU-FRONTEND.vercel.app
   ```

   Usar la URL real del frontend para los botones del correo. Conservar las
   variables existentes de Supabase, autenticación, Google y Stripe.
3. Guardar las variables y desplegar el último commit de `develop` con
   **Manual Deploy > Deploy latest commit**. El Blueprint tiene auto-deploy
   desactivado. `sync: false` solo solicita secretos al crear un Blueprint;
   actualizar Git no agrega la clave al servicio que ya existe.
4. Las variables antiguas de Gmail pueden eliminarse del panel; el código ya no
   las lee. La clave de Resend nunca debe ir en Vercel ni tener prefijo `VITE_`.

Para ejecutar localmente, agregar las mismas variables de correo a
`backend/.env`. No versionar ese archivo.

## Recordatorios y reintentos de matrícula en Supabase

Actualizar también el proveedor de la función; desplegar Render no actualiza
las Edge Functions. Antes de migrar, pausar temporalmente el Cron de la demo si
está activo para evitar que siga enviando con el proveedor anterior.

1. En **Edge Functions > Secrets**, configurar `RESEND_API_KEY`, `EMAIL_FROM`,
   `EMAIL_FROM_NAME` y `FRONTEND_PUBLIC_URL` con los mismos valores que en Render.
2. Conservar `SCHEDULE_CRON_SECRET` y el mismo valor en Vault. La función alojada
   ya dispone de `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`.
3. Con Supabase CLI autenticado, desplegar desde la raíz del repositorio:

   ```bash
   supabase functions deploy schedule-emails --project-ref TU_PROJECT_REF
   ```

4. Con las migraciones y el Cron existentes, comprobar desde SQL Editor:

   ```sql
   select public.invoke_schedule_emails(true);
   ```

   La consulta devuelve el identificador de la solicitud asíncrona. Revisar la
   respuesta en `net._http_response` o los logs de la función. El `dry_run`
   comprueba base y configuración, no envía correos ni verifica remotamente la
   API key. Su resultado incluye `resend: "configured_not_sent"`.
5. Verificar un envío con datos de demo antes de reactivar el Cron. Si no estaba
   configurado, seguir las instrucciones de `006` y `007`: la migración `007`
   necesita secretos en Vault y crea el trabajo pausado.

## Prueba de la review

- Registrar un cliente con el correo permitido por Resend.
- Completar un pago de prueba: comprobar el correo de pago confirmado.
- Activar la membresía: comprobar el correo con enlace al login.
- Matricular como administrador: comprobar la confirmación de clase.
- Para recordatorios, comprobar además que la función y el Cron estén activos
  y que exista una clase dentro de la ventana de recordatorio configurada.
- Revisar los eventos de Resend y la bandeja, incluida la carpeta de spam.

La aceptación de la API devuelve un identificador y marca el trabajo como
`sent`; no garantiza que el proveedor final lo coloque en la bandeja principal.
Los mensajes pendientes anteriores pueden volver a procesarse al configurar la
API key. Los marcados como enviados no se reenvían automáticamente.

## Reintentos y diagnósticos

La clave de idempotencia se deriva del proyecto Supabase y del evento. Python y
la función usan el mismo formato. Resend conserva estas claves durante 24 horas;
la cola local registra los envíos confirmados. No cambiar el contenido ni el
remitente de un evento pendiente después de que Resend lo haya aceptado.
Al migrar desde Gmail no puede garantizarse deduplicación entre proveedores de
un mensaje que Gmail aceptó pero cuya confirmación no llegó a guardarse.

- **401:** revisar la API key.
- **403:** revisar el dominio del remitente y la restricción de destinatario de demo.
- **409:** revisar cambios de contenido/remitente al reintentar el mismo evento.
- **422:** revisar remitente y datos del cliente.
- **429, caída de red o error del proveedor:** permanece pendiente con reintento.

Los errores guardados no incluyen cuerpos de respuesta, claves ni direcciones
devueltas por Resend. Sin `RESEND_API_KEY`, los correos de membresía quedan
deshabilitados y los de matrícula permanecen en la cola de horarios.

## Validación y Git Flow

Implementación en `feature/resend-email`, integración con merge `--no-ff` en
`develop`. No se modifica el tag publicado `v1.1.0` ni se cierra otra release
antes de probar la demo desplegada.

```bash
cd backend
python -m pytest -q
cd ..
deno check supabase/functions/schedule-emails/index.ts
deno test supabase/tests/
```

Las pruebas simulan el proveedor y no envían mensajes reales. La entrega real
se valida después de configurar las credenciales y desplegar ambos servicios.

Fuentes: [dominios](https://resend.com/docs/dashboard/domains/introduction),
[restricciones de demo](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain),
[idempotencia](https://resend.com/docs/dashboard/emails/idempotency-keys).
