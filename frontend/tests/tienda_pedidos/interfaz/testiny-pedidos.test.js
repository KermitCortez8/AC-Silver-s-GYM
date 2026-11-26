import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

const paid = { id_pedido: 1, id_cliente: 1, cliente_nombre: 'Cliente QA', cliente_dni: '11111111',
  fecha_pedido: '2026-10-07T15:00:00Z', estado_pago: 'PAGADO', estado_pedido: 'PENDIENTE',
  metodo_pago: 'Yape', referencia_pago: 'referencia-qa', total: 35.40,
  items: [{ id_producto: 1, nombre_producto: 'Botella QA', cantidad: 2, precio_unitario: 15, subtotal: 30 }] };

test('TC-106 y TC-108: pedidos cobrados muestran líneas y excluyen impagos de ventas', async () => {
  const { setup: s, html } = await setupView('OrdersView', '/admin/orders', (_s, gym) => {
    gym.storeOrders = [paid, { ...paid, id_pedido: 2, estado_pago: 'PENDIENTE', metodo_pago: 'tarjeta', total: 900 },
      { ...paid, id_pedido: 3, cliente_nombre: 'Control QA', cliente_dni: '22222222', total: 1000,
        items: [{ nombre_producto: 'Control', cantidad: 1 }], estado_pedido: 'CANCELADO' }];
  });
  assert.deepEqual(s.orders.map(row => row.id_pedido), [1, 3]);
  assert.equal(s.totalSales, 35.40);
  assert.equal(s.pendingOrders.length, 1);
  assert.match(html, /Cliente QA/);
  assert.match(html, /Botella QA/);
  assert.match(html, /35\.40/);
  for (const query of ['Cliente QA', '11111111', '1', 'Botella QA']) {
    s.search = query;
    assert.ok(s.filteredOrders.some(row => row.id_pedido === 1));
    assert.ok(!s.filteredOrders.some(row => row.id_pedido === 2));
  }
});

test('TC-106: confirmar y entregar usan la observación guardada y actualizar reconsulta el módulo', async () => {
  const { setup: s, gym } = await setupView('OrdersView', '/admin/orders');
  const calls = [];
  const loads = [];
  gym.updateStoreOrderStatus = async (...args) => { calls.push(args); };
  gym.fetchFromBackend = async (value) => { loads.push(value); };
  for (const state of ['CONFIRMADO', 'ENTREGADO']) {
    s.ensureDraft(paid).estado_pedido = state;
    s.ensureDraft(paid).observacion_admin = 'Entrega QA';
    await s.updateOrder(paid);
    assert.equal(calls.at(-1)[0], 1);
    assert.equal(calls.at(-1)[1].estado_pedido, state);
    assert.equal(calls.at(-1)[1].observacion_admin, 'Entrega QA');
    assert.equal(s.savingOrders.size, 0);
  }
  await s.refresh();
  assert.ok(loads.some(options => options.section === 'orders' && options.force));
});
