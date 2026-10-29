# MOD-09 · Tienda, pedidos e imágenes

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Vender productos con stock consistente, conservar el detalle contratado y
gestionar cobro, cancelación y entrega del pedido.

## 2. User Story

**P1.** Como cliente, quiero comprar productos disponibles y consultar mis
pedidos. Como administrador o staff, quiero mantener el catálogo y tramitar
pedidos con el cobro requerido y existencias correctas.

Prueba independiente: crear producto con stock de venta, comprarlo, verificar
descuento de existencias y cancelar un pedido pendiente para recuperarlas.

## 3. Acceptance Criteria

1. **CA-01.** Dado un pedido válido, al crearlo se descuenta solo el stock de
   venta; sin stock suficiente se rechaza sin cambios parciales.
2. **CA-02.** Dado pago con tarjeta, se usa el checkout Stripe y se reserva
   stock; no se acepta tarjeta en el endpoint de creación sin checkout.
3. **CA-03.** Dado un pedido pendiente cancelable, al cancelar se restaura su
   stock; para checkout se cierra la sesión antes de cambiar el estado local.
4. **CA-04.** Dado un fallo al cerrar Stripe o carrera con pago, no se informa
   una cancelación local exitosa. Un pedido impago no puede confirmarse ni entregarse.
5. **CA-05.** Dado un pedido con líneas e importe guardados, al recargar se
   conserva su desglose; el cliente solo consulta sus propios pedidos.
6. **CA-06.** Dada una subida de imagen, solo personal autorizado puede
   publicarla y deben pasar tamaño, extensión y MIME admitidos.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_venta_solo_descuenta_el_stock_de_la_tienda`, `test_venta_sin_stock_suficiente_no_cambia_nada`; [test_atomic_transactions_postgres.py](../../../backend/tests/test_atomic_transactions_postgres.py): `test_two_instances_cannot_sell_the_same_stock`. |
| CA-02 | [store_routes.py](../../../backend/presentation/routes/store_routes.py) y [store_checkout_service.py](../../../backend/application/services/store_checkout_service.py); [test_stripe_checkout.py](../../../backend/tests/test_stripe_checkout.py) cubre el proveedor compartido. |
| CA-03 | [test_partial_smell_fixes.py](../../../backend/tests/test_partial_smell_fixes.py): `test_administrative_cancel_closes_checkout_before_changing_order`; [test_inventario_tienda_stock.py](../../../backend/tests/test_inventario_tienda_stock.py): `test_cancelar_pedido_pendiente_devuelve_stock_a_la_tienda`. |
| CA-04 | [test_partial_smell_fixes.py](../../../backend/tests/test_partial_smell_fixes.py): `test_failed_close_or_a_payment_race_does_not_cancel_the_order`; [store_rules.py](../../../backend/domain/services/store_rules.py). |
| CA-05 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_order_breakdown_survives_persistence_using_its_saved_lines`; [test_priority_fixes.py](../../../backend/tests/test_priority_fixes.py): `test_orders_and_memberships_are_private_and_filtered`. |
| CA-06 | [test_store_images.py](../../../backend/tests/test_store_images.py), [test_priority_fixes.py](../../../backend/tests/test_priority_fixes.py): `test_image_upload_requires_staff_but_listing_remains_public`. |

## 4. Technical Constraints

- API: [store_routes.py](../../../backend/presentation/routes/store_routes.py),
  `/api/tienda`, `/pedidos`, `/pedidos/checkout`, `/pedidos/{id}/cancelar-pago`
  e `/imagenes`, todos bajo `/api/tienda`.
- Reglas: [store_rules.py](../../../backend/domain/services/store_rules.py).
  Casos de uso: [store_checkout_service.py](../../../backend/application/services/store_checkout_service.py)
  e [image service](../../../backend/application/services/store_images_service.py).
- Datos: `TIENDA_PRODUCTOS`, `VENTAS`, `DETALLE_VENTA`, movimientos y relación
  opcional con inventario. Usar las migraciones de pago de tienda y atomicidad.
- Imágenes: JPEG/PNG/WebP/GIF hasta 5 MiB; rutas locales o Supabase según adaptador.
  Catálogo público; mutaciones de productos/imágenes y estado por `admin/staff`.
- UI: `/admin/store`, `/admin/orders`, `/user/store`, `/user/store/payment`,
  [StoreView.vue](../../../frontend/src/presentation/views/StoreView.vue),
  [OrdersView.vue](../../../frontend/src/presentation/views/OrdersView.vue),
  [StorePaymentView.vue](../../../frontend/src/presentation/views/StorePaymentView.vue).

## 5. Guardrails

No vender existencias de reserva. No confirmar/entregar un pedido sin pago
confirmado. No cambiar el importe histórico por editar un producto. No dar por
hecho un reembolso automático: el pago tardío de un cancelado requiere atención.
No aceptar SVG nuevos aunque se listen SVG históricos.

## 6. Edge Cases

- Checkout impago que expira: liberar la reserva mediante la operación de aplicación.
- Cancelación tras pago o con proveedor indisponible: conservar consistencia y
  devolver el conflicto/error correspondiente.
- Pago recibido para pedido cancelado: señalar que requiere reembolso.
- Pedido histórico sin detalles: conservar el total conocido sin inventar líneas.
- Producto sin ítem vinculado: mantener su stock propio compatible con reglas actuales.
- Archivo vacío, excedido o MIME incompatible: rechazar antes de almacenar.

## 7. Definition of Done

Verificar stock, cancelación, privacidad, desglose e imágenes afectados. Los
casos identificados solo por código requieren comprobación reproducible si se
modifican; no suponer cobertura completa por la tabla. Cumplir el [DoD](../../docs/DoD.md).
