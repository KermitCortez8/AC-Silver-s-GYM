import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, h } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import { DEFAULT_PAGE_SIZE } from '../../../src/domain/utils/inputRules.js';
import { parsePageSize } from '../../../src/domain/utils/pagination.js';

let server;
let useGymStore;
let installServices;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('../../..', import.meta.url)), configFile: false, plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useGymStore } = await server.ssrLoadModule('/src/application/stores/gymStore.js'));
});

after(async () => { await server?.close(); });

const setupView = async (filename, path, prepare) => {
  const { default: View } = await server.ssrLoadModule(`/src/presentation/views/${filename}.vue`);
  const pinia = createPinia();
  installServices(pinia, { http: { apiGet: async () => [] } });
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path, component: View },
    { path: '/inventory', name: 'Inventory', component: { render: () => null } },
  ] });
  await router.push(path);
  let setup;
  const app = createSSRApp({ render: () => h(View) });
  app.use(pinia);
  app.use(router);
  app.mixin({ created() {
    if (this.$.type === View) {
      setup = this.$.setupState;
      prepare?.(setup, useGymStore(pinia));
    }
  } });
  const html = await renderToString(app);
  assert.ok(setup, 'Se debe ejecutar el setup real de la vista');
  return { setup, gym: useGymStore(pinia), html };
};

const inventoryItems = (count) => Array.from({ length: count }, (_, index) => ({
  id: `item-${index + 1}`, name: `Artículo ${index + 1}`, inventoryCode: `ACT-${String(index + 1).padStart(4, '0')}`,
  category: 'Tienda', location: 'Almacén', quantity: 10, minQuantity: 1, status: 'Operativo',
}));

const storeProducts = (count) => Array.from({ length: count }, (_, index) => ({
  id_producto: index + 1, nombre: `Producto ${index + 1}`, precio: 5, cantidad: 10, minimo: 1, estado: 'Disponible',
}));

test('el tamaño de página por defecto de las tablas es un valor permitido', async () => {
  const inventory = await setupView('InventoryView', '/admin/inventory');
  const store = await setupView('StoreView', '/admin/store');
  assert.equal(parsePageSize(DEFAULT_PAGE_SIZE), DEFAULT_PAGE_SIZE);
  assert.equal(inventory.setup.porPagina, DEFAULT_PAGE_SIZE);
  assert.equal(store.setup.porPagina, DEFAULT_PAGE_SIZE);
});

test('inventario muestra solo las filas escritas y la última página trae el resto', async () => {
  const { setup, gym } = await setupView('InventoryView', '/admin/inventory');
  gym.inventory = inventoryItems(27);
  setup.porPagina = 5;
  assert.equal(setup.inventoryPaginado.length, 5);
  assert.equal(setup.totalPages, 6);
  setup.paginaActual = 6;
  assert.equal(setup.inventoryPaginado.length, 2);
});

test('tienda muestra solo las filas escritas y la última página trae el resto', async () => {
  const { setup, gym } = await setupView('StoreView', '/admin/store');
  gym.productos_tienda = storeProducts(27);
  setup.porPagina = 5;
  assert.equal(setup.productosPaginados.length, 5);
  setup.paginaActual = 6;
  assert.equal(setup.productosPaginados.length, 2);
});

test('ambas vistas renderizan el paginador con el campo de filas por página', async () => {
  const inventory = await setupView('InventoryView', '/admin/inventory', (_setup, gym) => { gym.inventory = inventoryItems(27); });
  const store = await setupView('StoreView', '/admin/store', (_setup, gym) => { gym.productos_tienda = storeProducts(27); });
  for (const { html } of [inventory, store]) {
    assert.match(html, /Filas por pagina/);
    assert.match(html, /aria-label="Mostrar más filas"/);
    assert.match(html, /Mostrando 1 a/);
  }
});