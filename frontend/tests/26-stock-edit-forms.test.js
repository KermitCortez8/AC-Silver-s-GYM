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
let installServices;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('..', import.meta.url)), configFile: false, plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useGymStore } = await server.ssrLoadModule('/src/application/stores/gymStore.js'));
});

after(async () => { await server?.close(); });

const setupView = async (filename, path, prepare) => {
  const { default: View } = await server.ssrLoadModule(`/src/presentation/views/${filename}.vue`);
  const pinia = createPinia();
  installServices(pinia);
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path, component: View }] });
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
  const context = {};
  await renderToString(app, context);
  assert.ok(setup, 'Se debe ejecutar el setup real de la vista');
  return { setup, gym: useGymStore(pinia), dialogs: Object.values(context.teleports || {}).join('') };
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

test('client editor and membership actions preserve the actual view flow after extraction', async () => {
  const { setup, gym } = await setupView('ClientsView', '/admin/clients');
  const client = { id: 'SGCLI001', id_cliente: 1, name: 'Ana', email: 'ana@example.com', status: 'EN_TRAMITE', paymentStatus: 'PAGADO' };
  gym.members = [client];
  setup.editClient(client);
  setup.form.nombre = 'Ana editada';
  let submitted;
  gym.upsertClient = async payload => { submitted = payload; return { ...client, name: payload.nombre }; };
  await setup.handleSubmit();
  assert.equal(submitted.nombre, 'Ana editada');
  assert.equal(submitted.id_usuario, 'SGCLI001');
  assert.equal(setup.isEditorOpen, false);
  assert.equal(setup.feedbackTone, 'success');
  setup.requestActivation(client);
  gym.activateClientMembership = async () => { throw new Error('No hay conexión'); };
  await setup.activateMembership(client);
  assert.equal(setup.pendingActivation.id, client.id);
  assert.equal(setup.activationError, 'No hay conexión');
  assert.equal(setup.activatingClientId, '');
  gym.activateClientMembership = async () => ({ ...client, notification: { status: 'queued' } });
  await setup.activateMembership(client);
  assert.equal(setup.pendingActivation, null);
  assert.match(setup.feedbackMessage, /pendiente de envío/);
});

test('a failed product save preserves the editor and its entered values', async () => {
  const { setup, gym } = await setupView('StoreView', '/admin/store');
  setup.openNewProducto();
  setup.form.nombre = 'Agua';
  setup.form.precio = 3;
  gym.upsertProductoTienda = async () => { throw new Error('No se pudo guardar'); };
  await setup.handleSubmit();
  assert.equal(setup.isProductEditorOpen, true);
  assert.equal(setup.form.nombre, 'Agua');
  assert.equal(setup.isSaving, false);
  assert.equal(setup.feedbackTone, 'error');
});

test('extracted client dialogs render their real form and membership details', async () => {
  const { dialogs } = await setupView('ClientsView', '/admin/clients', (setup, gym) => {
    const client = { id: 'SGCLI001', id_cliente: 1, name: 'Ana editada', email: 'ana@example.com', plan: 'MENSUAL', status: 'EN_TRAMITE', paymentStatus: 'PAGADO' };
    gym.members = [client];
    setup.editClient(client);
    setup.openDetails(client);
  });
  assert.match(dialogs, /Ana editada/);
  assert.match(dialogs, /ana@example.com/);
  assert.match(dialogs, /Guardar cambios/);
  assert.match(dialogs, /Activar Membresía/);
});

test('extracted product dialog renders linked inventory and the image picker', async () => {
  const { dialogs } = await setupView('StoreView', '/admin/store', (setup, gym) => {
    gym.inventory = [{ id: 'item-1', name: 'Almacén Agua', inventoryCode: 'ACT-0001', category: 'Tienda' }];
    const product = { id_producto: 1, id_item: 1, nombre: 'Agua editada', precio: 3, cantidad: 4, minimo: 0, estado: 'Disponible' };
    gym.productos_tienda = [product];
    setup.editProducto(product);
    setup.isBucketPickerOpen = true;
    setup.bucketImages = [{ name: 'agua.png', url: '/agua.png' }];
  });
  assert.match(dialogs, /Agua editada/);
  assert.match(dialogs, /Almacén Agua/);
  assert.match(dialogs, /agua.png/);
  assert.match(dialogs, /Guardar cambios/);
});
