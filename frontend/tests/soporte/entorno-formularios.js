import assert from 'node:assert/strict';
import { before, after } from 'node:test';
import { crearServidorSsr } from './servidor-ssr.js';
import { createSSRApp, h } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';

let server;

let useGymStore;

let installServices;

before(async () => {
  server = await crearServidorSsr({ componentesVue: true });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useGymStore } = await server.ssrLoadModule('/src/application/stores/gymStore.js'));
});

after(async () => { await server?.close(); });

const setupView = async (filename, path, prepare, query = {}) => {
  const { default: View } = await server.ssrLoadModule(`/src/presentation/views/${filename}.vue`);
  const pinia = createPinia();
  installServices(pinia, { http: { apiGet: async (path) => path === '/planes-membresia'
    ? [{ id_pm: 1, nombre_plan: 'MENSUAL', duracion: '30 días', precio: 79, activo: true }] : [] } });
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path, component: View },
    { path: '/inventory', name: 'Inventory', component: { render: () => null } },
  ] });
  await router.push({ path, query });
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
  const html = await renderToString(app, context);
  assert.ok(setup, 'Se debe ejecutar el setup real de la vista');
  return { setup, gym: useGymStore(pinia), html, dialogs: Object.values(context.teleports || {}).join('') };
};

// Monta un componente de presentation/components con sus props; prepare recibe su setup y el store
// antes del render, para dejar datos listos.
const setupComponent = async (filename, props = {}, prepare) => {
  const { default: Component } = await server.ssrLoadModule(`/src/presentation/components/${filename}.vue`);
  const pinia = createPinia();
  installServices(pinia, { http: { apiGet: async () => [] } });
  let setup;
  const app = createSSRApp({ render: () => h(Component, props) });
  app.use(pinia);
  app.use(createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { render: () => null } }] }));
  app.mixin({ created() {
    if (this.$.type === Component) {
      setup = this.$.setupState;
      prepare?.(setup, useGymStore(pinia));
    }
  } });
  const html = await renderToString(app);
  assert.ok(setup, 'Se debe ejecutar el setup real del componente');
  return { setup, gym: useGymStore(pinia), html };
};

export { setupComponent, setupView };
