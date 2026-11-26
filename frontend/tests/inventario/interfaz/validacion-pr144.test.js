// Validación del PR #144 (dennis-ite-final).
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupComponent, setupView } from '../../soporte/entorno-formularios.js';
import { DEFAULT_PAGE_SIZE } from '../../../src/domain/utils/inputRules.js';

const retiredItems = (count) => Array.from({ length: count }, (_, index) => ({
  id: `item-${index + 1}`, inventoryCode: `ACT-${1001 + index}`, name: `Artículo ${index + 1}`, category: 'Tienda',
  location: 'Almacén', quantity: 0, minQuantity: 0, archived: true, retiredAt: '2026-11-20', observations: 'Baja de prueba',
}));

const order = (changes) => ({
  id_pedido: 1, id_cliente: 1, cliente_nombre: 'Ana', fecha_pedido: '2026-11-25T15:00:00Z', total: 10,
  items: [{ id_producto: 1, nombre_producto: 'Agua', cantidad: 1, precio_unitario: 10, subtotal: 10 }], ...changes,
});

test('VAL-01: Bajas pagina sus filas y la última página trae el resto', async () => {
  const { setup } = await setupComponent('inventory/InventoryRetirementsPanel', {}, (_setup, gym) => {
    gym.inventory = retiredItems(22);
  });
  assert.equal(setup.filteredRows.length, 22);
  assert.equal(setup.pagedRows.length, Math.min(DEFAULT_PAGE_SIZE, 22));
  setup.pageSize = 5;
  setup.page = 5;
  assert.equal(setup.pagedRows.length, 2);
});

test('VAL-02: un pedido Yape cancelado no se muestra como "YAPE POR CONFIRMAR"', { todo: 'Defecto reportado: Yape cancelado se rotula por confirmar' }, async () => {
  const { html } = await setupView('OrdersView', '/admin/orders', (_setup, gym) => {
    gym.storeOrders = [order({ metodo_pago: 'yape', estado_pago: 'PENDIENTE', estado_pedido: 'CANCELADO' })];
  });
  assert.match(html, /CANCELADO/);
  assert.doesNotMatch(html, /YAPE POR CONFIRMAR/);
});

test('VAL-03: el panel de ventas de Tienda no incluye un Yape sin confirmar', async () => {
  const { setup } = await setupComponent('store/StoreMovementsPanel', {}, (_setup, gym) => {
    gym.storeOrders = [
      order({ id_pedido: 1, metodo_pago: 'yape', estado_pago: 'PENDIENTE', estado_pedido: 'PENDIENTE' }),
      order({ id_pedido: 2, metodo_pago: 'plin', estado_pago: 'PAGADO', estado_pedido: 'CONFIRMADO' }),
    ];
  });
  assert.equal(setup.movements.length, 1);
});
