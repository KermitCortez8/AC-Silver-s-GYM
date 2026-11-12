# Plan de pruebas · MOD-03 · Membresías y pagos

**ID:** PP-MOD-03 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
108 CT (91 backend y 17 frontend) y 9 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Estados, pago verificado, primera activación, vigencia, historial y renovación.

Actores: Cliente habilitado y personal autorizado para caja, historial y primera activación.

Datos de partida: Primera compra impaga/pagada sin activar; período activado con fin F; fechas F−8, F−7, F y F+1; importe guardado cero y precio con descuento; checkout repetido.

Dependencias y orden: MOD-01/02/04 y cola de MOD-11; la recarga SQL de campos vive también en transversales.

Aplicar los [datos y entornos comunes](../plan-de-pruebas.md#entorno-y-datos-de-prueba)
y los criterios de entrada antes de ejecutar. Usar estado limpio para cada
variante y conservar las mismas identidades dentro de un recorrido compuesto.

## Funcionalidades y casos programados por tipo

P1 cubre identidad/permisos, dinero, consistencia y reglas indispensables;
P2 cubre presentación, navegación y ergonomía. Ambos forman parte del alcance.
Las precondiciones y pasos completos están en [casos-de-uso.md](casos-de-uso.md).

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Ciclo de estados de la membresía | [CP-M03-01](casos-de-uso.md) · CA-01 | P1 | Las escrituras solo usan EN_TRAMITE, ACTIVO y VENCIDA; un estado adicional es rechazado sin mutación. |
| Verificación de pago Stripe | [CP-M03-02](casos-de-uso.md) · CA-02 | P1 | Solo el caso válido guarda pago; las variantes rechazadas conservan estado previo sin acreditar importes del navegador. |
| Activación inicial e idempotencia | [CP-M03-03](casos-de-uso.md) · CA-03 | P1 | La impaga se rechaza; la pagada se activa con su duración; repetir no extiende el período. |
| Confirmación de efectivo y preservación de Stripe | [CP-M03-04](casos-de-uso.md) · CA-04 | P1 | La primera queda pagada sin activación automática; un pago Stripe existente conserva su método/referencia. |
| Vigencia inclusiva y vencimiento en Lima | [CP-M03-05](casos-de-uso.md) · CA-05 | P1 | D es inclusivo; luego vence sin borrar historial; una renovación vigente conserva/restaura el acceso. |
| Historial de cobros y acceso del personal | [CP-M03-06](casos-de-uso.md) · CA-06 | P1 | Cada pago aparece una vez con su importe original, incluso cero; el historial administrativo no se entrega al rol no autorizado. |
| Renovación automática tras pago y conservación de vigencia | [CP-M03-07](casos-de-uso.md) · CA-04, CA-05 | P1 | La renovación se activa sin otra aprobación; anticipada comienza tras el último día inclusivo anterior; reintentar no amplía fechas; la compra inicial no elude su aprobación. |
| Ventana de recompra y confirmación de recibo | [CP-M03-08](casos-de-uso.md) · CA-04, CA-05 | P1 | F−8 se rechaza; F−7 y vencida son elegibles; ninguna ruta elude la ventana ni guarda cobro de caja sin confirmación requerida. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Diálogo de renovación, errores y doble clic | [CP-M03-09](casos-de-uso.md) · CA-04 | P1 | No se duplican envíos; se reutiliza la compra pendiente y no se ofrece caja; una respuesta obsoleta se descarta y el error permite revisar otra vez. |

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
  tests/clientes/integracion/test_admin_client_payment.py \
  tests/membresias_pagos/integracion/test_admin_membership_renewal.py \
  tests/membresias_pagos/integracion/test_membership_expiration.py \
  tests/membresias_pagos/integracion/test_membership_payments.py \
  tests/membresias_pagos/integracion/test_membership_renewal.py \
  tests/membresias_pagos/integracion/test_membership_states.py \
  tests/membresias_pagos/integracion/test_stripe_checkout.py \
  tests/membresias_pagos/integracion/test_stripe_confirmation.py \
  tests/membresias_pagos/integracion/test_supabase_payment_safety.py -q)
(cd frontend && node --test \
  tests/membresias_pagos/interfaz/admin-membership-renewal.test.js \
  tests/membresias_pagos/interfaz/membership-renewal.test.js \
  tests/membresias_pagos/unitarias/admin-client-payment.test.js \
  tests/membresias_pagos/unitarias/membership-payments.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Solo la primera compra requiere activación administrativa. Los pagos se verifican con gateway simulado; el retorno del navegador no acredita pago. No recargar el precio histórico desde catálogo.

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
