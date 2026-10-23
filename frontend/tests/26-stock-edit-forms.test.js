import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, h } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';

let server;
let useGymStore;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('..', import.meta.url)), configFile: false, plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  await server.ssrLoadModule('/src/bootstrap.js');
  ({ useGymStore } = await server.ssrLoadModule('/src/application/stores/gymStore.js'));
});

after(async () => { await server?.close(); });

const setupView = async (filename, path) => {
  const { default: View } = await server.ssrLoadModule(`/src/presentation/views/${filename}.vue`);
  const pinia = createPinia();
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path, component: View }] });
  await router.push(path);
  let setup;
  const app = createSSRApp({ render: () => h(View) });
  app.use(pinia);
  app.use(router);
  app.mixin({ created() { if (this.$.type === View) setup = this.$.setupState; } });
  await renderToString(app);
  assert.ok(setup, 'Se debe ejecutar el setup real de la vista');
  return { setup, gym: useGymStore(pinia) };
};

test('editing a store product preserves a zero threshold through the actual view and save payload', async () => {
  const { setup, gym } = await setupView('StoreView', '/admin/store');
  const product = { id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 1, minimo: 0, estado: 'Disponible' };
  setup.editProducto(product);
  assert.equal(setup.form.minimo, 0);
  assert.equal(setup.stockBarColor(product), 'bg-emerald-400');
  setup.editProducto({ ...product, minimo: undefined });
  assert.equal(setup.form.minimo, 5);
  setup.editProducto(product);
  let payload;
  gym.upsertProductoTienda = async (value) => { payload = { ...value }; };
  await setup.handleSubmit();
  assert.equal(payload.minimo, 0);
  assert.equal(setup.feedbackTone, 'success');
});

test('editing inventory preserves a zero threshold and uses one only when the value is absent', async () => {
  const { setup, gym } = await setupView('InventoryView', '/admin/inventory');
  const item = { id: 'item-1', name: 'Pesas', category: 'Equipo', quantity: 1, minQuantity: 0, status: 'Operativo' };
  setup.editItem(item);
  assert.equal(setup.form.minQuantity, 0);
  assert.equal(setup.stockBarPercent(item), 100);
  setup.editItem({ ...item, minQuantity: undefined });
  assert.equal(setup.form.minQuantity, 1);
  setup.editItem(item);
  let payload;
  gym.upsertInventoryItem = async (value) => { payload = { ...value }; };
  await setup.handleSubmit();
  assert.equal(payload.minQuantity, 0);
  assert.equal(setup.feedbackTone, 'success');
});
