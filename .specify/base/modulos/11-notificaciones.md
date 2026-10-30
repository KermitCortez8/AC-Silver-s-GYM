# MOD-11 · Notificaciones y recordatorios

Estado: implementado según código y pruebas de referencia. Su operación real
depende de configuración privada, colas, Cron y despliegue externo no certificados aquí.

## 1. Sprint Goal

Informar pagos/activaciones y matrículas/clases mediante avisos persistentes,
sin revertir una operación de negocio correcta por un fallo de correo.

## 2. User Story

**P1.** Como cliente, quiero recibir confirmaciones y recordatorios de mi
membresía y clases. Como operador, quiero que los fallos de envío queden
pendientes y que los reintentos no se anuncien falsamente como entregados.

Prueba independiente: procesar una cola sintética con remitente inyectado,
simular timeout y luego respuesta con ID; comprobar el estado persistido.

## 3. Acceptance Criteria

1. **CA-01.** Dado un evento de membresía, el aviso usa clave por membresía/evento
   y se marca enviado solo después de obtener ID del proveedor.
2. **CA-02.** Dado un timeout o error del proveedor, el aviso queda pendiente
   y el pago/activación ya guardados no se revierten.
3. **CA-03.** Dada una matrícula/horario que cambia antes del envío, al resolver
   su contexto se cancela el aviso obsoleto.
4. **CA-04.** Dado un recordatorio de clase, el enlace apunta a la fecha de Perú
   y la confirmación de matrícula identifica una sola sesión con su fecha.
   Los recordatorios no se vuelven a generar para otra semana de esa matrícula.
5. **CA-05.** Dado un error HTTP de Resend, la respuesta/log seguro no expone
   el cuerpo sensible ni las credenciales; una respuesta sin ID no es entrega exitosa.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [membership_notifications.py](../../../backend/application/services/membership_notifications.py); [test_resend_email.py](../../../backend/tests/test_resend_email.py): `test_success_records_provider_id_for_membership`, `test_no_delivery_id_is_not_reported_as_sent`. |
| CA-02 | [test_resend_email.py](../../../backend/tests/test_resend_email.py): `test_timeout_keeps_membership_pending`; [membership_notifications.py](../../../backend/application/services/membership_notifications.py). |
| CA-03 | [test_resend_email.py](../../../backend/tests/test_resend_email.py): `test_schedule_cancelled_before_sending_when_enrollment_changes`. |
| CA-04 | [test_schedule_calendar.py](../../../backend/tests/test_schedule_calendar.py). |
| CA-05 | [test_resend_email.py](../../../backend/tests/test_resend_email.py): `test_provider_errors_are_safe_for_queue_and_logs`; [resend_email_test.ts](../../../supabase/tests/resend_email_test.ts). |

## 4. Technical Constraints

- Servicios: [membership_notifications.py](../../../backend/application/services/membership_notifications.py),
  [schedule_notifications.py](../../../backend/application/services/schedule_notifications.py),
  [email_templates.py](../../../backend/application/services/email_templates.py) y
  [email_service.py](../../../backend/infrastructure/services/email_service.py).
- Colas de membresía y horarios, puertos inyectados y envío HTTPS con Resend;
  no se necesita Gmail para las plantillas.
- [app/main.py](../../../backend/app/main.py) inicia el procesamiento de membresía
  en segundo plano. Recordatorios de horarios usan Supabase Cron + Edge Function
  [schedule-emails](../../../supabase/functions/schedule-emails/index.ts), con
  [worker.ts](../../../supabase/functions/schedule-emails/worker.ts).
- Migraciones `004_membership_email_notifications.sql`,
  `006_schedule_email_notifications.sql`, `007_schedule_emails_cron.sql` y
  [019_schedule_sessions.sql](../../../backend/migrations/019_schedule_sessions.sql).
- Configuración de servidor: `RESEND_API_KEY`, `EMAIL_FROM`, nombre de remitente,
  URL pública frontend y Supabase; la función usa además su secreto de Cron.
  No copiar valores reales a documentación o al frontend.

## 5. Guardrails

No marcar enviado sin ID ni asumir que el destinatario abrió el correo. No
revertir una matrícula confirmada por fallo posterior de envío. No exponer
respuestas crudas de proveedores. No afirmar que los recordatorios funcionan
en producción solo porque las pruebas con dobles pasan.

## 6. Edge Cases

- Configuración ausente: informar `not_configured`/pendiente según el servicio;
  no anunciar entrega ni iniciar un bucle de envíos sin credenciales.
- Matrícula cancelada o cambiada: cancelar el aviso cuyo contexto ya no aplica.
- Mismo evento reenviado: reutilizar clave de idempotencia estable.
- Proveedor rechaza, limita o no responde: conservar error seguro para reintento.
- Simulación de la función: no enviar ni afirmar una entrega remota comprobada.

## 7. Definition of Done

Verificar colas, contexto, claves e interpretación de errores afectados con
pytest y Deno según el componente. Registrar por separado cualquier prueba de
entrega real y la configuración externa comprobada. Cumplir el [DoD](../../docs/DoD.md).
