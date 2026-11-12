# MOD-09 · Tienda y pedidos · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

8 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-09](../../../../base/modulos/09-tienda-pedidos.md). Actores: Cliente comprador, visitante para catálogo y admin/staff para gestión.

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M09-01** · Integración HTTP / checkout · CA-02 | Producto disponible y tarjeta elegida con Stripe simulado. | Intentar creación sin checkout; después usar el servicio de checkout; simular confirmación no pagada. | Tarjeta sin checkout se rechaza; el checkout reserva stock y no acredita pago por el retorno del navegador. Cobertura completa del endpoint pendiente si no existe prueba directa. | [store_routes.py](../../../../../backend/presentation/routes/store_routes.py) |
| **CP-M09-02** · Integración / cancelación · CA-03 | Pedido pendiente con stock reservado y checkout abierto. | Cancelar, confirmar cierre del gateway y repetir cancelación. | Se cierra checkout antes de cambiar estado; se repone stock una sola vez y el pedido queda cancelado. | [test_partial_smell_fixes.py](../../../../../backend/tests/transversales/integracion/test_partial_smell_fixes.py): `test_administrative_cancel_closes_checkout_before_changing_order` |
| **CP-M09-03** · Integración / carrera con pago · CA-04 | Pedido pendiente y gateway que falla al cerrar o recibe pago concurrente. | Intentar cancelar y después confirmar/entregar una variante todavía impaga. | No se anuncia cancelación local ante fallo/carrera; el impago no se confirma/entrega; se conservan stock y estado coherentes. La variante de entrega sin prueba directa enlazada requiere verificación pendiente. | [test_partial_smell_fixes.py](../../../../../backend/tests/transversales/integracion/test_partial_smell_fixes.py): `test_failed_close_or_a_payment_race_does_not_cancel_the_order`; [store_rules.py](../../../../../backend/domain/services/store_rules.py) |
| **CP-M09-04** · Integración / historial y privacidad · CA-05 | Pedido de C1 con líneas e importe contratados; C2 con sesión propia; variante histórica sin líneas. | Cambiar catálogo; recargar pedido y consultarlo como C1/C2. | Se preservan desglose/total original; C2 no lo obtiene. Sin líneas históricas se conserva el total conocido sin inventar detalle. | [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_order_breakdown_survives_persistence_using_its_saved_lines`; [test_priority_fixes.py](../../../../../backend/tests/transversales/integracion/test_priority_fixes.py) |
| **CP-M09-05** · Integración / imágenes · CA-06 | Admin/staff y usuario sin permiso; archivos válidos y variantes vacía, >5 MiB, MIME/extensión incompatible y SVG nuevo. | Listar imágenes públicamente; intentar subir cada variante. | Solo personal autorizado sube formatos permitidos y tamaño admitido; inválidos no llegan al almacenamiento; URLs listadas siguen utilizables. | [test_store_images.py](../../../../../backend/tests/tienda_pedidos/integracion/test_store_images.py) |
| **CP-M09-06** · Integración / papelera · CA-07 | Producto vinculado con ventas/movimientos y otro sin historial. | Archivar y restaurar; intentar borrado definitivo sin archivar; archivar y eliminar definitivamente. | Producto/ítem pasan juntos por Papelera; se exige archivado previo; el histórico comercial permanece y el catálogo oculta eliminados. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_eliminar_definitivo_con_historial_lo_oculta_y_conserva_ventas_y_movimientos` |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M09-07** · PostgreSQL / stock concurrente · CA-01 | Producto con una unidad de venta y dos instancias que compran simultáneamente. | Crear ambos pedidos y recargar stock y líneas. | Solo una compra consume esa unidad; no hay stock negativo ni pedido parcial y no se consume reserva de inventario. | [test_atomic_transactions_postgres.py](../../../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py): `test_two_instances_cannot_sell_the_same_stock` |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M09-08** · Interfaz SSR / tabla y carrito · CA-01, CA-07 | Catálogo con stock cero y productos disponibles; inventario y tienda con distintos tamaños de página. | Buscar, paginar, cambiar tamaño, agregar cantidad superior a stock y abrir Papelera. | No se ofrece compra sin stock ni se excede cantidad; cada tabla conserva su tamaño y la Papelera permite sus acciones. | [table-pagination-views.test.js](../../../../../frontend/tests/transversales/interfaz/table-pagination-views.test.js); [tienda_pedidos · formularios.test.js](../../../../../frontend/tests/tienda_pedidos/interfaz/formularios.test.js); [data-repositories.test.js](../../../../../frontend/tests/transversales/integracion/data-repositories.test.js) |
