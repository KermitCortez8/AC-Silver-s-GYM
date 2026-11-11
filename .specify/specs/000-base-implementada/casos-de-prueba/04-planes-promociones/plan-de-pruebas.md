# Plan de pruebas · MOD-04 · Planes y promociones

**ID:** PP-MOD-04 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
13 CT (3 backend y 10 frontend) y 6 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Planes/duración, descuentos, vigencia, cupos y precio contratado.

Actores: Visitante consulta, admin/staff gestionan planes y solo admin muta promociones.

Datos de partida: Plan de precio 100 y otro de precio cero, duración histórica y predefinida; promoción del 10 %, futura, vencida, agotada, ajena e incompatible por fechas.

Dependencias y orden: MOD-02/03 consumen la oferta; transversales SQL comprueban recarga de asociaciones.

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
| Consulta y aplicación de promociones vigentes | [CP-M04-01](casos-de-uso.md) · CA-01 | P1 | Se publican/aplican únicamente las promociones elegibles por plan y fecha. |
| Límite de cupos promocionales | [CP-M04-02](casos-de-uso.md) · CA-02 | P1 | No se concede un cupo adicional ni se deja un descuento no autorizado. |
| Conflicto por solapamiento de promociones | [CP-M04-03](casos-de-uso.md) · CA-03 | P1 | Se rechaza el conflicto y se conserva la promoción inicial sin cambios parciales. |
| Formulario de duración, precio cero y validación | [CP-M04-04](casos-de-uso.md) · CA-01, CA-05 | P1 | Se aceptan duraciones válidas y precio cero explícito, se conserva la duración histórica y se rechaza una inválida con mensaje de campo. |

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Promoción seleccionada en el alta administrativa | [CP-M04-05](casos-de-uso.md) · CA-04 | P1 | La primera cobra precio sin descuento automático; la inválida impide crear cliente/membresía. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Persistencia de promoción y precio contratado | [CP-M04-06](casos-de-uso.md) · CA-05 | P1 | Se preservan campos y asociación de promoción; el importe contratado no se recalcula. |

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
  tests/planes_promociones/unitarias/test_promocion_cupos.py \
  tests/planes_promociones/unitarias/test_promocion_navidad.py \
  tests/transversales/postgres/test_atomic_transactions_postgres.py -q)
(cd frontend && node --test \
  tests/planes_promociones/integracion/plan-directory.test.js \
  tests/planes_promociones/interfaz/formularios.test.js \
  tests/planes_promociones/unitarias/membership-plan-form.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

El cupo promocional y el cupo de una clase son recursos diferentes. Un alta administrativa no aplica una promoción que el operador no seleccionó.

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
