import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, h, ref } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
let server, installServices, useClientMembershipActions;
before(async () => {
  server = await createServer({ root: fileURLToPath(new URL('..', import.meta.url)), configFile: false,
    plugins: [vue()], server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useClientMembershipActions } = await server.ssrLoadModule('/src/presentation/composables/clients/useClientMembershipActions.js'));
});
after(async () => { await server?.close(); });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
const services = (apiPost = async () => ({})) => {
  const pinia = createPinia(); setActivePinia(pinia); installServices(pinia, { http: { apiPost } }); return pinia;
};
const paymentView = async (apiPost, query = '?result=success&session_id=cs_test', requestId = '1') => {
  const { default: View } = await server.ssrLoadModule('/src/presentation/views/PaymentView.vue');
  const pinia = services(apiPost);
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/registro/pago/:idCliente', component: View }] });
  await router.push(`/registro/pago/${requestId}${query}`);
  let setup, instance;
  const app = createSSRApp({ render: () => h(View) }); app.use(pinia).use(router);
  app.mixin({ created() { if (this.$.type === View) { setup = this.$.setupState; instance = this.$; } } });
  await renderToString(app);
  return { setup, router, dispose: () => instance.scope.stop() };
};
test('error de verificación termina la carga y permite reintentar la misma sesión', async () => {
  const paths = [];
  const view = await paymentView(async path => { paths.push(path); if (paths.length === 1) throw new Error('Sin conexión'); return { confirmed: true, id_cliente: 1 }; });
  await view.setup.confirmPaidCheckout();
  assert.equal(view.setup.confirmationState, 'error');
  assert.equal(view.setup.resultStyle.title, 'No se pudo verificar el pago');
  assert.equal(view.setup.canRetryConfirmation, true);
  await view.setup.confirmPaidCheckout();
  assert.equal(view.setup.confirmationState, 'confirmed'); assert.equal(view.setup.confirmationError, '');
  assert.equal(view.setup.canRetryConfirmation, false); assert.equal(paths[0], paths[1]);
  assert.match(paths[0], /confirmar-retorno/); view.dispose();
});
test('el pago pendiente se distingue de la carga y permite volver a consultar', async () => {
  const view = await paymentView(async () => ({ confirmed: false }), '?result=pending&session_id=cs_test');
  await view.setup.confirmPaidCheckout();
  assert.equal(view.setup.confirmationState, 'pending'); assert.equal(view.setup.resultStyle.title, 'Pago pendiente de confirmación');
  assert.equal(view.setup.canRetryConfirmation, true); view.dispose();
});
test('no muestra confirmado el pago de otro cliente', async () => {
  const view = await paymentView(async () => ({ confirmed: true, id_cliente: 2 }));
  await view.setup.confirmPaidCheckout(); assert.equal(view.setup.confirmationState, 'error');
  assert.match(view.setup.confirmationError, /no corresponde/); view.dispose();
});
test('retorno de preregistro usa su token y muestra el cliente solo después de confirmar', async () => {
  const token = '12345678-1234-4234-8234-123456789abc';
  const view = await paymentView(async () => ({ confirmed: true, id_cliente: 42, preregistration_token: token }),
    '?result=success&session_id=cs_test', `p-${token}`);
  assert.equal(view.setup.requestLabel, 'Solicitud 12345678');
  await view.setup.confirmPaidCheckout();
  assert.equal(view.setup.confirmationState, 'confirmed');
  assert.equal(view.setup.requestLabel, 'SGCLI042');
  view.dispose();
});
test('retorno de preregistro rechaza el token de otra solicitud', async () => {
  const view = await paymentView(async () => ({ confirmed: true, id_cliente: 42, preregistration_token: 'ajeno' }),
    '?result=success&session_id=cs_test', 'p-12345678-1234-4234-8234-123456789abc');
  await view.setup.confirmPaidCheckout();
  assert.equal(view.setup.confirmationState, 'error');
  assert.match(view.setup.confirmationError, /no corresponde/);
  view.dispose();
});
test('solo permite una verificación en curso', async () => {
  const pending = deferred(); let calls = 0;
  const view = await paymentView(() => { calls++; return pending.promise; });
  const first = view.setup.confirmPaidCheckout(); await view.setup.confirmPaidCheckout(); assert.equal(calls, 1);
  pending.resolve({ confirmed: true, id_cliente: 1 }); await first;
  assert.equal(view.setup.confirmationState, 'confirmed'); view.dispose();
});
test('descarta respuesta de una ruta anterior', async () => {
  const pending = deferred(); const view = await paymentView(() => pending.promise);
  const first = view.setup.confirmPaidCheckout(); await view.router.push('/registro/pago/2?result=failure');
  pending.resolve({ confirmed: true, id_cliente: 1 }); await first;
  assert.notEqual(view.setup.confirmationState, 'confirmed'); view.dispose();
});
test('enlace sin sesión falla sin consultar el backend', async () => {
  let calls = 0; const view = await paymentView(() => { calls++; }, '?result=success');
  await view.setup.confirmPaidCheckout(); assert.equal(calls, 0); assert.equal(view.setup.confirmationState, 'error');
  assert.equal(view.setup.canRetryConfirmation, false); view.dispose();
});
const client = { id: 'SGCLI001', id_cliente: 1, name: 'Cliente', paymentStatus: 'PENDIENTE' };
const actions = gymStore => {
  services(); const ctx = { gymStore, authStore: { token: 'token-sintetico' }, feedbackMessage: ref(''), feedbackTone: ref(''),
    viewingClient: ref({ ...client }), route: { query: {} }, router: {}, refreshClients: async () => {} };
  return { ...ctx, ...useClientMembershipActions(ctx) };
};
test('pago manual bloquea clics repetidos y publica la ficha guardada', async () => {
  const previousWindow = globalThis.window; globalThis.window = { confirm: () => true };
  try {
    let calls = 0; const pending = deferred(); const state = actions({ confirmarPagoEfectivo: () => { calls++; return pending.promise; } });
    const first = state.markAsPaidManual(client); assert.equal(state.confirmingPaymentClientId.value, client.id);
    await state.markAsPaidManual(client); assert.equal(calls, 1);
    pending.resolve({ ...client, paymentStatus: 'PAGADO' }); await first;
    assert.equal(state.confirmingPaymentClientId.value, ''); assert.equal(state.viewingClient.value.paymentStatus, 'PAGADO');
  } finally { globalThis.window = previousWindow; }
});
test('pago manual fallido libera el botón y conserva la ficha pendiente', async () => {
  const previousWindow = globalThis.window; globalThis.window = { confirm: () => true };
  try {
    const state = actions({ confirmarPagoEfectivo: async () => { throw new Error('Sin conexión'); } }); await state.markAsPaidManual(client);
    assert.equal(state.confirmingPaymentClientId.value, ''); assert.equal(state.viewingClient.value.paymentStatus, 'PENDIENTE');
    assert.equal(state.feedbackTone.value, 'error');
  } finally { globalThis.window = previousWindow; }
});
test('activar sincroniza los detalles y cierra la confirmación', async () => {
  const state = actions({ activateClientMembership: async () => ({ ...client, paymentStatus: 'PAGADO', membershipStatus: 'ACTIVO',
    status: 'ACTIVO', notification: { status: 'queued' } }) });
  state.requestActivation(client); await state.activateMembership(client);
  assert.equal(state.viewingClient.value.membershipStatus, 'ACTIVO'); assert.equal(state.pendingActivation.value, null);
});
