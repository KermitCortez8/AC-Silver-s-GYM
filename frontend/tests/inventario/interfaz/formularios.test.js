import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

test('editing inventory preserves a zero threshold and uses one only when the value is absent', async () => {
  const { setup, gym } = await setupView('InventoryView', '/admin/inventory');
  const item = { id: 'item-1', name: 'Pesas', category: 'Equipo', quantity: 1, minQuantity: 0, status: 'Operativo' };
  setup.editItem(item);
  assert.equal(setup.form.minQuantity, 0);
  setup.editItem({ ...item, minQuantity: undefined });
  assert.equal(setup.form.minQuantity, 1);
  setup.editItem(item);
  let payload;
  gym.upsertInventoryItem = async (value) => { payload = { ...value }; };
  await setup.handleSubmit();
  assert.equal(payload.minQuantity, 0);
  assert.equal(setup.feedbackTone, 'success');
});

test('inventario conserva los avisos en vivo al combinar las ramas', async () => {
  const { setup } = await setupView('InventoryView', '/admin/inventory');
  setup.openNewItem();
  setup.touch('name');
  assert.match(setup.warnings.name, /obligatorio/);
  setup.form.name = 'Pesas';
  assert.equal(setup.warnings.name, '');
  setup.touch('minQuantity');
  assert.match(setup.warnings.minQuantity, /obligatorio/);
  setup.form.minQuantity = 0;
  assert.equal(setup.warnings.minQuantity, '');
  setup.form.minQuantity = '1.5';
  assert.match(setup.warnings.minQuantity, /entero/);
});

test('inventory rejects malformed quantities without saving or losing the draft', async () => {
  const { setup, gym } = await setupView('InventoryView', '/admin/inventory');
  setup.openNewItem();
  setup.form.name = 'Mancuerna';
  let saves = 0;
  gym.upsertInventoryItem = async () => { saves++; };
  for (const value of ['', '-1', '+2', '1.5', '1e2', '12abc', '2147483648']) {
    setup.form.quantity = value;
    await setup.handleSubmit();
    assert.equal(saves, 0, `No se debe guardar ${JSON.stringify(value)}`);
    assert.ok(setup.editorError);
    assert.equal(setup.isEditorOpen, true);
    assert.equal(setup.form.quantity, value);
    assert.equal(setup.form.name, 'Mancuerna');
  }
  setup.form.quantity = '12';
  setup.form.minQuantity = '1e2';
  await setup.handleSubmit();
  assert.equal(saves, 0);
  setup.form.minQuantity = '0';
  await setup.handleSubmit();
  assert.equal(saves, 1);
  assert.equal(setup.isEditorOpen, false);
});

test('inventory keeps server errors inside the editor and prevents duplicate saves', async () => {
  const { setup, gym } = await setupView('InventoryView', '/admin/inventory');
  setup.openNewItem();
  setup.form.name = 'Agua';
  let saves = 0;
  let reject;
  gym.upsertInventoryItem = () => {
    saves++;
    return new Promise((resolve, fail) => { reject = fail; });
  };
  // Sin stock minimo no se guarda: no hay valor por defecto.
  await setup.handleSubmit();
  assert.equal(saves, 0);
  assert.deepEqual(setup.formErrors, ['Stock mínimo']);
  setup.form.minQuantity = '5';
  const pending = setup.handleSubmit();
  await setup.handleSubmit();
  setup.closeEditor();
  assert.equal(saves, 1);
  assert.equal(setup.isSaving, true);
  assert.equal(setup.isEditorOpen, true);
  reject(new Error('Sin conexión'));
  await pending;
  assert.equal(setup.editorError, 'Sin conexión');
  assert.equal(setup.isEditorOpen, true);
  assert.equal(setup.form.name, 'Agua');
  assert.equal(setup.isSaving, false);
});

test('inventory dropdowns contain defaults and preserve existing custom values', async () => {
  const { setup, dialogs } = await setupView('InventoryView', '/admin/inventory', (setup, gym) => {
    const item = { id: 'item-1', name: 'Discos', category: 'Especial', location: 'Depósito B', unidad_venta: 'lote', quantity: 1 };
    gym.inventory = [item];
    setup.editItem(item);
  });
  for (const value of ['Tienda', 'Equipo de fuerza', 'Especial']) assert.ok(setup.categoryOptions.includes(value));
  assert.ok(setup.editorLocationOptions.includes('Depósito B'));
  assert.ok(setup.unitOptions.includes('lote'));
  assert.match(dialogs, /<select[^>]*>[\s\S]*Especial[\s\S]*<\/select>/);
  assert.match(dialogs, /pattern="\[0-9\]\+"/);
});

test('inventory searches the advertised code, name and category fields', async () => {
  const { setup, gym } = await setupView('InventoryView', '/admin/inventory');
  gym.inventory = [
    { id: 'item-1', name: 'Mancuerna', inventoryCode: 'ACT-0001', category: 'Fuerza' },
    { id: 'item-2', name: 'Agua', inventoryCode: 'ACT-0002', category: 'Tienda' },
  ];
  for (const value of ['ACT-0001', 'mancu', 'FUERZA']) {
    setup.searchQuery = value;
    assert.deepEqual(setup.filteredInventory.map(item => item.id), ['item-1']);
  }
});

test('stock alert compares typed quantities numerically', async () => {
  const { dialogs } = await setupView('InventoryView', '/admin/inventory', (setup) => {
    setup.openNewItem();
    setup.form.quantity = '12';
    setup.form.minQuantity = '2';
  });
  assert.doesNotMatch(dialogs, /Alerta activa/);
});

test('movement quantity buttons preserve invalid drafts instead of converting exponents', async () => {
  const { setup } = await setupView('InventoryMovementsView', '/admin/inventory/movements');
  setup.form.cantidad = '1e2';
  setup.stepCantidad(1);
  assert.equal(setup.form.cantidad, '1e2');
  assert.ok(setup.errors.cantidad);
  setup.form.cantidad = '12';
  setup.stepCantidad(1);
  assert.equal(setup.form.cantidad, 13);
});

test('movement editor refuses invalid quantities and sends valid quantities as integers', async () => {
  const { setup, gym } = await setupView('../components/inventory/InventoryMovementsPanel', '/admin/inventory');
  gym.inventory = [{ id: 'item-1', quantity: 10, name: 'Agua' }];
  setup.openNew();
  setup.form.id_item = 1;
  let payload;
  gym.registrarMovimientoToServer = async value => { payload = value; };
  for (const value of [0, '', -1, '1.5', '1e2']) {
    setup.form.cantidad = value;
    await setup.save();
    assert.equal(payload, undefined);
    assert.ok(setup.modalError);
    assert.equal(setup.isModalOpen, true);
  }
  setup.form.cantidad = '3';
  await setup.save();
  assert.equal(payload.cantidad, 3);
  assert.equal(setup.isModalOpen, false);
});
