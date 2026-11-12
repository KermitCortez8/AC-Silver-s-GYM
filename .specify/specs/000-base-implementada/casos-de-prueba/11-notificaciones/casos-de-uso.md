# MOD-11 · Notificaciones · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

6 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-11](../../../../base/modulos/11-notificaciones.md). Actores: Procesador de cola/Sistema y destinatario de prueba.

## Pruebas unitarias

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M11-01** · Unitaria e integración Deno / fecha · CA-04 | Matrícula de una sola fecha cerca de cambio de mes UTC/Lima. | Construir correo y recordatorios; intentar generar aviso para otra semana. | Enlace y texto usan la fecha reservada en Lima, no anuncian recurrencia y no se crea recordatorio de otra semana. | [test_schedule_calendar.py](../../../../../backend/tests/notificaciones/integracion/test_schedule_calendar.py) |

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M11-02** · Integración / confirmación de envío · CA-01 | Evento de membresía en cola y Resend simulado que responde con ID. | Procesar evento; reintentar el mismo evento y consultar cola. | Solo se marca enviado con ID del proveedor y se conserva la clave estable por membresía/evento. | [test_resend_email.py](../../../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_success_records_provider_id_for_membership` |
| **CP-M11-03** · Integración / timeout · CA-02 | Pago/activación guardados y evento listo; proveedor simula timeout. | Procesar cola y consultar negocio y aviso. | Pago/activación permanecen; aviso sigue pendiente con error seguro, sin declarar entrega. | [test_resend_email.py](../../../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_timeout_keeps_membership_pending` |
| **CP-M11-04** · Integración / aviso obsoleto · CA-03 | Notificación de matrícula en cola y matrícula cancelada/cambiada antes de enviar. | Resolver contexto y procesar el evento. | Se cancela el aviso que dejó de aplicar y no se contacta al destinatario con información obsoleta. | [test_resend_email.py](../../../../../backend/tests/notificaciones/integracion/test_resend_email.py): `test_schedule_cancelled_before_sending_when_enrollment_changes` |

## Pruebas de la Edge Function

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M11-05** · Integración Deno / privacidad · CA-05 | Resend simulado con errores 401/403/409/422/429/500 y respuesta sin ID. | Procesar cada respuesta e inspeccionar resultado/log seguro. | No aparecen cuerpo sensible ni credenciales; sin ID no hay entrega exitosa y el fallo recuperable conserva aviso pendiente. | [resend_email_test.ts](../../../../../supabase/tests/resend_email_test.ts) |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M11-06** · PostgreSQL / avisos de renovación · CA-01, CA-04 | Período activado y comenzado en últimos tres días o vencido, con datos sintéticos. | Preparar aviso y reclamarlo desde dos procesadores; repetir preparación. | Solo un reclamo y una clave por evento; se respetan permisos privados y no se generan avisos de compra inicial sin activar o período futuro. | [test_membership_renewal_postgres.py](../../../../../backend/tests/notificaciones/postgres/test_membership_renewal_postgres.py); [test_membership_renewal.py](../../../../../backend/tests/membresias_pagos/integracion/test_membership_renewal.py) |
