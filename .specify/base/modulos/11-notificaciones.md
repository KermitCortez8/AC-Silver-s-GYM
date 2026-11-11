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
| CA-01 | [membership_notifications.py](../../../backend/application/services/membership_notifications.py); [test_resend_email.py](../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_success_records_provider_id_for_membership`, `test_no_delivery_id_is_not_reported_as_sent`. |
| CA-02 | [test_resend_email.py](../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_timeout_keeps_membership_pending`; [membership_notifications.py](../../../backend/application/services/membership_notifications.py). |
| CA-03 | [test_resend_email.py](../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_schedule_cancelled_before_sending_when_enrollment_changes`. |
| CA-04 | [test_schedule_calendar.py](../../../backend/tests/notificaciones/integracion/test_schedule_calendar.py). |
| CA-05 | [test_resend_email.py](../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_provider_errors_are_safe_for_queue_and_logs`; [resend_email_test.ts](../../../supabase/tests/resend_email_test.ts). |

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

### Avisos de próximo vencimiento y membresía vencida

El backend revisa cada minuto las membresías pagadas. Prepara un aviso `expiring`
al entrar en los últimos tres días (incluye el día final) y otro `expired` después
del último día, con fecha `America/Lima`. Si el proceso estuvo detenido, recupera
el aviso que corresponde al volver, hasta treinta días después del vencimiento.
No prepara avisos de una membresía anterior si existe otra posterior pagada.
Cada evento se deduplica por membresía en la cola existente y conserva sus
reintentos/confirmación de entrega con Resend.

Los mensajes enlazan a `/renovar-membresia#token=…` para revisar la compra antes
de pagar. El enlace está firmado con `AUTH_SECRET_KEY`, requiere la fecha de fin
original y caduca treinta días después del vencimiento. No usa la sesión del
cliente, que puede haber perdido acceso por vencimiento. También necesita
`FRONTEND_PUBLIC_URL` y las credenciales de Resend/Supabase ya utilizadas.

Aplicar [024_membership_renewal_notifications.sql](../../../backend/migrations/024_membership_renewal_notifications.sql)
sobre la cola creada por 004 antes de iniciar la nueva versión del backend.
La migración amplía el CHECK de tipos de evento y mantiene RLS y RPC privadas.
La recuperación está descrita en el propio SQL. No requiere modificar ni desplegar
la Edge Function de recordatorios de clases.

Evidencia: [regresiones](../../../backend/tests/membresias_pagos/integracion/test_membership_renewal.py),
[pruebas PostgreSQL](../../../backend/tests/notificaciones/postgres/test_membership_renewal_postgres.py) y
[validación](../validaciones/renovacion-membresia/validation.md).


El correo de pago de una renovación activada automáticamente confirma la
renovación y presenta sus fechas y enlace de acceso. Solo el correo del primer
registro solicita activación administrativa. El evento sigue siendo `payment`
para conservar la deduplicación por membresía y la cola existente.


La ventana de recompra empieza siete días antes del vencimiento; los avisos
continúan enviándose desde los últimos tres días y después del vencimiento.
Solo se preparan para períodos pagados y activados que ya comenzaron: un pago
inicial pendiente de activación o una renovación futura no origina estos avisos.
