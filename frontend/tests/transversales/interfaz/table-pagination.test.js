import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, h } from 'vue';
import { renderToString } from 'vue/server-renderer';
import {
  clampPage, parsePageSize, pageSizeStorageKey, readStoredPageSize, stepPageSize, storePageSize,
} from '../../../src/domain/utils/pagination.js';

let server;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('../../..', import.meta.url)), configFile: false, plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
});

after(async () => { await server?.close(); });

const renderPager = async (props, { route } = {}) => {
  const { default: TablePager } = await server.ssrLoadModule('/src/presentation/components/common/TablePager.vue');
  const events = [];
  let setup;
  const app = createSSRApp({ render: () => h(TablePager, {
    ...props,
    'onUpdate:page': (value) => events.push(['page', value]),
    'onUpdate:pageSize': (value) => events.push(['pageSize', value]),
  }) });
  if (route) app.config.globalProperties.$route = route;
  app.mixin({ created() { if (this.$.type === TablePager) setup = this.$.setupState; } });
  const html = await renderToString(app);
  return { html, setup, events };
};

const buttonOf = (html, label) => html.split('<button').find((chunk) => chunk.includes(label)) ?? '';

test('el tamaño de página acepta enteros de 1 a 100 y recorta lo que excede', () => {
  for (const [value, expected] of [[1, 1], ['1', 1], ['10', 10], ['007', 7], [100, 100], ['101', 100], ['500', 100]]) {
    assert.equal(parsePageSize(value), expected, String(value));
  }
});

test('el tamaño de página rechaza vacío, cero, negativos, decimales, texto y notación científica', () => {
  for (const value of ['', ' ', '0', 0, '-3', -3, '+5', '7.5', 7.5, 'abc', '1e2', '12abc', null, undefined, NaN, true]) {
    assert.equal(parsePageSize(value), null, String(value));
  }
});

test('las flechas del tamaño suben y bajan de uno en uno sin salir de 1 a 100', () => {
  assert.equal(stepPageSize(10, 1), 11);
  assert.equal(stepPageSize(10, -1), 9);
  assert.equal(stepPageSize(100, 1), 100);
  assert.equal(stepPageSize(1, -1), 1);
  assert.equal(stepPageSize(150, 1), 100);
  assert.equal(stepPageSize('abc', 1), 2);
});

test('la página se ajusta a una que exista cuando la lista se acorta', () => {
  assert.equal(clampPage(3, 6), 3);
  assert.equal(clampPage(7, 6), 6);
  for (const value of [0, -2, 'x', NaN]) assert.equal(clampPage(value, 6), 1, String(value));
  assert.equal(clampPage(5, 0), 1);
});

test('el control muestra el rango, el campo numérico y las flechas del tamaño', async () => {
  const { html } = await renderPager({ page: 1, pageSize: 10, total: 27, itemLabel: 'articulos' });
  assert.match(html, /Mostrando 1 a 10 de/);
  assert.match(html, />27<\/span>/);
  assert.match(html, /Filas por pagina/);
  assert.match(html, /inputmode="numeric"/);
  assert.match(html, /value="10"/);
  assert.match(html, /aria-label="Mostrar menos filas"/);
  assert.match(html, /aria-label="Mostrar más filas"/);
});

test('las flechas de página se desactivan en la primera y en la última página', async () => {
  const first = (await renderPager({ page: 1, pageSize: 10, total: 27 })).html;
  assert.match(buttonOf(first, 'Anterior'), /disabled/);
  assert.doesNotMatch(buttonOf(first, 'Siguiente'), /disabled/);
  const last = (await renderPager({ page: 3, pageSize: 10, total: 27 })).html;
  assert.match(last, /Mostrando 21 a 27 de/);
  assert.match(buttonOf(last, 'Siguiente'), /disabled/);
  assert.doesNotMatch(buttonOf(last, 'Anterior'), /disabled/);
});

test('sin registros no se muestra el control y con una sola página no hay flechas de página', async () => {
  assert.doesNotMatch((await renderPager({ page: 1, pageSize: 10, total: 0 })).html, /Mostrando/);
  const single = (await renderPager({ page: 1, pageSize: 10, total: 5 })).html;
  assert.match(single, /Mostrando 1 a 5 de/);
  assert.doesNotMatch(single, /Anterior/);
});

test('un tamaño mayor al total deja una sola página con todos los registros', async () => {
  const { html } = await renderPager({ page: 1, pageSize: 50, total: 27 });
  assert.match(html, /Mostrando 1 a 27 de/);
  assert.doesNotMatch(html, /Siguiente/);
});

test('las flechas del tamaño se desactivan en 1 y en 100', async () => {
  const min = (await renderPager({ page: 1, pageSize: 1, total: 30 })).html;
  assert.match(buttonOf(min, 'Mostrar menos filas'), /disabled/);
  assert.doesNotMatch(buttonOf(min, 'Mostrar más filas'), /disabled/);
  const max = (await renderPager({ page: 1, pageSize: 100, total: 300 })).html;
  assert.match(buttonOf(max, 'Mostrar más filas'), /disabled/);
  assert.doesNotMatch(buttonOf(max, 'Mostrar menos filas'), /disabled/);
  const mid = (await renderPager({ page: 1, pageSize: 10, total: 30 })).html;
  assert.doesNotMatch(buttonOf(mid, 'Mostrar menos filas'), /disabled/);
  assert.doesNotMatch(buttonOf(mid, 'Mostrar más filas'), /disabled/);
});

test('escribir un tamaño válido lo aplica y vuelve a la página 1', async () => {
  const { setup, events } = await renderPager({ page: 3, pageSize: 10, total: 27 });
  setup.onInput({ target: { value: '5' } });
  assert.deepEqual(events, [['pageSize', 5], ['page', 1]]);
  assert.equal(setup.draft, '5');
});

test('un tamaño mayor a 100 se recorta a 100', async () => {
  const { setup, events } = await renderPager({ page: 1, pageSize: 10, total: 500 });
  const target = { value: '500' };
  setup.onInput({ target });
  assert.deepEqual(events, [['pageSize', 100], ['page', 1]]);
  assert.equal(target.value, '100');
});

test('los valores inválidos no cambian el tamaño y conservan lo escrito antes', async () => {
  const { setup, events } = await renderPager({ page: 2, pageSize: 10, total: 27 });
  for (const value of ['0', 'abc', '7.5', '1e2', '-3', '+4']) {
    const target = { value };
    setup.onInput({ target });
    assert.equal(target.value, '10', value);
  }
  assert.deepEqual(events, []);
});

test('borrar el campo no cambia el tamaño y al salir se restaura el valor actual', async () => {
  const { setup, events } = await renderPager({ page: 1, pageSize: 10, total: 27 });
  setup.onInput({ target: { value: '' } });
  assert.equal(setup.draft, '');
  assert.deepEqual(events, []);
  setup.restoreDraft();
  assert.equal(setup.draft, '10');
});

test('escribir el mismo tamaño no emite cambios', async () => {
  const { setup, events } = await renderPager({ page: 2, pageSize: 10, total: 27 });
  setup.onInput({ target: { value: '10' } });
  assert.deepEqual(events, []);
});

test('las flechas del tamaño aplican el cambio y respetan los límites', async () => {
  const up = await renderPager({ page: 2, pageSize: 10, total: 27 });
  up.setup.stepSize(1);
  assert.deepEqual(up.events, [['pageSize', 11], ['page', 1]]);
  assert.equal(up.setup.draft, '11');
  const max = await renderPager({ page: 1, pageSize: 100, total: 300 });
  max.setup.stepSize(1);
  assert.deepEqual(max.events, []);
  const min = await renderPager({ page: 1, pageSize: 1, total: 30 });
  min.setup.stepSize(-1);
  assert.deepEqual(min.events, []);
});

test('ninguna vista usa el prop sizes que se retiró del paginador', () => {
  const root = fileURLToPath(new URL('../../../src', import.meta.url));
  const offenders = [];
  for (const file of readdirSync(root, { recursive: true })) {
    if (!String(file).endsWith('.vue')) continue;
    const source = readFileSync(join(root, String(file)), 'utf8');
    for (const tag of source.match(/<TablePager\b[^>]*>/g) ?? []) {
      if (/\s:?sizes\b/.test(tag)) offenders.push(String(file));
    }
  }
  assert.deepEqual(offenders, []);
});

const fakeStorage = (initial = {}) => {
  const data = { ...initial };
  return { data, getItem: (k) => (k in data ? data[k] : null), setItem: (k, v) => { data[k] = String(v); } };
};
const INVENTORY = pageSizeStorageKey('inventory');
const STORE = pageSizeStorageKey('store');

test('cada tabla tiene su propia clave de almacenamiento', () => {
  assert.notEqual(INVENTORY, STORE);
});

test('el tamaño guardado se lee solo si es válido y no falla si el almacenamiento falla', () => {
  assert.equal(readStoredPageSize(fakeStorage({ [INVENTORY]: '20' }), INVENTORY), 20);
  assert.equal(readStoredPageSize(fakeStorage({ [INVENTORY]: '500' }), INVENTORY), 100);
  for (const bad of ['', 'abc', '0', '7.5']) {
    assert.equal(readStoredPageSize(fakeStorage({ [INVENTORY]: bad }), INVENTORY), null, bad);
  }
  assert.equal(readStoredPageSize(fakeStorage(), INVENTORY), null);
  assert.equal(readStoredPageSize(null, INVENTORY), null);
  assert.equal(readStoredPageSize(fakeStorage({ [INVENTORY]: '20' }), ''), null);
  assert.equal(readStoredPageSize({ getItem: () => { throw new Error('bloqueado'); } }, INVENTORY), null);
});

test('guardar el tamaño no falla si falta la clave o el almacenamiento no está disponible', () => {
  const storage = fakeStorage();
  storePageSize(storage, 20, INVENTORY);
  assert.equal(storage.data[INVENTORY], '20');
  storePageSize(storage, 30, '');
  assert.deepEqual(Object.keys(storage.data), [INVENTORY]);
  assert.doesNotThrow(() => storePageSize(null, 20, INVENTORY));
  assert.doesNotThrow(() => storePageSize({ setItem: () => { throw new Error('lleno'); } }, 20, INVENTORY));
});

const withStorage = async (storage, run) => {
  Object.defineProperty(globalThis, 'localStorage', { value: storage, configurable: true, writable: true });
  try { await run(); } finally { delete globalThis.localStorage; }
};

test('elegir un tamaño lo guarda y al recargar se recupera', async () => {
  const storage = fakeStorage();
  await withStorage(storage, async () => {
    const first = await renderPager({ page: 1, pageSize: 8, total: 29, storageKey: INVENTORY });
    first.setup.onInput({ target: { value: '20' } });
    assert.equal(storage.data[INVENTORY], '20');
    const reloaded = await renderPager({ page: 1, pageSize: 8, total: 29, storageKey: INVENTORY });
    reloaded.setup.applySavedSize();
    assert.deepEqual(reloaded.events, [['pageSize', 20], ['page', 1]]);
  });
});

test('inventario y tienda recuerdan su tamaño de forma independiente', async () => {
  const storage = fakeStorage();
  await withStorage(storage, async () => {
    const inventory = await renderPager({ page: 1, pageSize: 8, total: 29, storageKey: INVENTORY });
    inventory.setup.onInput({ target: { value: '15' } });
    const store = await renderPager({ page: 1, pageSize: 8, total: 20, storageKey: STORE });
    store.setup.onInput({ target: { value: '13' } });
    assert.deepEqual(storage.data, { [INVENTORY]: '15', [STORE]: '13' });
    const inventoryAgain = await renderPager({ page: 1, pageSize: 8, total: 29, storageKey: INVENTORY });
    inventoryAgain.setup.applySavedSize();
    assert.deepEqual(inventoryAgain.events, [['pageSize', 15], ['page', 1]]);
    const storeAgain = await renderPager({ page: 1, pageSize: 8, total: 20, storageKey: STORE });
    storeAgain.setup.applySavedSize();
    assert.deepEqual(storeAgain.events, [['pageSize', 13], ['page', 1]]);
  });
});

test('sin storageKey no se guarda ni se lee nada', async () => {
  const storage = fakeStorage({ [INVENTORY]: '20' });
  await withStorage(storage, async () => {
    const { setup, events } = await renderPager({ page: 1, pageSize: 8, total: 29 });
    setup.applySavedSize();
    assert.deepEqual(events, []);
    setup.onInput({ target: { value: '12' } });
    assert.deepEqual(storage.data, { [INVENTORY]: '20' });
  });
});

test('un valor guardado inválido o igual al actual no emite cambios', async () => {
  for (const saved of ['abc', '8']) {
    await withStorage(fakeStorage({ [INVENTORY]: saved }), async () => {
      const { setup, events } = await renderPager({ page: 1, pageSize: 8, total: 29, storageKey: INVENTORY });
      setup.applySavedSize();
      assert.deepEqual(events, [], saved);
    });
  }
});

test('sin storageKey cada tabla usa la clave de su ruta y no se mezclan', async () => {
  const storage = fakeStorage();
  await withStorage(storage, async () => {
    const inventory = await renderPager({ page: 1, pageSize: 8, total: 29 }, { route: { path: '/admin/inventory' } });
    inventory.setup.onInput({ target: { value: '15' } });
    const store = await renderPager({ page: 1, pageSize: 8, total: 20 }, { route: { path: '/admin/store' } });
    store.setup.onInput({ target: { value: '13' } });
    assert.deepEqual(storage.data, {
      [pageSizeStorageKey('/admin/inventory')]: '15',
      [pageSizeStorageKey('/admin/store')]: '13',
    });
    const again = await renderPager({ page: 1, pageSize: 8, total: 29 }, { route: { path: '/admin/inventory' } });
    again.setup.applySavedSize();
    assert.deepEqual(again.events, [['pageSize', 15], ['page', 1]]);
  });
});