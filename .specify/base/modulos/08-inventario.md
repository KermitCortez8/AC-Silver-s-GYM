# MOD-08 · Inventario y movimientos

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Mantener existencias de almacén, equipos y reposiciones hacia tienda mediante
movimientos que preservan la consistencia de ambos stocks.

## 2. User Story

**P1.** Como administrador o staff, quiero registrar entradas, salidas, ajustes
y reposiciones para conocer la reserva disponible y abastecer la tienda.

Prueba independiente: dar de alta un ítem tipo Tienda, reponer desde su reserva
al producto y comprobar ambos stocks y el movimiento generado.

## 3. Acceptance Criteria

1. **CA-01.** Dado un nuevo ítem tipo Tienda con existencias, al guardarlo se
   registra la entrada y se crea su producto con stock de venta vacío.
2. **CA-02.** Dada reserva suficiente y producto vinculado, al reponer se resta
   reserva y se suma stock de tienda en una operación; sin reserva se conserva todo.
3. **CA-03.** Dado un ítem o producto existente, editar sus datos no modifica
   directamente el stock.
4. **CA-04.** Dada una corrección de movimiento, se recalcula la diferencia sin
   admitir stock negativo; un movimiento de pedido solo permite sus campos admitidos.
5. **CA-05.** Dado un ítem con historial, al borrarlo se descontinúa; un ítem
   sin historial puede eliminarse.
6. **CA-06.** Dada una reserva tipo Tienda, su estado se calcula desde stock y
   mínimo; el estado Descontinuado manual y los equipos mantienen su tratamiento propio.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_alta_de_item_tienda_registra_entrada_y_crea_producto_vacio`. |
| CA-02 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_reponer_tienda_pasa_unidades_de_la_reserva_al_producto`, `test_reponer_sin_reserva_suficiente_no_cambia_nada`, `test_fallo_de_supabase_revierte_la_reposicion`. |
| CA-03 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_editar_item_no_modifica_el_stock`, `test_editar_producto_no_cambia_su_stock`. |
| CA-04 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_editar_movimiento_no_deja_stock_negativo`, `test_editar_reposicion_corrige_ambos_stocks`, `test_movimientos_de_pedido_solo_editan_fecha_y_descripcion`. |
| CA-05 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_borrar_item_con_historial_lo_descontinua`, `test_borrar_item_sin_historial_lo_elimina`. |
| CA-06 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_estado_automatico_sigue_la_reserva_del_inventario`, `test_equipo_del_gimnasio_conserva_su_estado_manual`. |

## 4. Technical Constraints

- API: [inventory_routes.py](../../../backend/presentation/routes/inventory_routes.py),
  `/api/inventario` y `/api/inventario/movimientos`; acceso `admin/staff`.
- Reglas: [inventory_rules.py](../../../backend/domain/services/inventory_rules.py).
  Datos `INVENTARIO`, `MOV_INV`, `TIENDA_PRODUCTOS` y actor desde sesión.
- Reposición mediante salida con destino `TIENDA`. Un ítem vendible se vincula
  a un solo producto; el catálogo exige tipo Tienda para ese vínculo.
- SQL de relación en `008_enlazar_tienda_inventario.sql` y campos/transacciones
  en `014`/`015`/`016` según sus precondiciones.
- UI: [InventoryView.vue](../../../frontend/src/presentation/views/InventoryView.vue),
  [InventoryMovementsPanel.vue](../../../frontend/src/presentation/components/inventory/InventoryMovementsPanel.vue),
  [inventory.js](../../../frontend/src/application/modules/inventory.js).

## 5. Guardrails

No confundir reserva de almacén con stock disponible para vender. No editar
stock desde el formulario de datos. No permitir que el navegador suplante
el actor del movimiento. No borrar historial como efecto secundario de descontinuar.

## 6. Edge Cases

- Reserva insuficiente o producto sin vínculo para reponer: rechazar sin cambios.
- Cambio de ítem o conversión de una salida en reposición: ajustar ambos lados
  según el movimiento anterior y el nuevo.
- Ajuste que no es el último movimiento del ítem: no admitir su corrección
  cuando invalida la secuencia de existencias.
- Ítem que deja de ser Tienda o se descontinúa: retirar su disponibilidad de venta.
- Fallo de persistencia o conflicto: no publicar solo una mitad de la reposición.

## 7. Definition of Done

Verificar movimientos, vínculos, estados y atomicidad afectados. Para formularios,
usar [26-stock-edit-forms.test.js](../../../frontend/tests/26-stock-edit-forms.test.js).
Para concurrencia de stock, usar PostgreSQL aislado. Cumplir el [DoD](../../docs/DoD.md).
