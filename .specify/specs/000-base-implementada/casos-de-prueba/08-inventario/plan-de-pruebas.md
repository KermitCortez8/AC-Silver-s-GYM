# Plan de pruebas · MOD-08 · Inventario y movimientos

**ID:** PP-MOD-08 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
90 CT (63 backend y 27 frontend) y 7 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Reserva/reposición, movimientos, estados, archivo y validación de cantidades.

Actores: Admin/staff con actor de movimiento resuelto por la sesión.

Datos de partida: Reserva 10, venta 2, reposición 3; solicitud insuficiente 11; mínimo cero; ítem con/sin historial, equipo y Descontinuado manual; borrador inválido.

Dependencias y orden: MOD-09 para producto vinculado y movimientos de pedido; transversales para errores/atomicidad.

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
| Alta de artículo y separación de reserva/venta | [CP-M08-01](casos-de-uso.md) · CA-01 | P1 | Inventario reserva 10, un movimiento de entrada y producto vinculado con stock de venta cero. |
| Reposición atómica hacia tienda | [CP-M08-02](casos-de-uso.md) · CA-02 | P1 | Éxito deja reserva 7 y tienda 5 con movimiento; insuficiencia/fallo conserva ambos stocks y el historial previo. |
| Edición de datos sin modificar stock | [CP-M08-03](casos-de-uso.md) · CA-03 | P1 | El stock no se modifica directamente; cero sigue siendo cero y no se reemplaza por un valor predeterminado. |
| Corrección de movimientos y saldo no negativo | [CP-M08-04](casos-de-uso.md) · CA-04 | P1 | Se recalcula la diferencia en recursos afectados; se rechaza saldo negativo y en pedidos solo se permiten fecha/descripción. |
| Borrado/archivo conservando historial | [CP-M08-05](casos-de-uso.md) · CA-05 | P1 | El primero queda descontinuado/archivado según vínculo; el segundo puede eliminarse; no se pierden movimientos históricos. |
| Estado calculado por stock y mínimo | [CP-M08-06](casos-de-uso.md) · CA-06 | P1 | La reserva calcula su estado por stock/mínimo; Descontinuado y equipos conservan su tratamiento manual. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Teclado, longitudes y cantidades de formularios | [CP-M08-07](casos-de-uso.md) · CA-03, CA-04 | P1 | Se respetan límites sin perder borrador ni interceptar controles nativos; cantidades inválidas no se envían; navegación por teclado sigue la regla vigente. |

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
  tests/inventario/integracion/test_inventario_tienda_stock.py \
  tests/inventario/unitarias/test_inventory_quantities.py -q)
(cd frontend && node --test \
  tests/inventario/interfaz/formularios.test.js \
  tests/inventario/unitarias/inventario-teclado-limites.test.js \
  tests/inventario/unitarias/quantities.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Validar ambos stocks y el movimiento tras fallo/rollback. Los campos descriptivos no son mecanismos para ajustar existencias.

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
