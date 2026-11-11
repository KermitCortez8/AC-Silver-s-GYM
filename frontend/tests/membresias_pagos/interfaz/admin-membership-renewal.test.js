import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, ref } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia, setActivePinia } from 'pinia';
import { canRenewClientMembership } from '../../../src/domain/utils/adminClientPayment.js';
let server, installServices, useClientRenewal;
before(async () => {
  server = await createServer({ root: fileURLToPath(new URL('../../..', import.meta.url)), configFile: false,
    plugins: [vue()], server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useClientRenewal } = await server.ssrLoadModule('/src/presentation/composables/clients/useClientRenewal.js'));
});
after(async () => { await server?.close(); });
const client = { id: 'SGCLI001', id_cliente: 1, name: 'Cliente de prueba', status: 'VENCIDA', membershipStatus: 'VENCIDA', membershipEnd: '2000-01-01', paymentStatus: 'PAGADO' };
const summary = { id_membresia_origen: 4, plan: 'MENSUAL', duracion: '30 días', monto_pago: 80, renovacion_pendiente: false };
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
async function fixture(apiGet = async () => summary, apiPost = async () => ({})) {
  const pinia = createPinia(); setActivePinia(pinia); installServices(pinia, { http: { apiGet, apiPost } });
  let state, instance;
  const refreshes = [];
  const args = { authStore: { token: 'token-sintetico' }, gymStore: { members: [] }, viewingClient: ref({ ...client }),
    feedbackMessage: ref(''), feedbackTone: ref(''), refreshClients: async force => { refreshes.push(force); } };
  const app = createSSRApp({ setup() { state = useClientRenewal(args); return () => null; }, created() { instance = this.$; } });
  app.use(pinia); await renderToString(app);
  return { ...state, args, refreshes, dispose: () => instance.scope.stop() };
}
test('permite renovar activos/vencidos y conserva la activación inicial', () => {
  assert.equal(canRenewClientMembership(client), true);
  assert.equal(canRenewClientMembership({ ...client, status: 'ACTIVO' }), true);
  assert.equal(canRenewClientMembership({ ...client, status: 'EN_TRAMITE' }), false);
  assert.equal(canRenewClientMembership({ ...client, id_cliente: 0 }), false);
});
test('revisar detalles no cobra y efectivo exige confirmación de recibo', async () => {
  let posts = 0;
  const state = await fixture(async () => summary, async () => { posts++; });
  await state.requestRenewal(client);
  assert.equal(state.renewalDetails.value.monto_pago, 80); assert.equal(posts, 0);
  await state.confirmRenewal();
  assert.equal(posts, 0); assert.match(state.renewalError.value, /pago recibido/);
  state.closeRenewal(); assert.equal(state.pendingRenewal.value, null); state.dispose();
});
test('confirmar efectivo bloquea clics duplicados y actualiza la ficha guardada', async () => {
  const pending = deferred(); let posts = 0;
  const state = await fixture(async () => summary, async (path, payload, token) => {
    posts++; assert.equal(path, '/clientes/1/renovar-membresia'); assert.equal(token, 'token-sintetico');
    assert.equal(payload.metodo_pago, 'efectivo'); assert.equal(payload.pago_recibido, true);
    return pending.promise;
  });
  await state.requestRenewal(client); state.renewalCashReceived.value = true;
  const first = state.confirmRenewal(); await state.confirmRenewal(); assert.equal(posts, 1);
  state.closeRenewal(); assert.notEqual(state.pendingRenewal.value, null);
  state.args.gymStore.members = [{ ...client, status: 'ACTIVO', membershipStatus: 'ACTIVO' }];
  pending.resolve({ metodo_pago: 'efectivo', membership_status: 'ACTIVO' }); await first;
  assert.equal(state.args.viewingClient.value.membershipStatus, 'ACTIVO');
  assert.deepEqual(state.refreshes, [true]); assert.equal(state.pendingRenewal.value, null);
  assert.equal(state.renewingClientId.value, ''); state.dispose();
});
test('compra pendiente selecciona Stripe y reutiliza la compra del servidor', async () => {
  const previousWindow = globalThis.window; let assigned;
  globalThis.window = { location: { assign: url => { assigned = url; } } };
  try {
    const state = await fixture(async () => ({ ...summary, renovacion_pendiente: true }), async (_path, payload) => {
      assert.equal(payload.metodo_pago, 'stripe'); assert.equal(payload.id_membresia_origen, 4); assert.equal(payload.monto_pago, 80);
      return { metodo_pago: 'stripe', payment: { checkout_url: 'https://checkout.stripe.com/retomar' } };
    });
    await state.requestRenewal(client); assert.equal(state.renewalMethod.value, 'stripe');
    await state.confirmRenewal(); assert.equal(assigned, 'https://checkout.stripe.com/retomar');
    state.dispose();
  } finally { globalThis.window = previousWindow; }
});
test('error de precio conserva el diálogo sin anunciar renovación ni duplicar el cobro', async () => {
  const state = await fixture(async () => summary, async () => { throw new Error('El precio cambió. Actualiza los detalles.'); });
  await state.requestRenewal(client); state.renewalCashReceived.value = true;
  await state.confirmRenewal(); assert.match(state.renewalError.value, /precio cambió/);
  assert.notEqual(state.pendingRenewal.value, null); assert.equal(state.renewingClientId.value, '');
  assert.equal(state.args.feedbackMessage.value, ''); assert.deepEqual(state.refreshes, []); state.dispose();
});
test('cerrar o cambiar de sesión descarta una respuesta pendiente de detalles', async () => {
  const pending = deferred(); const state = await fixture(() => pending.promise);
  const first = state.requestRenewal(client); state.closeRenewal(); pending.resolve(summary); await first;
  assert.equal(state.pendingRenewal.value, null); assert.equal(state.renewalDetails.value, null); state.dispose();
  const other = deferred(); const switched = await fixture(() => other.promise);
  const loading = switched.requestRenewal(client); switched.args.authStore.token = 'otra-sesion'; other.resolve(summary); await loading;
  assert.equal(switched.renewalDetails.value, null); switched.dispose();
});
test('el botón solo permite vencidas o los últimos siete días, con fecha de Perú', () => {
  const today = '2026-11-09';
  for (const [end, allowed] of [['2026-11-17', false], ['2026-11-16', true], ['2026-11-12', true], ['2026-11-09', true], ['2026-11-08', true]]) {
    assert.equal(canRenewClientMembership({ ...client, status: 'ACTIVO', membershipEnd: end }, today), allowed);
  }
  assert.equal(canRenewClientMembership({ ...client, membershipEnd: '' }, today), false);
  assert.equal(canRenewClientMembership({ ...client, membershipEnd: '2026-02-30' }, today), false);
  assert.equal(canRenewClientMembership({ ...client, status: 'ACTIVO', membershipStart: '2026-11-10', membershipEnd: '2026-11-12' }, today), false);
});
test('el botón respeta la elegibilidad del servidor aunque la última fila sea una compra pendiente', () => {
  const pending = { ...client, status: 'ACTIVO', membershipEnd: '2026-11-09', membershipStatus: 'EN_TRAMITE' };
  assert.equal(canRenewClientMembership({ ...pending, canRenewMembership: false }), false);
  assert.equal(canRenewClientMembership({ ...pending, canRenewMembership: true }), true);
});
