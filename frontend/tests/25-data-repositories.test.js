import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createPinia, setActivePinia } from 'pinia';
import { ref } from 'vue';
import { createAttendanceModule } from '../src/application/modules/attendance.js';
import { createClientsModule } from '../src/application/modules/clients.js';
import { createInventoryModule } from '../src/application/modules/inventory.js';
import { createMembershipsModule } from '../src/application/modules/memberships.js';
import { createSchedulesModule } from '../src/application/modules/schedules.js';
import { createStoreModule } from '../src/application/modules/store.js';
import { refreshAfterMutation } from '../src/application/services/refreshAfterMutation.js';
import { createSchedulesRepository } from '../src/infrastructure/repositories/schedulesRepository.js';
import { dataRequest } from '../src/infrastructure/repositories/dataRequest.js';
import { normalizeBackendClientToMember, normalizePlanFromBackend, normalizePromotionFromBackend,
  normalizeStoreOrder, normalizeStoreProductFromBackend, normalizeUser, normalizeBackendAttendanceRecord } from '../src/domain/utils/gymRules.js';

const context = () => ({
  apiBase: '/api', authStore: { token: 'session' }, generation: 0,
  members: ref([]), promotions: ref([]), planCatalog: ref([]),
  attendance: ref([]), attendancePasses: ref([]), routines: ref([]),
  productos_tienda: ref([]), storeOrders: ref([]), cart: ref([]),
  inventory: ref([]), inventoryMovements: ref([]), syncError: ref(''), resourceErrors: new Map(),
});

test('deleting inventory preserves discontinued records and reports the server response', async () => {
  setActivePinia(createPinia());
  const ctx = context();
  ctx.inventory.value = [{ id: 'item-1', name: 'Agua', status: 'Disponible' }];
  ctx.fetchFromBackend = async () => {};
  const result = { accion: 'descontinuado', item: { estado: 'Descontinuado' } };
  const module = createInventoryModule(ctx, {
    deleteInventoryItem: async (id, token) => {
      assert.equal(id, 1);
      assert.equal(token, 'session');
      return result;
    },
  });
  assert.deepEqual(await module.deleteInventoryItem('item-1'), result);
  assert.equal(ctx.inventory.value[0].status, 'Descontinuado');
});

test('deleting inventory without history removes the record after a successful response', async () => {
  setActivePinia(createPinia());
  const ctx = context();
  ctx.inventory.value = [{ id: 'item-1' }];
  const module = createInventoryModule(ctx, { deleteInventoryItem: async () => null });
  await module.deleteInventoryItem('item-1');
  assert.equal(ctx.inventory.value.length, 0);
});

const operations = [
  ['attendance', createAttendanceModule, 'checkinByDniServer', [{ dni: '12345678' }], { id_asistencia: 1 }],
  ['clients', createClientsModule, 'upsertClienteToServer', [{ nombre: 'Ana' }], { id_cliente: 1 }],
  ['inventory', createInventoryModule, 'upsertInventoryToServer', [{ nombre_item: 'Pesas' }], { id_item: 1 }],
  ['memberships', createMembershipsModule, 'refreshPromotionsFromBackend', [], [{ id_promocion: 1 }]],
  ['schedules', createSchedulesModule, 'refreshRoutinesFromBackend', [], [{ id_rutina: 1 }]],
  ['store', createStoreModule, 'refreshStoreProductsFromBackend', [], [{ id_producto: 1 }]],
];

for (const [area, createModule, method, args, result] of operations) {
  test(`${area} works with a data repository and no HTTP or service registry`, async () => {
    setActivePinia(createPinia());
    let calls = 0;
    const repository = { [method]: async (...received) => {
      calls++;
      assert.deepEqual(received, [...args, 'session']);
      return structuredClone(result);
    } };
    const module = createModule(context(), repository);
    const saved = await module[method](...args);
    assert.ok(saved);
    assert.equal(calls, 1);
  });
}

test('all client entry points use a stable identity and the same safe default state', () => {
  const byNumber = normalizeBackendClientToMember({ id_cliente: 7, nombre: 'Ana' });
  const byCode = normalizeBackendClientToMember({ id_usuario: 'SGCLI007', nombre: 'Ana' });
  assert.deepEqual(byNumber, byCode);
  assert.equal(byNumber.status, 'EN_TRAMITE');
  assert.equal(byNumber.internalCode, 'SGCLI007');
  assert.throws(() => normalizeBackendClientToMember({ id_cliente: 7, id_usuario: 'SGCLI008' }), /no coincide/);
});

for (const [name, normalize] of [
  ['client', normalizeBackendClientToMember], ['plan', normalizePlanFromBackend],
  ['promotion', normalizePromotionFromBackend], ['order', normalizeStoreOrder],
  ['product', normalizeStoreProductFromBackend], ['user', normalizeUser], ['attendance', normalizeBackendAttendanceRecord],
]) {
  test(`${name} rejects missing server identities instead of generating an ID`, () => {
    assert.throws(() => normalize({}), /identificador válido/);
  });
}

test('zero prices and zero line subtotals survive normalization', () => {
  const order = normalizeStoreOrder({ id_pedido: 1, total: 0, items: [
    { id_producto: 1, cantidad: 2, precio_unitario: 0, precio: 10, subtotal: 0 },
  ] });
  assert.equal(order.items[0].precio_unitario, 0);
  assert.equal(order.items[0].subtotal, 0);
  const product = normalizeStoreProductFromBackend({ id_producto: 1, precio_venta: 0, stock_minimo: 0 });
  assert.equal(product.precio, 0);
  assert.equal(product.minimo, 0);
});

test('a successful save reports a failed refresh without turning it into a failed save', async () => {
  const ctx = context();
  const ok = await refreshAfterMutation(ctx, async () => { throw new Error('Sin conexión'); });
  assert.equal(ok, false);
  assert.match(ctx.syncError.value, /El cambio se guardó/);
  assert.match(ctx.syncError.value, /Sin conexión/);
  assert.equal(await refreshAfterMutation(ctx, async () => {}), true);
  assert.equal(ctx.syncError.value, '');
});

test('old refresh errors cannot replace the next session warning', async () => {
  const ctx = context();
  let reject;
  const pending = refreshAfterMutation(ctx, () => new Promise((_, fail) => { reject = fail; }));
  ctx.generation++;
  ctx.syncError.value = 'Mensaje de la nueva sesión';
  reject(new Error('Error anterior'));
  assert.equal(await pending, false);
  assert.equal(ctx.syncError.value, 'Mensaje de la nueva sesión');
});

test('cancellation never rebuilds the cart with stale stock when the catalogue refresh fails', async () => {
  setActivePinia(createPinia());
  const ctx = context();
  ctx.productos_tienda.value = [{ id_producto: 1, nombre: 'Agua', cantidad: 10 }];
  const module = createStoreModule(ctx, {
    cancelStoreCheckout: async () => ({ cancelled: true, items: [{ id_producto: 1, cantidad: 2 }] }),
    refreshStoreProductsFromBackend: async () => { throw new Error('Sin conexión'); },
  });
  const result = await module.cancelStoreCheckout(1);
  assert.equal(result.refreshPending, true);
  assert.deepEqual(result.restored, []);
  assert.deepEqual(ctx.cart.value, []);
  assert.match(ctx.syncError.value, /El cambio se guardó/);
});

test('schedule filters and tokens are encoded by infrastructure', async () => {
  let request;
  const repository = createSchedulesRepository({
    authHeaders: (token) => ({ Authorization: `Bearer ${token}` }),
    rawRequest: async (url, options) => {
      request = { url, options };
      return new Response('[]', { headers: { 'content-type': 'application/json' } });
    },
  }, '/api');
  await repository.refreshEnrollmentsFromBackend({ dni: '123 & 456' }, 'session');
  assert.equal(request.url, '/api/gym/matriculas?dni=123+%26+456');
  assert.equal(request.options.headers.Authorization, 'Bearer session');
});

test('data repositories reject HTML gateways and explain validation failures', async () => {
  const http = { authHeaders: () => ({}), rawRequest: async () => new Response('<html>proxy</html>', {
    headers: { 'content-type': 'text/html' },
  }) };
  await assert.rejects(dataRequest(http, '/api'), /datos esperados/);
  http.rawRequest = async () => new Response(JSON.stringify({ detail: [{ loc: ['body', 'precio'], msg: 'Debe ser positivo' }] }), {
    status: 422, headers: { 'content-type': 'application/json' },
  });
  await assert.rejects(dataRequest(http, '/api'), /Precio: Debe ser positivo/);
});

test('partial client edits preserve membership and payment details while accepting a zero amount', () => {
  const previous = normalizeBackendClientToMember({ id_cliente: 1, nombre: 'Ana', membership_status: 'ACTIVO',
    id_membresia: 7, membership_start: '2026-10-01', membership_end: '2026-10-31',
    payment_status: 'PAGADO', monto_pago: 79,
  });
  const edited = normalizeBackendClientToMember({ id_cliente: 1, nombre: 'Ana Pérez', monto_pago: 0 }, previous);
  assert.equal(edited.name, 'Ana Pérez');
  assert.equal(edited.id_membresia, 7);
  assert.equal(edited.membershipEnd, '2026-10-31');
  assert.equal(edited.membershipStatus, 'ACTIVO');
  assert.equal(edited.paymentStatus, 'PAGADO');
  assert.equal(edited.membershipPrice, 0);
});
