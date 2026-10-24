import assert from 'node:assert/strict';
import { test, before, after } from 'node:test';
import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';
import { createPinia, setActivePinia } from 'pinia';
let createGymState;
let createGymModules;
let getApplicationServices;
let server;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('..', import.meta.url)), configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  await server.ssrLoadModule('/src/bootstrap.js');
  ({ createGymState } = await server.ssrLoadModule('/src/application/modules/state.js'));
  ({ createGymModules } = await server.ssrLoadModule('/src/application/services/gymModules.js'));
  ({ getApplicationServices } = await server.ssrLoadModule('/src/application/ports/services.js'));
});

after(async () => { await server?.close(); });

const fixture = (repositories = {}) => {
  setActivePinia(createPinia());
  const state = createGymState();
  state.authStore.token = 'test-session';
  state.authStore.userRole = 'trainer';
  return { state, modules: createGymModules(state, repositories) };
};

const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};

test('independent module assemblies keep state isolated and do not mount operations on shared state', () => {
  const first = fixture();
  const second = fixture();
  first.modules.store.addToCart({ id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 9 }, 2);
  assert.equal(first.state.cart.value.length, 1);
  assert.equal(second.state.cart.value.length, 0);
  assert.equal(first.state.upsertMember, undefined);
  assert.equal(first.state.fetchFromBackend, undefined);
  assert.equal(second.modules.clients.memberById('SGCLI001'), null);
});

test('membership renewal uses client lookup and history through declared capabilities', async () => {
  const { state, modules } = fixture({ memberships: {
    assignPlanToMember: async (body, token) => {
      assert.equal(body.id_cliente, 1);
      assert.equal(body.id_pm, 1);
      assert.equal(token, 'test-session');
      return { id_membresia: 8, monto_pago: 45, estado: 'EN_TRAMITE', estado_pago: 'PENDIENTE' };
    },
  } });
  state.members.value = [{ id: 'SGCLI001', id_cliente: 1, name: 'Ana', planId: 'pm-1', membershipPrice: 40 }];
  state.planCatalog.value = [{ id: 'pm-1', name: 'Especial', durationDays: 45, price: 45 }];
  const member = await modules.memberships.renewMembership('SGCLI001');
  assert.equal(member.plan, 'Especial');
  assert.equal(member.membershipPrice, 45);
  assert.equal(modules.clients.memberById('SGCLI001').id_membresia, 8);
  assert.equal(member.changeHistory.length, 1);
});

test('trainer and section synchronization share only their activity counter', async () => {
  const waiting = deferred();
  const services = getApplicationServices();
  const original = services.http.apiGet;
  services.http.apiGet = async path => {
    assert.equal(path, '/planes-membresia');
    return [{ id_pm: 1, nombre_plan: 'Especial', duracion: '45 dias', precio: 45 }];
  };
  try {
    const { state, modules } = fixture({ schedules: { fetchTrainerOverview: () => waiting.promise } });
    const overview = modules.schedules.fetchTrainerOverview();
    assert.equal(state.activeSyncs, 1);
    await modules.synchronization.fetchFromBackend({ section: 'plans' });
    assert.equal(state.planCatalog.value[0].name, 'Especial');
    assert.equal(state.activeSyncs, 1);
    assert.equal(state.isSyncing.value, true);
    waiting.resolve({ clientes: [] });
    await overview;
    assert.equal(state.activeSyncs, 0);
    assert.equal(state.isSyncing.value, false);
  } finally {
    services.http.apiGet = original;
  }
});

test('a trainer response from before reset cannot change the next generation or its activity counter', async () => {
  const waiting = deferred();
  const { state, modules } = fixture({ schedules: { fetchTrainerOverview: () => waiting.promise } });
  const pending = modules.schedules.fetchTrainerOverview();
  const rejection = assert.rejects(pending, /sesión ha cambiado/);
  state.resetState();
  waiting.resolve({ clientes: [{ dni: '12345678' }] });
  await rejection;
  assert.equal(state.activeSyncs, 0);
  assert.equal(state.isSyncing.value, false);
  assert.equal(state.trainerOverview.value?.clientes?.length || 0, 0);
});
