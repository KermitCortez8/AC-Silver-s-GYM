import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';
import { computed, createSSRApp, effectScope, h, proxyRefs, ref } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia, setActivePinia } from 'pinia';
import { createMemoryHistory, createRouter } from 'vue-router';
import { usePublicCatalog } from '../src/application/services/publicCatalog.js';

const plans = [
  { id_pm: 41, nombre_plan: 'PLAN MAÑANA', duracion: '45 días', precio: 100, activo: true },
  { id_pm: 52, nombre_plan: 'FIN DE SEMANA', duracion: '90 días', precio: 200, activo: true },
  { id_pm: 63, nombre_plan: 'RETIRADO', duracion: '30 días', precio: 50, activo: false },
];
const promotions = [
  { id_promocion: 8, nombre: 'Descuento mañana', activo: true, planes_aplicables: ['41'], tipo_descuento: 'porcentaje', valor_descuento: 20 },
  { id_promocion: 9, nombre: 'Descuento fin de semana', activo: true, planes_aplicables: [52], tipo_descuento: 'monto', valor_descuento: 30 },
  { id_promocion: 10, nombre: 'Futura', activo: true, fecha_inicio: '2999-01-01' },
  { id_promocion: 11, nombre: 'Vencida', activo: true, fecha_fin: '2000-01-01' },
  { id_promocion: 12, nombre: 'Agotada', activo: true, limite_cupos: 1, usos_actuales: 1 },
  { id_promocion: 13, nombre: 'Pausada', activo: false },
];
let server, installServices, useGymStore, useAuthStore, useClientEditor;
before(async () => {
  server = await createServer({ root: fileURLToPath(new URL('..', import.meta.url)), configFile: false,
    plugins: [vue()], server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useGymStore } = await server.ssrLoadModule('/src/application/stores/gymStore.js'));
  ({ useAuthStore } = await server.ssrLoadModule('/src/application/stores/authStore.js'));
  ({ useClientEditor } = await server.ssrLoadModule('/src/presentation/composables/clients/useClientEditor.js'));
});
after(async () => { await server?.close(); });
const view = async (filename, get = async path => path === '/planes-membresia' ? plans : promotions, http = {}) => {
  const { default: View } = await server.ssrLoadModule(`/src/presentation/views/${filename}.vue`);
  const pinia = createPinia();
  setActivePinia(pinia);
  installServices(pinia, { http: { apiGet: get, ...http } });
  if (filename === 'ClientsView') {
    const gym = useGymStore(pinia), scope = effectScope();
    const setup = proxyRefs(scope.run(() => useClientEditor({ gymStore: gym,
      clients: computed(() => gym.members), feedbackMessage: ref(''), feedbackTone: ref(''),
      resetFilters() {}, sortOrder: ref('recent'), openDetails() {}, paymentError: ref(''),
      normalizeStatus: value => String(value || '').toUpperCase(),
    })));
    return { setup, gym, auth: useAuthStore(pinia), dispose: () => scope.stop() };
  }
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: View }] });
  await router.push('/');
  let setup, instance;
  const app = createSSRApp({ render: () => h(View) });
  app.use(pinia).use(router);
  app.mixin({ created() { if (this.$.type === View) { setup = this.$.setupState; instance = this.$; } } });
  await renderToString(app);
  return { setup, gym: useGymStore(pinia), auth: useAuthStore(pinia), dispose: () => instance.scope.stop() };
};
const validForm = { nombre: 'Ana', correo: 'ana@example.com', dni: '12345678', telefono: '999111222', password: 'clave123' };
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

test('el registro público guarda una solicitud temporal sin añadir un cliente ni un código ficticio', async () => {
  const token = '12345678-1234-4234-8234-123456789abc';
  const v = await view('RegisterView', undefined, { authHeaders: () => ({}), rawRequest: async () => new Response(JSON.stringify({
    preregistro: { token, estado: 'PENDIENTE', monto_pago: 80, expira_en: '2099-01-01T00:00:00+00:00' },
    payment: { configured: true, message: 'Reintenta con los mismos datos.' },
  }), { headers: { 'content-type': 'application/json' } }) });
  try {
    await v.setup.loadPlans();
    Object.assign(v.setup.form, validForm);
    await v.setup.submitRegistration();
    assert.equal(v.setup.registeredPreregistration.token, token);
    assert.equal(v.setup.registeredClient, undefined);
    assert.equal(v.gym.members.length, 0);
    assert.equal(v.setup.feedback, 'Reintenta con los mismos datos.');
    assert.equal(v.setup.form.correo, validForm.correo);
  } finally { v.dispose(); }
});

test('el servicio consulta los catálogos correctos y normaliza sus IDs', async () => {
  const requests = [];
  const catalog = usePublicCatalog({ apiGet: async path => { requests.push(path); return path === '/planes-membresia' ? plans : promotions; } });
  const result = await catalog.loadClientMembershipCatalog();
  assert.deepEqual(requests, ['/planes-membresia', '/promociones/vigentes-publico']);
  assert.equal(result.plans[0].id, 'pm-41');
  assert.deepEqual(result.promotions[0].appliesTo, ['pm-41']);
  requests.length = 0;
  await catalog.loadClientMembershipCatalog({ includeHistorical: true });
  assert.deepEqual(requests, ['/planes-membresia', '/promociones']);
});

test('el alta administrativa usa planes remotos y promociones aplicables, sin opciones fijas', async () => {
  const v = await view('ClientsView');
  try {
    await v.setup.openNewClient();
    const props = v.setup.clientEditorProps;
    assert.deepEqual(props.editorPlans.map(p => p.name), ['PLAN MAÑANA', 'FIN DE SEMANA']);
    assert.equal(v.setup.form.plan, 'PLAN MAÑANA');
    assert.deepEqual(v.setup.availablePromotions.map(p => p.id_promocion), [8]);
    v.setup.form.id_promocion = 8;
    assert.equal(v.setup.estimatedCharge.finalPrice, 80);
    v.setup.form.plan = 'FIN DE SEMANA';
    assert.equal(v.setup.form.id_promocion, 0);
    assert.deepEqual(v.setup.availablePromotions.map(p => p.id_promocion), [9]);
    v.setup.form.id_promocion = 9;
    assert.equal(v.setup.estimatedCharge.finalPrice, 170);
    Object.assign(v.setup.form, validForm);
    let payload;
    v.gym.upsertClient = async value => { payload = value; return { id: 'SGCLI001', status: 'EN_TRAMITE' }; };
    await v.setup.handleSubmit();
    assert.equal(payload.plan, 'FIN DE SEMANA');
    assert.equal(payload.id_promocion, 9);
  } finally { v.dispose(); }
});

test('carga fallida permite reintentar sin perder el borrador ni registrar con precios locales', async () => {
  let fail = true, calls = 0;
  const v = await view('ClientsView', async path => {
    calls++;
    if (fail) throw new Error('Catálogo indisponible');
    return path === '/planes-membresia' ? plans : promotions;
  });
  try {
    await v.setup.openNewClient();
    Object.assign(v.setup.form, validForm);
    let saves = 0;
    v.gym.upsertClient = async () => { saves++; };
    await v.setup.handleSubmit();
    assert.equal(saves, 0);
    assert.match(v.setup.submitError, /Catálogo indisponible/);
    assert.equal(v.setup.clientEditorProps.canSaveClient, false);
    fail = false;
    await v.setup.clientEditorProps.refreshCatalog();
    assert.equal(v.setup.form.nombre, 'Ana');
    assert.equal(v.setup.clientEditorProps.canSaveClient, true);
    assert.equal(calls, 4);
    v.setup.closeEditor();
    await v.setup.openNewClient();
    assert.equal(calls, 6, 'cada apertura vuelve a consultar ambos catálogos');
  } finally { v.dispose(); }
});

test('editar conserva plan retirado, promoción histórica e importe cero', async () => {
  const v = await view('ClientsView');
  try {
    const client = { id: 'SGCLI001', plan: 'PLAN HISTÓRICO', promocion: 'Vencida', id_promocion: 11,
      membershipPrice: 0, name: 'Ana', email: 'ana@example.com', dni: '12345678', status: 'ACTIVO' };
    v.gym.members = [client];
    await v.setup.editClient(client);
    assert.equal(v.setup.form.plan, 'PLAN HISTÓRICO');
    assert(v.setup.clientEditorProps.editorPlans.some(p => p.name === 'PLAN HISTÓRICO'));
    assert(v.setup.availablePromotions.some(p => p.id_promocion === 11));
    assert.equal(v.setup.clientEditorProps.registeredAmount, 0);
    v.setup.form.nombre = 'Ana editada';
    // Incluso un cambio programático no recontrata una membresía desde datos personales.
    v.setup.form.plan = 'FIN DE SEMANA';
    v.setup.form.id_promocion = 9;
    let payload;
    v.gym.upsertClient = async value => { payload = value; return { ...client, name: value.nombre }; };
    await v.setup.handleSubmit();
    assert.equal(payload.plan, 'PLAN HISTÓRICO');
    assert.equal(payload.id_promocion, 11);
    assert.equal(payload.nombre, 'Ana editada');
  } finally { v.dispose(); }
});

test('la edición enviada al servidor conserva el descriptor de promoción existente', async () => {
  let sent;
  const v = await view('ClientsView', async () => [], {
    authHeaders: () => ({}), rawRequest: async (_url, options) => {
      sent = JSON.parse(options.body);
      return new Response(JSON.stringify({ ...sent, id_cliente: 1 }), { status: 200, headers: { 'content-type': 'application/json' } });
    },
  });
  try {
    v.gym.members = [{ id: 'SGCLI001', id_cliente: 1, ...validForm, name: 'Ana', email: validForm.correo, plan: 'PLAN MAÑANA', promocion: 'Oferta contratada', membershipPrice: 0 }];
    await v.gym.upsertClient({ id_usuario: 'SGCLI001', nombre: 'Ana editada', plan: 'PLAN MAÑANA' });
    assert.equal(sent.promocion, 'Oferta contratada');
    assert.equal(v.gym.members[0].membershipPrice, 0);
  } finally { v.dispose(); }
});

test('registro público calcula descuentos remotos y descarta promociones futuras, agotadas o ajenas', async () => {
  const requests = [];
  const v = await view('RegisterView', async path => { requests.push(path); return path === '/planes-membresia' ? plans : promotions; });
  try {
    await v.setup.loadPlans();
    assert.deepEqual(requests, ['/planes-membresia', '/promociones/vigentes-publico']);
    assert.deepEqual(v.setup.planOptions.map(p => [p.id, p.price]), [['PLAN MAÑANA', 80], ['FIN DE SEMANA', 170]]);
    assert.equal(v.setup.form.plan, 'PLAN MAÑANA');
    assert.equal(v.setup.canRegister, true);
    v.setup.form.plan = 'MENSUAL';
    assert.equal(v.setup.canRegister, false);
  } finally { v.dispose(); }
});

test('registro público no inventa planes cuando el catálogo está vacío o falla', async () => {
  for (const fail of [false, true]) {
    const v = await view('RegisterView', async () => { if (fail) throw new Error('Sin conexión'); return []; });
    try {
      await v.setup.loadPlans();
      assert.deepEqual(v.setup.planOptions, []);
      assert.equal(v.setup.canRegister, false);
      Object.assign(v.setup.form, validForm, { plan: 'MENSUAL' });
      let calls = 0;
      v.gym.registerPublicClient = async () => { calls++; };
      await v.setup.submitRegistration();
      assert.equal(calls, 0);
      assert.equal(v.setup.form.nombre, 'Ana');
    } finally { v.dispose(); }
  }
});

test('catálogos mal formados impiden el alta y una respuesta tardía no se publica tras salir', async () => {
  const service = usePublicCatalog({ apiGet: async () => ({ data: [] }) });
  await assert.rejects(service.loadClientMembershipCatalog(), /datos incompletos o inválidos/);
  const pending = deferred();
  const v = await view('RegisterView', async path => path === '/planes-membresia' ? pending.promise : []);
  const first = v.setup.loadPlans(), second = v.setup.loadPlans();
  assert.equal(v.setup.catalogLoading, true);
  assert.equal(v.setup.canRegister, false);
  v.dispose();
  pending.resolve(plans);
  await Promise.all([first, second]);
  assert.deepEqual(v.setup.planOptions, []);
});
