import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupComponent, setupView } from '../../soporte/entorno-formularios.js';

const ITEM = { id: 'item-1', inventoryCode: 'ACT-1001', name: 'Mancuerna hexagonal 5 kg par', category: 'Equipo de fuerza',
  location: 'Almacén', quantity: 2, minQuantity: 1, archived: false, byUnit: true, n_activo: 1001 };
const STORE_ITEM = { id: 'item-2', inventoryCode: 'ACT-1002', name: 'Agua', category: 'Tienda', location: 'Almacén',
  quantity: 10, minQuantity: 1, archived: false, byUnit: false };
// Atributo disabled real del botón (no la clase CSS "disabled:cursor-not-allowed").
const DISABLED_BUTTON = /<button\b[^>]*?\sdisabled(?=[\s>=])/;
const UNITS = [
  { id_unidad: 11, id_item: 1, correlativo: 1, codigo: '1001-MH-001', estado: 'Operativo', ubicacion: 'Almacén' },
  { id_unidad: 12, id_item: 1, correlativo: 2, codigo: '1001-MH-002', estado: 'Operativo', ubicacion: 'Sala 1' },
  { id_unidad: 13, id_item: 1, correlativo: 3, codigo: '1001-MH-003', estado: 'Dado de baja', ubicacion: 'Almacén', fecha_baja: '2026-11-20' },
];

test('B-06: la pestaña Bajas lista las bajas con sus filtros y el contador de 40 caracteres', async () => {
  const { setup, html } = await setupComponent('inventory/InventoryRetirementsPanel', {}, (_setup, gym) => {
    gym.inventory = [ITEM, { ...STORE_ITEM, archived: true, retiredAt: '2026-10-02' }];
    gym.inventoryUnits = UNITS;
    gym.inventoryMovements = [{ id_mov: 3, tipo_movimiento: 'salida', id_unidad: 13, descripcion: 'Óxido · Unidades: 1001-MH-003' }];
  });
  assert.match(html, /Bajas de inventario/);
  assert.match(html, /1001-MH-003/);
  assert.match(html, /ACT-1002/);
  assert.match(html, /Óxido/);
  assert.match(html, /Todos los meses/);
  assert.match(html, /Noviembre 2026/);
  assert.match(html, /0\/40/);
  assert.match(html, /Descargar Excel/);
  assert.doesNotMatch(html, DISABLED_BUTTON);
  setup.monthFilter = '2026-10';
  assert.deepEqual(setup.filteredRows.map((row) => row.codigo), ['ACT-1002']);
});

test('B-06: sin bajas se muestra el estado vacío y el Excel queda deshabilitado', async () => {
  const { html } = await setupComponent('inventory/InventoryRetirementsPanel', {}, (_setup, gym) => {
    gym.inventory = [ITEM];
    gym.inventoryUnits = UNITS.slice(0, 2);
  });
  assert.match(html, /Todavía no hay bajas registradas/);
  assert.match(html, DISABLED_BUTTON);
});

test('B-07: Inventario muestra las pestañas Artículos, Movimientos y Bajas y abre Bajas por la URL', async () => {
  const { setup, html } = await setupView('InventoryView', '/admin/inventory', null, { tab: 'bajas' });
  assert.deepEqual(setup.tabs.map((tab) => tab.label), ['Artículos', 'Movimientos', 'Bajas']);
  assert.equal(setup.activeTab, 'bajas');
  assert.equal(setup.retirementsVisited, true);
  assert.match(html, />\s*Bajas\s*</);
});

test('T-07: con un equipo con N° de activo aparece Traslado con unidades y ubicación, sin destino Tienda', async () => {
  const { setup } = await setupComponent('inventory/InventoryMovementsPanel', {}, (_setup, gym) => {
    gym.inventory = [ITEM, STORE_ITEM];
    gym.inventoryUnits = UNITS;
  });
  setup.form.id_item = 1;
  assert.deepEqual(setup.availableMovementTypes.map((option) => option.value), ['entrada', 'salida', 'ajuste', 'traslado']);
  setup.form.tipo_movimiento = 'traslado';
  assert.equal(setup.isTransfer, true);
  assert.equal(setup.needsUnitPick, true);
  assert.deepEqual(setup.selectableUnits.map((unit) => unit.codigo), ['1001-MH-001', '1001-MH-002']);
  assert.equal(setup.projectedStock, 2);
  assert.ok(setup.transferLocationOptions.includes('Sala de fuerza'));

  setup.form.id_item = 2;
  assert.deepEqual(setup.availableMovementTypes.map((option) => option.value), ['entrada', 'salida', 'ajuste']);
});

test('T-07: el traslado exige destino y envía unidades y ubicación al servidor', async () => {
  const { setup, gym } = await setupComponent('inventory/InventoryMovementsPanel', {}, (_setup, store) => {
    store.inventory = [ITEM];
    store.inventoryUnits = UNITS;
  });
  const sent = [];
  gym.registrarMovimientoToServer = async (payload) => { sent.push(payload); return { movimiento: { id_mov: 1 } }; };
  setup.openNew();
  Object.assign(setup.form, { id_item: 1, tipo_movimiento: 'traslado', unidades: [11, 12] });
  await setup.save();
  assert.equal(sent.length, 0);
  assert.match(setup.modalError, /ubicación de destino/);

  setup.form.ubicacion_destino = 'Sala de fuerza';
  await setup.save();
  assert.equal(sent.length, 1);
  assert.deepEqual([sent[0].tipo_movimiento, sent[0].unidades, sent[0].ubicacion_destino, sent[0].cantidad], ['traslado', [11, 12], 'Sala de fuerza', 2]);
  assert.equal(sent[0].destino, null);
  assert.match(setup.feedback, /Traslado registrado: 2 unidades a Sala de fuerza/);
});

test('P-06: Pedidos permite cancelar un pedido CONFIRMADO pero no uno ENTREGADO', async () => {
  const { setup } = await setupView('OrdersView', '/admin/orders');
  assert.equal(setup.canCancel({ estado_pedido: 'CONFIRMADO' }), true);
  assert.equal(setup.canCancel({ estado_pedido: 'PENDIENTE' }), true);
  assert.equal(setup.canCancel({ estado_pedido: 'ENTREGADO' }), false);
});

test('E-01: el listado de Inventario ofrece Descargar Excel solo cuando hay filas', async () => {
  const empty = await setupComponent('inventory/InventoryListHeader', { items: [] });
  assert.match(empty.html, DISABLED_BUTTON);
  const full = await setupComponent('inventory/InventoryListHeader', { items: [ITEM] });
  assert.doesNotMatch(full.html, DISABLED_BUTTON);
  assert.match(full.html, /Listado de inventario/);
});
