# Plan de pruebas · MOD-09 · Tienda y pedidos

**ID:** PP-MOD-09 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
15 CT (5 backend y 10 frontend) y 8 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Catálogo/carrito, checkout, stock, cancelación, privacidad, imágenes y Papelera.

Actores: Visitante consulta catálogo, comprador consulta lo propio y admin/staff gestionan producto, imágenes y estado.

Datos de partida: Producto con una unidad para dos compradores; pedido pendiente, pagado y cancelado; checkout con cierre fallido/pago concurrente; imagen válida/vacía/excedida/MIME incompatible y SVG nuevo.

Dependencias y orden: MOD-01/02/08 y proveedor de checkout compartido con MOD-03; transversales SQL y privacidad.

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
| Compra con tarjeta y checkout obligatorio | [CP-M09-01](casos-de-uso.md) · CA-02 | P1 | Tarjeta sin checkout se rechaza; el checkout reserva stock y no acredita pago por el retorno del navegador. Cobertura completa del endpoint pendiente si no existe prueba directa. |
| Cancelación y restitución única de stock | [CP-M09-02](casos-de-uso.md) · CA-03 | P1 | Se cierra checkout antes de cambiar estado; se repone stock una sola vez y el pedido queda cancelado. |
| Cancelación concurrente con pago y entrega de impagos | [CP-M09-03](casos-de-uso.md) · CA-04 | P1 | No se anuncia cancelación local ante fallo/carrera; el impago no se confirma/entrega; se conservan stock y estado coherentes. La variante de entrega sin prueba directa enlazada requiere verificación pendiente. |
| Desglose histórico y privacidad de pedidos | [CP-M09-04](casos-de-uso.md) · CA-05 | P1 | Se preservan desglose/total original; C2 no lo obtiene. Sin líneas históricas se conserva el total conocido sin inventar detalle. |
| Subida/listado de imágenes y autorización | [CP-M09-05](casos-de-uso.md) · CA-06 | P1 | Solo personal autorizado sube formatos permitidos y tamaño admitido; inválidos no llegan al almacenamiento; URLs listadas siguen utilizables. |
| Papelera, restauración y eliminación definitiva | [CP-M09-06](casos-de-uso.md) · CA-07 | P1 | Producto/ítem pasan juntos por Papelera; se exige archivado previo; el histórico comercial permanece y el catálogo oculta eliminados. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Venta concurrente de la última unidad | [CP-M09-07](casos-de-uso.md) · CA-01 | P1 | Solo una compra consume esa unidad; no hay stock negativo ni pedido parcial y no se consume reserva de inventario. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Tabla, paginación, carrito y acciones de Papelera | [CP-M09-08](casos-de-uso.md) · CA-01, CA-07 | P1 | No se ofrece compra sin stock ni se excede cantidad; cada tabla conserva su tamaño y la Papelera permite sus acciones. |

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
  tests/tienda_pedidos/integracion/test_store_images.py \
  tests/transversales/integracion/test_partial_smell_fixes.py \
  tests/transversales/integracion/test_priority_fixes.py \
  tests/transversales/integracion/test_review_regressions.py \
  tests/transversales/postgres/test_atomic_transactions_postgres.py -q)
(cd frontend && node --test \
  tests/tienda_pedidos/interfaz/formularios.test.js \
  tests/transversales/integracion/data-repositories.test.js \
  tests/transversales/interfaz/table-pagination-views.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

CP-M09-01 y la variante de entrega impaga de CP-M09-03 enlazan también código y requieren verificación funcional directa donde falta prueba automatizada. No se darán por aprobadas solo por compilar o por probar el gateway compartido.

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
