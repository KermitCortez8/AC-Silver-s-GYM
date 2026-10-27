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

// Headers arrive immediately, but the body stalls. Model fetch's abort behavior;
// the fallback completes the body so a broken timeout fails instead of hanging CI.
const stalledBody = (t, status = 200) => {
  let calls = 0;
  let aborted = false;
  t.mock.method(globalThis, 'fetch', async (_url, { signal }) => {
    calls++;
    const body = new ReadableStream({
      start(controller) {
        const fallback = setTimeout(() => {
          signal.removeEventListener('abort', abort);
          controller.enqueue(new TextEncoder().encode('{}'));
          controller.close();
        }, 100);
        const abort = () => {
          aborted = true;
          clearTimeout(fallback);
          controller.error(new DOMException('Aborted', 'AbortError'));
        };
        signal.addEventListener('abort', abort, { once: true });
      },
    });
    return new Response(body, { status, headers: { 'content-type': 'application/json' } });
  });
  return { calls: () => calls, aborted: () => aborted };
};

for (const kind of ['JSON API', 'repository', 'image gallery', 'image upload']) {
  test(`${kind}: timeout also covers a stalled response body`, async (t) => {
    const transport = stalledBody(t);
    const config = { authApiBaseUrl: '/api', requestTimeoutMs: 10 };
    const client = createApiClient(config);
    const images = createStoreImageService(config);
    const actions = {
      'JSON API': () => client.apiGet('/clientes'),
      repository: () => dataRequest(client, '/api/clientes'),
      'image gallery': () => images.listStoreImages(),
      'image upload': () => images.uploadStoreImage(new File(['image'], 'agua.png', { type: 'image/png' })),
    };
    await assert.rejects(actions[kind](), error => error.code === 'request_timeout');
    assert.equal(transport.aborted(), true);
    assert.equal(transport.calls(), 1);
  });
}

test('a write with stalled confirmation keeps the uncertain outcome and is not retried', async (t) => {
  const transport = stalledBody(t);
  const client = createApiClient({ authApiBaseUrl: '/api', requestTimeoutMs: 10 });
  await assert.rejects(client.apiPost('/inventario', {}), error => {
    assert.equal(error.code, 'request_timeout');
    assert.equal(error.outcomeUnknown, true);
    assert.match(error.message, /antes de repetir/);
    return true;
  });
  assert.equal(transport.calls(), 1);
});

test('a stalled HTTP error body is also bounded by the timeout', async (t) => {
  stalledBody(t, 503);
  const client = createApiClient({ authApiBaseUrl: '/api', requestTimeoutMs: 10 });
  await assert.rejects(client.apiGet('/clientes'), error => error.code === 'request_timeout');
});

test('caller cancellation after headers still cancels the response body', async (t) => {
  const transport = stalledBody(t);
  const controller = new AbortController();
  const pending = fetchWithTimeout('/api/clientes', { signal: controller.signal }, 1000)
    .then(response => response.json());
  const rejection = assert.rejects(pending, error => error.code === 'request_cancelled');
  await new Promise(resolve => setTimeout(resolve, 0));
  controller.abort();
  await rejection;
  assert.equal(transport.aborted(), true);
});

test('complete responses preserve status, headers, metadata and readable content', async (t) => {
  let signal;
  t.mock.method(globalThis, 'fetch', async (_url, options) => {
    signal = options.signal;
    return Object.defineProperties(json({ saved: true }, 201), {
      url: { value: 'https://api.example.com/clientes' },
      redirected: { value: true },
      type: { value: 'cors' },
    });
  });
  const response = await fetchWithTimeout('/api/clientes', {}, 10);
  assert.equal(response.status, 201);
  assert.equal(response.headers.get('content-type'), 'application/json');
  assert.equal(response.url, 'https://api.example.com/clientes');
  assert.equal(response.redirected, true);
  assert.equal(response.type, 'cors');
  assert.equal(response.bodyUsed, false);
  assert.deepEqual(await response.json(), { saved: true });
  await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(signal.aborted, false);
});

test('empty 204 responses remain readable by the API and repositories', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(null, { status: 204 }));
  const client = createApiClient({ authApiBaseUrl: '/api' });
  assert.equal(await client.apiDelete('/clientes/1'), null);
  assert.equal(await dataRequest(client, '/api/clientes/1', { method: 'DELETE' }), null);
});
