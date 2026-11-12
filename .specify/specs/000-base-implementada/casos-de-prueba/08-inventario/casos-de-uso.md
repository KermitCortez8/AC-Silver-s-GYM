# MOD-08 · Inventario y movimientos · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

7 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-08](../../../../base/modulos/08-inventario.md). Actores: Admin/staff; autor del movimiento derivado de la sesión.

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M08-01** · Integración / alta de reserva · CA-01 | Admin/staff, artículo tipo Tienda y stock inicial 10. | Guardar artículo y consultar movimientos/producto asociado. | Inventario reserva 10, un movimiento de entrada y producto vinculado con stock de venta cero. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_alta_de_item_tienda_registra_entrada_y_crea_producto_vacio` |
| **CP-M08-02** · Integración / reposición atómica · CA-02 | Reserva 10 y producto vinculado con stock 2. | Reponer 3; en variantes separadas solicitar 11 y simular fallo remoto al persistir. | Éxito deja reserva 7 y tienda 5 con movimiento; insuficiencia/fallo conserva ambos stocks y el historial previo. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_fallo_de_supabase_revierte_la_reposicion` |
| **CP-M08-03** · Integración e interfaz / edición · CA-03 | Artículo/producto con stock y mínimo cero guardados. | Editar nombre/descripción sin movimiento; guardar y recargar. | El stock no se modifica directamente; cero sigue siendo cero y no se reemplaza por un valor predeterminado. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_editar_item_no_modifica_el_stock` |
| **CP-M08-04** · Integración / corrección de movimiento · CA-04 | Entrada o reposición previa y movimiento de pedido existente. | Corregir cantidad/ítem; probar diferencia que daría stock negativo; intentar alterar cantidad de movimiento de pedido. | Se recalcula la diferencia en recursos afectados; se rechaza saldo negativo y en pedidos solo se permiten fecha/descripción. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_editar_reposicion_corrige_ambos_stocks` |
| **CP-M08-05** · Integración / borrado · CA-05 | Un artículo con historial y otro sin historial. | Borrar ambos y consultar existencias/histórico. | El primero queda descontinuado/archivado según vínculo; el segundo puede eliminarse; no se pierden movimientos históricos. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_borrar_item_con_historial_lo_descontinua` |
| **CP-M08-06** · Integración / estado calculado · CA-06 | Reserva tipo Tienda con stock 2/mínimo 3; variantes Descontinuado manual y equipo. | Modificar stock por movimiento y luego mínimo; recargar estado. | La reserva calcula su estado por stock/mínimo; Descontinuado y equipos conservan su tratamiento manual. | [test_inventario_tienda_stock.py](../../../../../backend/tests/inventario/integracion/test_inventario_tienda_stock.py): `test_estado_automatico_sigue_la_reserva_del_inventario` |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M08-07** · Interfaz / teclado y límites · CA-03, CA-04 | Formulario de artículo y movimiento con borrador. | Pegar nombre >40 y observaciones >100; usar Enter, Shift+Enter, flechas, textarea e IME; enviar cantidad inválida. | Se respetan límites sin perder borrador ni interceptar controles nativos; cantidades inválidas no se envían; navegación por teclado sigue la regla vigente. | [inventario-teclado-limites.test.js](../../../../../frontend/tests/inventario/unitarias/inventario-teclado-limites.test.js); [inventario · formularios.test.js](../../../../../frontend/tests/inventario/interfaz/formularios.test.js) |
