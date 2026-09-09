import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseError, parseResponse } from '../src/services/apiResponse.js';

test('gateway errors show a readable message instead of nginx HTML', async () => {
  for (const status of [502, 504]) {
    const error = await parseError(new Response('<html><h1>Gateway Time-out</h1></html>', {
      status, headers: { 'content-type': 'text/html' },
    }));
    assert.match(error.message, new RegExp(String(status)));
    assert.doesNotMatch(error.message, /<|nginx/);
  }
});

test('other HTML responses are not exposed even with an incorrect content type', async () => {
  for (const contentType of ['text/html', 'text/plain']) {
    const error = await parseError(new Response('<html>Server error</html>', {
      status: 500, headers: { 'content-type': contentType },
    }));
    assert.equal(error.message, 'Error HTTP 500');
  }
});

test('preserves API authentication and configuration errors', async () => {
  for (const status of [401, 503]) {
    const error = await parseError(new Response(JSON.stringify({ detail: 'Mensaje de la API' }), {
      status, headers: { 'content-type': 'application/json' },
    }));
    assert.equal(error.message, 'Mensaje de la API');
  }
});

test('handles malformed JSON and successful responses', async () => {
  const error = await parseError(new Response('{', {
    status: 500, headers: { 'content-type': 'application/json' },
  }));
  assert.equal(error.message, 'Error HTTP 500');
  assert.equal(await parseResponse(new Response(null, { status: 204 })), null);
  assert.deepEqual(await parseResponse(new Response('{"ok":true}', {
    headers: { 'content-type': 'application/json' },
  })), { ok: true });
});
