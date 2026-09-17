import assert from 'node:assert/strict';
import { after, before, beforeEach, test } from 'node:test';
import { createPinia } from 'pinia';
import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';

let server;
let useAuthStore;
let useGymStore;
let auth;
let gym;
const originals = { fetch: globalThis.fetch, window: globalThis.window, localStorage: globalThis.localStorage };
const profile = { id_usuario: 'ADMIN1', name: 'Admin Demo', email: 'admin@example.com', role: 'admin' };
const token = `test.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.test`;
const json = (value, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { 'content-type': 'application/json' },
});
const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};
const flush = () => new Promise((resolve) => setImmediate(resolve));

before(async () => {
  // Vite resuelve los imports del store sin abrir puertos ni conectar con la API.
  server = await createServer({
    root: fileURLToPath(new URL('..', import.meta.url)), configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  ({ useAuthStore } = await server.ssrLoadModule('/src/stores/authStore.js'));
  ({ useGymStore } = await server.ssrLoadModule('/src/stores/gymStore.js'));
});

beforeEach(() => {
  const values = new Map();
  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  };
  globalThis.window = {};
  globalThis.fetch = async () => { throw new Error('Unexpected network request'); };
  const pinia = createPinia();
  auth = useAuthStore(pinia);
  gym = useGymStore(pinia);
});

after(async () => {
  Object.assign(globalThis, originals);
  await server?.close();
});

test('store checks a restored session once and rejects locally expired tokens before using the cache', async () => {
  localStorage.setItem('gym_auth_token', token);
  let calls = 0;
  globalThis.fetch = async () => { calls++; return json(profile); };
  await Promise.all([auth.initializeAuth(), auth.initializeAuth()]);
  for (let index = 0; index < 5; index++) await auth.initializeAuth();
  assert.equal(calls, 1);
  assert.equal(auth.isAdmin, true);
  localStorage.setItem('gym_auth_token_expiry', Date.now() - 1);
  await auth.initializeAuth();
  assert.equal(auth.isAuthenticated, false);
  assert.equal(auth.token, null);
  assert.equal(calls, 1);
});

test('a pending validation cannot restore a signed-out session', async () => {
  localStorage.setItem('gym_auth_token', token);
  const response = deferred();
  globalThis.fetch = () => response.promise;
  const check = auth.initializeAuth();
  await flush();
  await auth.signOut();
  response.resolve(json(profile));
  await check;
  assert.equal(auth.isAuthenticated, false);
  assert.equal(localStorage.getItem('gym_auth_token'), null);
});

test('server rejection on revalidation clears the previously valid session', async () => {
  localStorage.setItem('gym_auth_token', token);
  globalThis.fetch = async () => json(profile);
  await auth.initializeAuth();
  globalThis.fetch = async () => json({ detail: 'Cuenta desactivada' }, 403);
  await auth.initializeAuth({ force: true });
  assert.equal(auth.isAuthenticated, false);
  assert.equal(auth.userRole, null);
  assert.equal(localStorage.getItem('gym_auth_token'), null);
});

test('section changes reuse synced data; refresh and a new session fetch it again', async () => {
  auth.token = token;
  auth.userRole = 'admin';
  let calls = 0;
  globalThis.fetch = async () => { calls++; return json([]); };
  await Promise.all([gym.fetchFromBackend(), gym.fetchFromBackend()]);
  const initialCalls = calls;
  assert.ok(initialCalls > 0);
  await gym.fetchFromBackend();
  assert.equal(calls, initialCalls);
  await gym.fetchFromBackend({ force: true });
  assert.equal(calls, initialCalls * 2);
  auth.token = 'another-session';
  await gym.fetchFromBackend();
  assert.equal(calls, initialCalls * 3);
});

test('synced data expires after thirty seconds', async (t) => {
  let now = 0;
  t.mock.method(Date, 'now', () => now);
  auth.token = token;
  auth.userRole = 'admin';
  let calls = 0;
  globalThis.fetch = async () => { calls++; return json([]); };
  await gym.fetchFromBackend();
  const firstCalls = calls;
  now = 29_999;
  await gym.fetchFromBackend();
  assert.equal(calls, firstCalls);
  now = 30_000;
  await gym.fetchFromBackend();
  assert.equal(calls, firstCalls * 2);
});

test('failed forced refresh is not cached and a later navigation retries it', async () => {
  auth.token = token;
  auth.userRole = 'admin';
  let fail = false;
  let clientRequests = 0;
  globalThis.fetch = async (url) => {
    if (url.endsWith('/clientes')) {
      clientRequests++;
      if (fail) return json({ detail: 'Sin conexión' }, 503);
    }
    return json([]);
  };
  await gym.fetchFromBackend();
  fail = true;
  await assert.rejects(gym.fetchFromBackend({ force: true }), /Sin conexión/);
  fail = false;
  await gym.fetchFromBackend();
  assert.equal(clientRequests, 3);
  assert.equal(gym.syncError, '');
});

test('attendance waits for client names and forced refresh runs after the pending sync', async () => {
  auth.token = token;
  auth.userRole = 'admin';
  const clients = deferred();
  let clientRequests = 0;
  let attendanceRequests = 0;
  globalThis.fetch = async (url) => {
    if (url.endsWith('/clientes')) {
      clientRequests++;
      if (clientRequests === 1) await clients.promise;
      return json([{ id_cliente: 1, nombre: 'Cliente Demo', correo: 'cliente@example.com' }]);
    }
    if (url.endsWith('/asistencia')) {
      attendanceRequests++;
      return json([{ id_asistencia: 1, id_cliente: 1, fecha: '2026-09-17', hora: '10:00' }]);
    }
    return json([]);
  };
  const initial = gym.fetchFromBackend();
  const forced = gym.fetchFromBackend({ force: true });
  await flush();
  assert.equal(attendanceRequests, 0);
  clients.resolve();
  await Promise.all([initial, forced]);
  assert.equal(clientRequests, 2);
  assert.equal(attendanceRequests, 2);
  assert.equal(gym.attendance[0].memberName, 'Cliente Demo');
});
