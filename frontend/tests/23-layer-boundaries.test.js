import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
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
    auth: {}, session: {}, attendance: {}, images: {}, config: {}, storage: {}, preferences: {},
  });
  assert.deepEqual(await loadMembershipPlans(), [{ id_pm: 1 }]);
  assert.deepEqual(await confirmMembershipPayment('session/with?symbols', 'token'), { confirmed: true });
  assert.deepEqual(calls, [
    ['get', '/planes-membresia'],
    ['post', '/pagos/stripe/confirmar-retorno?session_id=session%2Fwith%3Fsymbols', {}, 'token'],
  ]);
});
