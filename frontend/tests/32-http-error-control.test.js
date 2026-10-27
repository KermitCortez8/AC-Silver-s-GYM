import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { fetchWithTimeout } from '../src/infrastructure/services/httpTransport.js';
import { parseError } from '../src/infrastructure/services/apiResponse.js';
import { dataRequest } from '../src/infrastructure/repositories/dataRequest.js';

let server, createApiClient, createAuthService, createStoreImageService;
before(async () => {
  server = await createServer({ root: fileURLToPath(new URL('..', import.meta.url)), configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  ({ createApiClient } = await server.ssrLoadModule('/src/infrastructure/services/apiClient.js'));
  ({ createAuthService } = await server.ssrLoadModule('/src/infrastructure/services/authService.js'));
  ({ createStoreImageService } = await server.ssrLoadModule('/src/infrastructure/services/storeImageService.js'));
});
after(async () => { await server?.close(); });

const json = (value, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { 'content-type': 'application/json' },
});

test('HTTP errors retain status and domain codes used by authentication', async () => {
  const error = await parseError(json({ detail: { code: 'membership_expired', message: 'Membresía vencida' } }, 403));
  assert.equal(error.status, 403);
  assert.equal(error.code, 'membership_expired');
  assert.equal(error.message, 'Membresía vencida');
});

test('network failures produce readable errors across JSON requests, repositories and images', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('Failed to fetch'); });
  const client = createApiClient({ authApiBaseUrl: '/api' });
  const images = createStoreImageService({ authApiBaseUrl: '/api' });
  for (const action of [
    () => client.apiGet('/clientes'),
    () => dataRequest(client, '/api/usuarios'),
    () => images.listStoreImages(),
    () => images.uploadStoreImage(new File(['image'], 'agua.png', { type: 'image/png' })),
  ]) {
    await assert.rejects(action(), error => error.code === 'network_error' && /conexión/.test(error.message));
  }
});

test('a timed-out write is never retried and warns that its outcome is unconfirmed', async (t) => {
  let calls = 0;
  t.mock.method(globalThis, 'fetch', (_url, options) => {
    calls++;
    return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('Aborted'))));
  });
  const client = createApiClient({ authApiBaseUrl: '/api', requestTimeoutMs: 5 });
  await assert.rejects(client.apiPost('/inventario', {}), error => {
    assert.equal(error.code, 'request_timeout');
    assert.equal(error.outcomeUnknown, true);
    assert.match(error.message, /antes de repetir/);
    return true;
  });
  assert.equal(calls, 1);
  await assert.rejects(dataRequest(client, '/api/inventario', { method: 'POST' }), error => error.code === 'request_timeout');
  assert.equal(calls, 2);
});

test('caller cancellation is kept distinct from a network failure', async (t) => {
  t.mock.method(globalThis, 'fetch', (_url, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('Aborted')));
  }));
  const controller = new AbortController();
  const pending = fetchWithTimeout('/api/clientes', { signal: controller.signal });
  controller.abort();
  await assert.rejects(pending, error => error.code === 'request_cancelled');
});

test('malformed successful JSON becomes a readable error instead of a parser exception', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('{', { headers: { 'content-type': 'application/json' } }));
  const client = createApiClient({ authApiBaseUrl: '/api' });
  await assert.rejects(client.apiGet('/planes-membresia'), /datos inválidos/);
  await assert.rejects(dataRequest(client, '/api/inventario'), /datos inválidos/);
});

test('password authentication rejects an incomplete session before returning credentials', async () => {
  for (const value of [null, {}, { token: 'token' }, { user: { email: 'ana@example.com' } }]) {
    const auth = createAuthService({ apiPost: async () => value });
    await assert.rejects(auth.authenticateWithPassword({ correo: 'ana@example.com', password: 'test' }), /sesión válida/);
  }
});

test('invalid image responses fail explicitly instead of pretending the gallery is empty', async (t) => {
  const images = createStoreImageService({ authApiBaseUrl: '/api' });
  for (const value of [null, {}, [null], [{ name: 'sin-url.png' }]]) {
    t.mock.method(globalThis, 'fetch', async () => json(value));
    await assert.rejects(images.listStoreImages(), /galería.*inválida/);
  }
  t.mock.method(globalThis, 'fetch', async () => json({}));
  await assert.rejects(images.uploadStoreImage(new File(['image'], 'agua.png', { type: 'image/png' })), /no confirmó/);
});
