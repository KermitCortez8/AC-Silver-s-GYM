import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, h } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
let server, installServices, View;
before(async () => {
  server = await createServer({ root: fileURLToPath(new URL('..', import.meta.url)), configFile: false,
    plugins: [vue()], server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ default: View } = await server.ssrLoadModule('/src/presentation/views/MembershipRenewalView.vue'));
});
after(async () => { await server?.close(); });
const summary = { plan: 'Mensual', duracion: '30 días', fecha_fin: '2026-11-10', monto_pago: 120, renovada: false };
async function view(apiGet, apiPost = async () => ({}), hash = '#token=personal') {
  const pinia = createPinia(); setActivePinia(pinia); installServices(pinia, { http: { apiGet, apiPost } });
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/renovar-membresia', component: View }] });
  await router.push(`/renovar-membresia${hash}`);
  let setup, instance;
  const app = createSSRApp({ render: () => h(View) }); app.use(pinia).use(router);
  app.mixin({ created() { if (this.$.type === View) { setup = this.$.setupState; instance = this.$; } } });
  await renderToString(app);
  return { setup, router, dispose: () => instance.scope.stop() };
}
test('revisa detalles sin iniciar pago y exige enlace personal', async () => {
  let gets = 0, posts = 0;
  const mounted = await view(async () => { gets++; return summary; }, async () => { posts++; });
  await mounted.setup.load();
  assert.equal(mounted.setup.details.monto_pago, 120);
  assert.equal(posts, 0); assert.ok(gets > 0);
  await mounted.router.push('/renovar-membresia');
  await mounted.setup.load();
  assert.match(mounted.setup.error, /incompleto/);
  assert.equal(mounted.setup.details, null);
  mounted.dispose();
});
test('un precio desactualizado muestra error y permite recargar sin redirigir', async () => {
  const mounted = await view(async () => summary, async (_path, payload) => {
    assert.equal(payload.token, 'personal'); assert.equal(payload.monto_pago, 120);
    throw new Error('El precio cambió. Actualiza los detalles antes de continuar.');
  });
  await mounted.setup.load(); await mounted.setup.pay();
  assert.match(mounted.setup.error, /precio cambió/);
  assert.equal(mounted.setup.paying, false);
  await mounted.setup.load(); assert.equal(mounted.setup.error, '');
  mounted.dispose();
});
test('una renovación pagada bloquea el botón de compra', async () => {
  let posts = 0;
  const mounted = await view(async () => ({ ...summary, renovada: true }), async () => { posts++; });
  await mounted.setup.load(); await mounted.setup.pay();
  assert.equal(posts, 0); mounted.dispose();
});
test('cambiar de enlace descarta los detalles anteriores', async () => {
  let resolve;
  const mounted = await view(() => new Promise(done => { resolve = done; }));
  const first = mounted.setup.load();
  const finish = resolve;
  await mounted.router.push('/renovar-membresia');
  await mounted.setup.load();
  finish(summary); await first;
  assert.equal(mounted.setup.details, null);
  assert.match(mounted.setup.error, /incompleto/); mounted.dispose();
});
