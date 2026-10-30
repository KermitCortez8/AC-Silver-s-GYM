import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createPinia, setActivePinia } from 'pinia';
import { ref } from 'vue';
import { createAttendanceModule } from '../src/application/modules/attendance.js';
import { createClientsModule } from '../src/application/modules/clients.js';
import { createDashboardModule } from '../src/application/modules/dashboard.js';
import { createInventoryModule } from '../src/application/modules/inventory.js';
import { createMembershipsModule } from '../src/application/modules/memberships.js';
import { createSchedulesModule } from '../src/application/modules/schedules.js';
import { createStoreModule } from '../src/application/modules/store.js';
import { createUsersModule } from '../src/application/modules/users.js';
import { createResourceCache } from '../src/application/services/resourceCache.js';

const snapshot = value => JSON.parse(JSON.stringify(value));

const context = () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  return {
    pinia, apiBase: '/api', authStore: { token: 'test', userRole: 'admin' }, generation: 0,
    members: ref([{ id: 'SGCLI001', id_cliente: 1, name: 'Ana' }]),
    users: ref([{ id_usuario: 'SGSTA001', nombre: 'Ana' }]),
    inventory: ref([{ id: 'item-1', name: 'Agua', quantity: 10 }]),
    attendance: ref([{ id_asistencia: 1 }]), attendancePasses: ref([]),
    inventoryMovements: ref([{ id_mov: 1 }]), planCatalog: ref([{ id: 'pm-1', id_pm: 1 }]),
    promotions: ref([{ id: 'promo-1', id_promocion: 1 }]),
    productos_tienda: ref([{ id_producto: 1, nombre: 'Agua', cantidad: 3, precio: 2, estado: 'Disponible' }]),
    storeOrders: ref([{ id_pedido: 1 }]), cart: ref([]),
    routines: ref([{ id_rutina: 1 }]), schedule: ref([{ id_horario: 1 }]),
    serviceSchedules: ref([{ id_horario_servicio: 1 }]), enrollments: ref([{ id_matricula: 1 }]),
    gymSettings: ref({ capacidad_total: 30, capacidad_por_hora: 10 }),
    trainerOverview: ref({ clientes: [{ nombre: 'Ana' }] }), trainerOverviewCache: createResourceCache(),
    isSyncing: ref(false), activeSyncs: 0, resourceErrors: new Map(), syncError: ref(''),
    fetchFromBackend: async () => {}, logMemberEvent: () => {},
  };
};

const reads = [
  ['attendance', createAttendanceModule, 'refreshAttendanceFromBackend', 'attendance'],
  ['inventory movements', createInventoryModule, 'refreshInventoryMovementsFromBackend', 'inventoryMovements'],
  ['promotions', createMembershipsModule, 'refreshPromotionsFromBackend', 'promotions'],
  ['products', createStoreModule, 'refreshStoreProductsFromBackend', 'productos_tienda'],
  ['orders', createStoreModule, 'refreshStoreOrdersFromBackend', 'storeOrders'],
  ['routines', createSchedulesModule, 'refreshRoutinesFromBackend', 'routines'],
  ['service schedules', createSchedulesModule, 'refreshServiceSchedulesFromBackend', 'serviceSchedules'],
  ['enrollments', createSchedulesModule, 'refreshEnrollmentsFromBackend', 'enrollments'],
  ['dashboard settings', createDashboardModule, 'refreshGymSettingsFromBackend', 'gymSettings', 'load'],
  ['trainer overview', createSchedulesModule, 'fetchTrainerOverview', 'trainerOverview'],
];

for (const [label, create, method, field, repositoryMethod = method] of reads) {
  test(`${label}: failed or malformed reads retain the last valid state and clear loading`, async () => {
    const ctx = context();
    const before = snapshot(ctx[field].value);
    let response;
    const module = create(ctx, { [repositoryMethod]: async () => {
      if (response instanceof Error) throw response;
      return response;
    } });
    const malformed = ['dashboard settings', 'trainer overview'].includes(label)
      ? [null, [], 'incorrecto'] : [null, {}, [null], [{}]];
    for (response of [new Error('Servidor no disponible'), ...malformed]) {
      await assert.rejects(module[method](), Error);
      assert.deepEqual(ctx[field].value, before);
      assert.equal(ctx.isSyncing.value, false);
    }
  });
}

const writes = [
  ['users', createUsersModule, 'upsertUser', 'users', { nombre: 'Ana', correo: 'ana@example.com' }, 'save'],
  ['clients', createClientsModule, 'upsertClient', 'members', { id_usuario: 'SGCLI001', nombre: 'Ana' }, 'upsertClienteToServer'],
  ['plans', createMembershipsModule, 'upsertPlan', 'planCatalog', { id_pm: 1, name: 'Mensual' }],
  ['promotions', createMembershipsModule, 'upsertPromotion', 'promotions', { id_promocion: 1, name: 'Verano' }],
  ['inventory', createInventoryModule, 'upsertInventoryItem', 'inventory', { id: 'item-1', name: 'Agua', quantity: 2 }, 'upsertInventoryToServer'],
  ['products', createStoreModule, 'upsertProductoTienda', 'productos_tienda', { id_producto: 1, nombre: 'Agua', cantidad: 1 }],
  ['routines', createSchedulesModule, 'upsertRutina', 'routines', { nombre_rutina: 'Fuerza' }],
  ['trainer routines', createSchedulesModule, 'upsertTrainerRoutine', 'routines', { nombre_rutina: 'Fuerza' }],
  ['schedules', createSchedulesModule, 'upsertHorario', 'schedule', { id_cliente: 1, id_rutina: 1 }],
  ['service schedules', createSchedulesModule, 'upsertServiceSchedule', 'serviceSchedules', { id_rutina: 1 }],
  ['enrollments', createSchedulesModule, 'enrollSchedule', 'enrollments', { id_cliente: 1 }],
  ['new clients', createClientsModule, 'upsertClient', 'members', { nombre: 'Ana' }, 'registerAdmin'],
  ['public registration', createClientsModule, 'registerPublicClient', 'members', { nombre: 'Ana' }],
];

for (const [label, create, method, field, payload, repositoryMethod = method] of writes) {
  test(`${label}: failed or unconfirmed saves do not publish a local record`, async () => {
    const ctx = context();
    const before = snapshot(ctx[field].value);
    let response;
    const module = create(ctx, { [repositoryMethod]: async () => {
      if (response instanceof Error) throw response;
      return response;
    } });
    for (response of [new Error('No se pudo guardar'), null, [], {}]) {
      await assert.rejects(module[method](payload), Error);
      assert.deepEqual(ctx[field].value, before);
    }
  });
}

for (const [label, create, method, field, id, repositoryMethod = method] of [
  ['users', createUsersModule, 'deleteUser', 'users', 'SGSTA001', 'remove'],
  ['clients', createClientsModule, 'deleteClient', 'members', 'SGCLI001', 'deleteMember'],
  ['inventory', createInventoryModule, 'deleteInventoryItem', 'inventory', 'item-1'],
  ['products', createStoreModule, 'deleteProductoTienda', 'productos_tienda', 1],
  ['plans', createMembershipsModule, 'deletePlan', 'planCatalog', 'pm-1'],
  ['promotions', createMembershipsModule, 'deletePromotion', 'promotions', 'promo-1'],
  ['schedules', createSchedulesModule, 'deleteServiceSchedule', 'serviceSchedules', 1],
  ['enrollments', createSchedulesModule, 'deleteEnrollment', 'enrollments', 1],
]) {
  test(`${label}: rejected deletes preserve local data`, async () => {
    const ctx = context();
    const before = snapshot(ctx[field].value);
    const module = create(ctx, { [repositoryMethod]: async () => { throw new Error('No se pudo eliminar'); } });
    await assert.rejects(module[method](id), /No se pudo eliminar/);
    assert.deepEqual(ctx[field].value, before);
  });
}

test('cart rejects malformed quantities and repeated additions beyond stock without changing state', () => {
  const ctx = context();
  const store = createStoreModule(ctx, {});
  const product = ctx.productos_tienda.value[0];
  store.addToCart(product, 2);
  const before = snapshot(ctx.cart.value);
  for (const invalid of [0, -1, '1e2', '1.5', '', NaN, 4]) {
    assert.throws(() => store.addToCart(product, invalid));
    assert.throws(() => store.updateCartQuantity(1, invalid));
    assert.deepEqual(ctx.cart.value, before);
  }
  assert.throws(() => store.addToCart(product, 2), /stock/);
  assert.deepEqual(ctx.cart.value, before);
  store.updateCartQuantity(1, '3');
  assert.equal(ctx.cart.value[0].cantidad, 3);
});

test('a local order validates every line and duplicate totals before changing stock or clearing the cart', async () => {
  const ctx = context();
  ctx.apiBase = '';
  ctx.cart.value = [{ id_producto: 1, cantidad: 2 }];
  const store = createStoreModule(ctx, {});
  for (const items of [
    [{ id_producto: 1, cantidad: 2 }, { id_producto: 2, cantidad: 1 }],
    [{ id_producto: 1, cantidad: 2 }, { id_producto: 1, cantidad: 2 }],
    [{ id_producto: 1, cantidad: '1e2' }],
  ]) {
    await assert.rejects(store.createStoreOrder({ items }), Error);
    assert.equal(ctx.productos_tienda.value[0].cantidad, 3);
    assert.equal(ctx.cart.value.length, 1);
    assert.equal(ctx.storeOrders.value.length, 1);
  }
  await store.createStoreOrder();
  assert.equal(ctx.productos_tienda.value[0].cantidad, 1);
  assert.equal(ctx.cart.value.length, 0);
});

test('failed checkout retains the cart and sends no request for invalid quantities', async () => {
  const ctx = context();
  ctx.cart.value = [{ id_producto: 1, cantidad: '1e2' }];
  let calls = 0;
  const store = createStoreModule(ctx, { createStoreCheckout: async () => {
    calls++;
    throw new Error('Stripe no disponible');
  } });
  await assert.rejects(store.createStoreCheckout(), Error);
  assert.equal(calls, 0);
  ctx.cart.value[0].cantidad = 2;
  await assert.rejects(store.createStoreCheckout(), /Stripe/);
  assert.equal(calls, 1);
  assert.equal(ctx.cart.value[0].cantidad, 2);
});

test('capacity zero is reported instead of replaced with a default', async () => {
  const ctx = context();
  const dashboard = createDashboardModule(ctx, { save: async () => { throw new Error('Should not be called'); } });
  await assert.rejects(dashboard.updateGymSettings({ capacidad_total: 0 }), /capacidad total/);
  assert.equal(ctx.gymSettings.value.capacidad_total, 30);
});

test('unconfirmed inventory movements do not append a local history entry', async () => {
  const ctx = context();
  const inventory = createInventoryModule(ctx, { registrarMovimientoToServer: async () => ({}) });
  await assert.rejects(inventory.registrarMovimientoToServer({ id_item: 1, cantidad: 2 }), /datos incompletos/);
  assert.equal(ctx.inventoryMovements.value.length, 1);
  assert.equal(ctx.inventory.value[0].quantity, 10);
});
