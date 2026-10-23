import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { ref } from 'vue';
import { createUsersModule } from '../src/application/modules/users.js';
import { createDashboardModule } from '../src/application/modules/dashboard.js';
import { configureApplicationServices } from '../src/application/ports/services.js';
import { loadMembershipPlans } from '../src/application/services/publicCatalog.js';
import { confirmMembershipPayment } from '../src/application/services/clientPayments.js';

const root = fileURLToPath(new URL('../src/', import.meta.url));
const files = async (directory) => (await Promise.all((await readdir(directory, { withFileTypes: true }))
  .map((entry) => entry.isDirectory() ? files(join(directory, entry.name)) : [join(directory, entry.name)]))).flat();

test('domain, application and presentation keep their dependency boundaries', async () => {
  for (const layer of ['domain', 'application', 'presentation']) {
    for (const path of await files(join(root, layer))) {
      if (!/\.(js|vue)$/.test(path)) continue;
      const source = await readFile(path, 'utf8');
      const imports = [...source.matchAll(/(?:from\s*|import\s*\()(['"])([^'"]+)\1/g)].map((m) => m[2]);
      for (const specifier of imports) {
        const resolved = specifier.startsWith('.') ? join(dirname(path), specifier) : specifier;
        assert.ok(!resolved.includes('/infrastructure/'), `${layer} imports infrastructure: ${path}`);
        if (layer === 'domain') {
          assert.ok(!resolved.includes('/application/') && !resolved.includes('/presentation/'), path);
          assert.ok(!['vue', 'pinia', 'vue-router'].includes(specifier), path);
        }
        if (layer === 'application') assert.ok(!resolved.includes('/presentation/'), path);
      }
      assert.ok(!/\bfetch\s*\(/.test(source), `HTTP outside infrastructure: ${path}`);
      assert.ok(!/\blocalStorage\b/.test(source), `Storage outside infrastructure: ${path}`);
    }
  }
});

test('catalog and payments work with injected backend adapters', async () => {
  const calls = [];
  configureApplicationServices({
    http: {
      apiGet: async (...args) => { calls.push(['get', ...args]); return [{ id_pm: 1 }]; },
      apiPost: async (...args) => { calls.push(['post', ...args]); return { confirmed: true }; },
    },
    auth: {}, session: {}, attendance: {}, images: {}, config: {}, storage: {}, preferences: {}, repositories: {},
  });
  assert.deepEqual(await loadMembershipPlans(), [{ id_pm: 1 }]);
  assert.deepEqual(await confirmMembershipPayment('session/with?symbols', 'token'), { confirmed: true });
  assert.deepEqual(calls, [
    ['get', '/planes-membresia'],
    ['post', '/pagos/stripe/confirmar-retorno?session_id=session%2Fwith%3Fsymbols', {}, 'token'],
  ]);
});

test('users and settings accept data repositories without HTTP responses or a global adapter registry', async () => {
  const ctx = { apiBase: '/api', authStore: { token: 'session' }, users: ref([]), gymSettings: ref({}) };
  const users = createUsersModule(ctx, {
    save: async (payload, token) => {
      assert.equal(token, 'session');
      return { ...payload, id_usuario: 'SGUS001' };
    },
    remove: async (id, token) => {
      assert.equal(id, 'SGUS001');
      assert.equal(token, 'session');
      return true;
    },
  });
  const settings = createDashboardModule(ctx, {
    load: async (token) => {
      assert.equal(token, 'session');
      return { capacidad_total: 40, capacidad_por_hora: 12 };
    },
    save: async (payload, token) => {
      assert.equal(token, 'session');
      return payload;
    },
  });

  await users.upsertUser({ nombre: 'Ana' });
  assert.equal(ctx.users.value[0].nombre, 'Ana');
  await users.deleteUser('SGUS001');
  assert.deepEqual(ctx.users.value, []);
  assert.equal((await settings.refreshGymSettingsFromBackend()).capacidad_total, 40);
  assert.equal((await settings.updateGymSettings({ totalCapacity: 50 })).capacidad_total, 50);
});

test('local user edits keep the same identity and settings still support their local defaults', async () => {
  const ctx = { users: ref([]), gymSettings: ref({}) };
  const users = createUsersModule(ctx);
  const created = await users.upsertUser({ nombre: 'Ana', rol: 'trainer' });
  await users.upsertUser({ id_usuario: created.id_usuario, nombre: 'Ana Perez' });
  assert.equal(ctx.users.value.length, 1);
  assert.equal(ctx.users.value[0].id_usuario, 'SGUS001');
  assert.equal(ctx.users.value[0].nombre, 'Ana Perez');
  assert.equal(ctx.users.value[0].rol, 'trainer');
  await users.deleteUser(created.id_usuario);
  assert.deepEqual(ctx.users.value, []);

  const settings = createDashboardModule(ctx);
  assert.deepEqual(await settings.updateGymSettings(), { capacidad_total: 30, capacidad_por_hora: 10 });
});
