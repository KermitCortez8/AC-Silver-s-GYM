# Plan de pruebas · MOD-11 · Notificaciones

**ID:** PP-MOD-11 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
21 CT (21 backend y 0 frontend) y 6 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Confirmación, recordatorio por fecha, reintento, privacidad y deduplicación.

Actores: Procesador/Sistema y destinatario ficticio; roles públicos sin acceso a RPC privadas.

Datos de partida: Evento estable con ID de proveedor, timeout, 429/500 y respuesta sin ID; matrícula cancelada, fecha cerca de cambio de mes y dos trabajadores reclamando el mismo evento.

Dependencias y orden: MOD-03 para pago/renovación y MOD-05 para matrícula por fecha; Edge Function y pg_cron según variante.

Aplicar los [datos y entornos comunes](../plan-de-pruebas.md#entorno-y-datos-de-prueba)
y los criterios de entrada antes de ejecutar. Usar estado limpio para cada
variante y conservar las mismas identidades dentro de un recorrido compuesto.

## Funcionalidades y casos programados por tipo

P1 cubre identidad/permisos, dinero, consistencia y reglas indispensables;
P2 cubre presentación, navegación y ergonomía. Ambos forman parte del alcance.
Las precondiciones y pasos completos están en [casos-de-uso.md](casos-de-uso.md).

### Pruebas unitarias y de reglas

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Correo y recordatorio de la fecha reservada | [CP-M11-01](casos-de-uso.md) · CA-04 | P1 | Enlace y texto usan la fecha reservada en Lima, no anuncian recurrencia y no se crea recordatorio de otra semana. |

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Confirmación de envío e idempotencia del evento | [CP-M11-02](casos-de-uso.md) · CA-01 | P1 | Solo se marca enviado con ID del proveedor y se conserva la clave estable por membresía/evento. |
| Timeout y conservación de negocio/aviso pendiente | [CP-M11-03](casos-de-uso.md) · CA-02 | P1 | Pago/activación permanecen; aviso sigue pendiente con error seguro, sin declarar entrega. |
| Cancelación de notificación con contexto obsoleto | [CP-M11-04](casos-de-uso.md) · CA-03 | P1 | Se cancela el aviso que dejó de aplicar y no se contacta al destinatario con información obsoleta. |
| Errores privados y respuesta sin ID de entrega | [CP-M11-05](casos-de-uso.md) · CA-05 | P1 | No aparecen cuerpo sensible ni credenciales; sin ID no hay entrega exitosa y el fallo recuperable conserva aviso pendiente. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Avisos de renovación y reclamo exclusivo en SQL | [CP-M11-06](casos-de-uso.md) · CA-01, CA-04 | P1 | Solo un reclamo y una clave por evento; se respetan permisos privados y no se generan avisos de compra inicial sin activar o período futuro. |

## Selección y orden de ejecución

1. Revisar los CP anteriores y los [casos individuales](casos-de-prueba.md);
   clasificar las variantes por sus precondiciones y el entorno requerido.
2. Ejecutar reglas y contratos locales, después servicios/HTTP y los controles
   compartidos indicados por las fuentes de los CP. Separar resultados SQL.
3. Preparar y ejecutar cada variante PostgreSQL en su contenedor desechable;
   comprobar locks, rollback y recarga cuando el caso lo exige. Sin ese entorno,
   registrar omisión o bloqueo y continuar con las pruebas independientes.
4. Realizar los recorridos de interfaz que correspondan: estados correcto/error,
   teclado, móvil/escritorio, claro/oscuro y conservación de borradores.
   Un resultado Node/SSR no aprueba por sí solo el recorrido de navegador.
5. Repetir el caso fallido tras la corrección y su regresión relacionada; cerrar
   con la regresión completa del plan general en la versión que se informa.

La selección reproducible se obtiene de [catalogo-pruebas.json](catalogo-pruebas.json).
Estos comandos cubren suites propias y fuentes compartidas citadas por sus CP;
los totales reales se registran desde el runner y se deduplican por selector.

```bash
(cd backend && python -m pytest \
  tests/membresias_pagos/integracion/test_membership_renewal.py \
  tests/notificaciones/integracion/test_resend_email.py \
  tests/notificaciones/integracion/test_schedule_calendar.py \
  tests/notificaciones/postgres/test_membership_renewal_postgres.py -q)
deno check supabase/functions/schedule-emails/index.ts
deno test supabase/tests/
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Los siete casos Deno se programan como evidencia complementaria, fuera de los 1.177. Un doble o dry run no acredita entrega real ni despliegue externo.

Por cada CP registrar variante, CT/selector o recorrido manual que lo comprueba,
versión, datos, resultado observado y evidencia. Para navegador adjuntar captura
propia y pasos; para API/SQL registrar respuesta/consulta y estado antes/después.
Si la referencia solo aporta código, completar una verificación directa en el
entorno de pruebas o registrar la cobertura pendiente; no inferir una aprobación.

El módulo se declara aprobado cuando todos sus casos programados y regresiones
aplicables cumplen el resultado esperado, sin defectos S1/S2 abiertos ni bloqueos
P1. Cada omisión/bloqueo mantiene pendiente la funcionalidad que depende de ella.
El [plan general](../plan-de-pruebas.md#criterios-de-salida-y-entregables) define
el cierre completo y el tratamiento de un informe parcial.
