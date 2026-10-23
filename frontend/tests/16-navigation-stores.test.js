import assert from 'node:assert/strict';
import { after, before, beforeEach, test } from 'node:test';
import { createPinia } from 'pinia';
import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';

let server;
let useAuthStore;
let useGymStore;
let auth;
let gym;

const originals = {
  fetch: globalThis.fetch,
  window: globalThis.window,
  localStorage: globalThis.localStorage,
};

const profile = {
  id_usuario: 'ADMIN1',
  name: 'Admin Demo',
  email: 'admin@example.com',
  role: 'admin',
};

const token = `test.${btoa(JSON.stringify({
  exp: Math.floor(Date.now() / 1000) + 3600,
}))}.test`;

const json = (value, status = 200) => new Response(JSON.stringify(value), {
  status,
  headers: { 'content-type': 'application/json' },
});

const deferred = () => {
  let resolve;
  const promise = new Promise((done) => {
    resolve = done;
  });
  return { promise, resolve };
};

const flush = () => new Promise((resolve) => setImmediate(resolve));

test('users save, replace and delete through the configured repository, including empty 204 responses', async () => {
  auth.token = token;
  gym.users = [];
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push([url, options.method]);
    assert.equal(options.headers.Authorization, `Bearer ${token}`);
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.equal(Object.hasOwn(options, 'errorMessage'), false);
    if (options.method === 'DELETE') return new Response(null, { status: 204 });
    return json({ ...JSON.parse(options.body), id_usuario: 'SGUS001', has_password: true });
  };

  const created = await gym.upsertUser({ nombre: ' Ana ', email: 'ana@example.com', rol: 'trainer' });
  assert.equal(created.nombre, 'Ana');
  assert.equal(created.correo, 'ana@example.com');
  assert.equal(created.hasPassword, true);

  await gym.upsertUser({ id_usuario: created.id_usuario, nombre: 'Ana Perez' });
  assert.equal(gym.users.length, 1);
  assert.equal(gym.users[0].nombre, 'Ana Perez');
  assert.equal(gym.users[0].rol, 'trainer');

  await gym.deleteUser(created.id_usuario);
  assert.deepEqual(gym.users, []);
  assert.deepEqual(requests, [
    ['/api/usuarios', 'POST'], ['/api/usuarios', 'POST'], ['/api/usuarios/SGUS001', 'DELETE'],
  ]);
});

test('failed user writes preserve local users and their existing error messages', async () => {
  gym.users = [{ id_usuario: 'SGUS001', nombre: 'Ana', rol: 'staff' }];
  const initial = gym.users.map((user) => ({ ...user }));
  globalThis.fetch = async () => json({ detail: 'Acceso denegado' }, 403);

  await assert.rejects(gym.upsertUser({ id_usuario: 'SGUS001', nombre: 'Otra persona' }), /Error al guardar usuario/);
  await assert.rejects(gym.deleteUser('SGUS001'), /Error al eliminar usuario/);
  assert.deepEqual(gym.users, initial);
});

test('gym configuration loads and saves data, preserving the last settings if the server rejects a change', async () => {
  auth.token = token;
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/gym/configuracion');
    assert.equal(options.headers.Authorization, `Bearer ${token}`);
    if (options.method === 'GET') return json({ capacidad_total: 40, capacidad_por_hora: 12 });
    const body = JSON.parse(options.body);
    assert.deepEqual(body, { capacidad_total: 50, capacidad_por_hora: 15 });
    return json(body);
  };

  assert.deepEqual(await gym.refreshGymSettingsFromBackend(), { capacidad_total: 40, capacidad_por_hora: 12 });
  assert.deepEqual(await gym.updateGymSettings({ totalCapacity: '50', hourCapacity: '15' }), {
    capacidad_total: 50, capacidad_por_hora: 15,
  });

  globalThis.fetch = async () => json({ detail: 'Configuracion no valida' }, 400);
  await assert.rejects(gym.updateGymSettings({ totalCapacity: 60 }), /Configuracion no valida/);
  assert.equal(gym.gymSettings.capacidad_total, 50);
});

before(async () => {
  // Vite resuelve los imports del store sin abrir puertos ni conectar con la API.
  server = await createServer({
    root: fileURLToPath(new URL('..', import.meta.url)),
    configFile: false,
    server: {
      middlewareMode: true,
      hmr: false,
      ws: false,
      watch: null,
    },
  });

  await server.ssrLoadModule('/src/bootstrap.js');
  ({ useAuthStore } = await server.ssrLoadModule('/src/application/stores/authStore.js'));
  ({ useGymStore } = await server.ssrLoadModule('/src/application/stores/gymStore.js'));
});

beforeEach(() => {
  const values = new Map();

  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  };

  globalThis.window = {};
  globalThis.fetch = async () => {
    throw new Error('Unexpected network request');
  };

  const pinia = createPinia();
  auth = useAuthStore(pinia);
  gym = useGymStore(pinia);
});

after(async () => {
  Object.assign(globalThis, originals);
  await server?.close();
});

test('store checks a restored session once and rejects locally expired tokens before using the cache', async () => {
  localStorage.setItem('gym_auth_token', token);

  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return json(profile);
  };

  await Promise.all([auth.initializeAuth(), auth.initializeAuth()]);

  for (let index = 0; index < 5; index++) {
    await auth.initializeAuth();
  }

  assert.equal(calls, 1);
  assert.equal(auth.isAdmin, true);

  localStorage.setItem('gym_auth_token_expiry', Date.now() - 1);
  await auth.initializeAuth();

  assert.equal(auth.isAuthenticated, false);
  assert.equal(auth.token, null);
  assert.equal(calls, 1);
});

test('a pending validation cannot restore a signed-out session', async () => {
  localStorage.setItem('gym_auth_token', token);

  const response = deferred();
  globalThis.fetch = () => response.promise;

  const check = auth.initializeAuth();
  await flush();
  await auth.signOut();

  response.resolve(json(profile));
  await check;

  assert.equal(auth.isAuthenticated, false);
  assert.equal(localStorage.getItem('gym_auth_token'), null);
});

test('server rejection on revalidation clears the previously valid session', async () => {
  localStorage.setItem('gym_auth_token', token);
  globalThis.fetch = async () => json(profile);

  await auth.initializeAuth();

  globalThis.fetch = async () => json({ detail: 'Cuenta desactivada' }, 403);
  await auth.initializeAuth({ force: true });

  assert.equal(auth.isAuthenticated, false);
  assert.equal(auth.userRole, null);
  assert.equal(localStorage.getItem('gym_auth_token'), null);
});

test('membership expiration closes an existing session and keeps the reason for the login notice', async () => {
  localStorage.setItem('gym_auth_token', token);

  globalThis.fetch = async () => json({
    ...profile,
    role: 'user',
    id_cliente: 1,
  });

  await auth.initializeAuth();
  assert.equal(auth.isAuthenticated, true);

  globalThis.fetch = async () => json({
    detail: {
      code: 'membership_expired',
      message: 'Tu membresía está vencida',
    },
  }, 403);

  await auth.initializeAuth({ force: true });

  assert.equal(auth.isAuthenticated, false);
  assert.equal(auth.sessionErrorCode, 'membership_expired');
  assert.equal(localStorage.getItem('gym_auth_token'), null);

  await auth.initializeAuth();
  assert.equal(auth.sessionErrorCode, 'membership_expired');

  await auth.signIn(token, profile);
  assert.equal(auth.sessionErrorCode, '');
});

test('section changes reuse synced data; refresh and a new session fetch it again', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return json([]);
  };

  await Promise.all([gym.fetchFromBackend(), gym.fetchFromBackend()]);

  const initialCalls = calls;
  assert.ok(initialCalls > 0);

  await gym.fetchFromBackend();
  assert.equal(calls, initialCalls);

  await gym.fetchFromBackend({ force: true });
  assert.equal(calls, initialCalls * 2);

  auth.token = 'another-session';
  await gym.fetchFromBackend();
  assert.equal(calls, initialCalls * 3);
});

test('payments section fetches membership history and refreshes confirmed Stripe payments', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const calls = [];
  let status = 'PENDIENTE';

  globalThis.fetch = async (url) => {
    calls.push(url);
    assert.ok(url.endsWith('/pagos/membresias'));

    return json([{
      id_membresia: 1,
      estado_pago: status,
      metodo_pago: 'stripe',
    }]);
  };

  await gym.fetchFromBackend({ section: 'payments' });

  assert.equal(calls.length, 1);
  assert.equal(gym.membershipPayments[0].estado_pago, 'PENDIENTE');

  status = 'PAGADO';

  await gym.fetchFromBackend({ section: 'payments', force: true });

  assert.equal(calls.length, 2);
  assert.equal(gym.membershipPayments[0].estado_pago, 'PAGADO');
});

test('users finish loading while a previous section still has pending requests', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const clients = deferred();

  globalThis.fetch = async (url) => {
    if (url.endsWith('/clientes')) {
      await clients.promise;
    }
    return json([]);
  };

  const previous = gym.fetchFromBackend({ section: 'clients' });
  await flush();

  assert.equal(gym.isSyncing, true);
  assert.equal(gym.isSectionSyncing('clients'), true);
  assert.equal(gym.isSectionSyncing('users'), false);

  await gym.fetchFromBackend({ section: 'users' });

  assert.equal(gym.isSyncing, true);
  assert.equal(gym.isSectionSyncing('users'), false);

  clients.resolve();
  await previous;

  assert.equal(gym.isSyncing, false);
  assert.equal(gym.isSectionSyncing('clients'), false);
});

test('a failed users request clears only its section loading status', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  globalThis.fetch = async () => json({ detail: 'Sin conexión' }, 503);

  await assert.rejects(
    gym.fetchFromBackend({ section: 'users' }),
    /Sin conexión/,
  );

  assert.equal(gym.isSectionSyncing('users'), false);
  assert.equal(gym.isSyncing, false);
  assert.match(gym.syncError, /Usuarios/);
});

test('synced data expires after thirty seconds', async (t) => {
  let now = 0;
  t.mock.method(Date, 'now', () => now);

  auth.token = token;
  auth.userRole = 'admin';

  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return json([]);
  };

  await gym.fetchFromBackend();
  const firstCalls = calls;

  now = 29_999;
  await gym.fetchFromBackend();
  assert.equal(calls, firstCalls);

  now = 30_000;
  await gym.fetchFromBackend();
  assert.equal(calls, firstCalls * 2);
});

test('failed forced refresh is not cached and a later navigation retries it', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  let fail = false;
  let clientRequests = 0;

  globalThis.fetch = async (url) => {
    if (url.endsWith('/clientes')) {
      clientRequests++;
      if (fail) {
        return json({ detail: 'Sin conexión' }, 503);
      }
    }
    return json([]);
  };

  await gym.fetchFromBackend();

  fail = true;
  await assert.rejects(
    gym.fetchFromBackend({ force: true }),
    /Sin conexión/,
  );

  fail = false;
  await gym.fetchFromBackend();

  assert.equal(clientRequests, 3);
  assert.equal(gym.syncError, '');
});

test('attendance waits for client names and forced refresh runs after the pending sync', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const clients = deferred();
  let clientRequests = 0;
  let attendanceRequests = 0;

  globalThis.fetch = async (url) => {
    if (url.endsWith('/clientes')) {
      clientRequests++;

      if (clientRequests === 1) {
        await clients.promise;
      }

      return json([{
        id_cliente: 1,
        nombre: 'Cliente Demo',
        correo: 'cliente@example.com',
      }]);
    }

    if (url.endsWith('/asistencia')) {
      attendanceRequests++;

      return json([{
        id_asistencia: 1,
        id_cliente: 1,
        fecha: '2026-09-17',
        hora: '10:00',
      }]);
    }

    return json([]);
  };

  const initial = gym.fetchFromBackend();
  const forced = gym.fetchFromBackend({ force: true });

  await flush();
  assert.equal(attendanceRequests, 0);

  clients.resolve();
  await Promise.all([initial, forced]);

  assert.equal(clientRequests, 2);
  assert.equal(attendanceRequests, 2);
  assert.equal(gym.attendance[0].memberName, 'Cliente Demo');
});

test('admin registration sends the payment choice and keeps the saved membership amount and origin', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const requests = [];

  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });

    return json({
      cliente: {
        id_cliente: 12,
        id_usuario: 'SGCLI012',
        nombre: 'Cliente',
        plan: 'MENSUAL',
        estado: 'PENDIENTE_PAGO',
        origen_registro: 'ADMIN',
      },
      membresia: {
        id_membresia: 34,
        estado: 'PENDIENTE_PAGO',
        estado_pago: 'PENDIENTE',
        monto_pago: 69,
        id_promocion: 5,
      },
      payment: {
        checkout_url: 'https://checkout.stripe.com/test',
        amount: 69,
      },
    });
  };

  const saved = await gym.upsertClient({
    nombre: 'Cliente',
    correo: 'cliente@example.com',
    password: 'secreto',
    dni: '12345678',
    id_promocion: 5,
    pagar_con_stripe: true,
  });

  assert.equal(requests.length, 1);
  assert.ok(requests[0].url.endsWith('/clientes/registro-admin'));
  assert.equal(
    requests[0].options.headers.Authorization,
    `Bearer ${token}`,
  );

  const payload = JSON.parse(requests[0].options.body);

  assert.equal(payload.pagar_con_stripe, true);
  assert.equal(payload.id_promocion, 5);
  assert.equal(saved.registrationOrigin, 'ADMIN');
  assert.equal(saved.membershipPrice, 69);
  assert.equal(saved.id_membresia, 34);
  assert.equal(saved.paymentStatus, 'PENDIENTE');
  assert.equal(
    saved.payment.checkout_url,
    'https://checkout.stripe.com/test',
  );
  assert.equal(gym.members[0].registrationOrigin, 'ADMIN');
});

test('each admin section loads only its resources and shares them with the dashboard', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const paths = [];

  globalThis.fetch = async (url) => {
    paths.push(new URL(url, 'http://local').pathname);
    return json([]);
  };

  await gym.fetchFromBackend({ section: 'users' });
  assert.deepEqual(paths, ['/api/usuarios']);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'plans' });
  assert.deepEqual(paths, ['/api/planes-membresia']);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'clients' });

  assert.ok(paths.includes('/api/clientes'));
  assert.equal(
    paths.some(path => /inventario|tienda|asistencia/.test(path)),
    false,
  );
  assert.equal(paths.includes('/api/planes-membresia'), false);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'schedules' });
  assert.equal(paths.length, 2);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'dashboard' });

  assert.equal(paths.includes('/api/clientes'), false);
  assert.equal(
    paths.some(path => /usuarios|tienda|planes-membresia|rutinas/.test(path)),
    false,
  );

  paths.length = 0;

  await Promise.all(
    ['users', 'plans', 'clients', 'schedules', 'dashboard'].map(
      section => gym.fetchFromBackend({ section }),
    ),
  );

  assert.deepEqual(paths, []);

  await gym.fetchFromBackend({ section: 'users', force: true });
  assert.deepEqual(paths, ['/api/usuarios']);
});

test('switching to users is not delayed by a pending client list', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const clients = deferred();

  globalThis.fetch = async url => {
    if (url.endsWith('/clientes')) {
      await clients.promise;
    }
    return json([]);
  };

  const clientLoad = gym.fetchFromBackend({ section: 'clients' });
  await flush();

  await gym.fetchFromBackend({ section: 'users' });
  assert.equal(gym.isSyncing, true);

  clients.resolve();
  await clientLoad;

  assert.equal(gym.isSyncing, false);
});

test('a new session loads immediately and discards previous data responses', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const oldResponse = deferred();
  let clientRequests = 0;

  globalThis.fetch = async url => {
    if (url.endsWith('/clientes')) {
      const request = ++clientRequests;

      if (request === 1) {
        await oldResponse.promise;
      }

      return json([{
        id_cliente: request,
        nombre: `Sesión ${request}`,
      }]);
    }

    return json([]);
  };

  const oldLoad = gym.fetchFromBackend({ section: 'clients' }).catch(error => error);
  await flush();

  auth.token = 'new-session-token';
  const newLoad = gym.fetchFromBackend({ section: 'clients' });
  await newLoad;
  assert.equal(clientRequests, 2);
  assert.equal(gym.members[0].name, 'Sesión 2');

  oldResponse.resolve();
  assert.match((await oldLoad).message, /sesión ha cambiado/);
  assert.equal(gym.members[0].name, 'Sesión 2');
});

test('trainer routine requests preserve exercises when saving and refreshing the catalog', async () => {
  auth.token = token;
  auth.userRole = 'trainer';

  const exercises = [{
    id_ejercicio: 'press',
    nombre_ejercicio: 'Press',
    series: 4,
    repeticiones: '8-12',
    descanso_segundos: 90,
    peso_sugerido_kg: 30,
  }];

  let sent;

  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/trainer/rutinas')) {
      sent = JSON.parse(options.body);
      return json({ ...sent, id_rutina: 15 });
    }

    assert.ok(url.endsWith('/trainer/overview'));

    return json({
      routines: [{
        ...sent,
        id_rutina: 15,
        clientes_asignados: 2,
      }],
    });
  };

  const saved = await gym.upsertTrainerRoutine({
    nombre_rutina: ' Fuerza ',
    zonas_musculares: ' Pecho ',
    servicio: 'musculacion',
    ejercicios: exercises,
  });

  assert.equal(sent.nombre_rutina, 'Fuerza');
  assert.deepEqual(sent.ejercicios, exercises);
  assert.deepEqual(saved.ejercicios, exercises);
  assert.deepEqual(gym.trainerOverview.routines[0].ejercicios, exercises);
});

test('trainer progress requests preserve state and exercise performance', async () => {
  auth.token = token;
  auth.userRole = 'trainer';

  const details = [{
    nombre_ejercicio: 'Press',
    completado: true,
    series_completadas: 4,
    repeticiones_logradas: '10',
    peso_utilizado_kg: 30,
  }];

  globalThis.fetch = async (url, options) => {
    assert.ok(url.endsWith('/trainer/matriculas/10/progreso'));

    const body = JSON.parse(options.body);

    assert.equal(body.estado, 'REALIZADO');
    assert.equal(body.fecha, '2026-10-01');
    assert.deepEqual(body.ejercicios_detalle, details);

    return json({ ...body, id_matricula: 10 });
  };

  const result = await gym.markTrainerRoutineProgress(10, {
    fecha: '2026-10-01',
    estado: 'REALIZADO',
    ejercicios_detalle: details,
  });

  assert.deepEqual(result.ejercicios_detalle, details);
});

test('trainer requests keep the loading indicator until concurrent section loads finish', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const users = deferred();

  globalThis.fetch = async url => {
    if (url.endsWith('/usuarios')) {
      return users.promise;
    }
    if (url.endsWith('/trainer/overview')) {
      return json({ routines: [] });
    }
    throw new Error(`Unexpected request: ${url}`);
  };

  const userLoad = gym.fetchFromBackend({ section: 'users' });
  await flush();

  await gym.fetchTrainerOverview();
  assert.equal(gym.isSyncing, true);

  users.resolve(json([]));
  await userLoad;

  assert.equal(gym.isSyncing, false);

  globalThis.fetch = async () => json({
    detail: 'No se pudo cargar el catálogo',
  }, 503);

  await assert.rejects(
    () => gym.fetchTrainerOverview({ force: true }),
    /No se pudo cargar el catálogo/,
  );

  assert.equal(gym.isSyncing, false);
});

test('inventory, orders, promotions and payments load only their own data', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const paths = [];

  globalThis.fetch = async url => {
    const path = new URL(url, 'http://local').pathname;
    paths.push(path);
    return json(path.endsWith('/configuracion') ? {} : []);
  };

  await gym.fetchFromBackend({ section: 'inventory' });

  assert.deepEqual(paths.sort(), [
    '/api/inventario',
    '/api/inventario/movimientos',
  ]);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'orders' });

  assert.deepEqual(paths.sort(), [
    '/api/clientes',
    '/api/tienda/pedidos',
  ]);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'promotions' });

  assert.deepEqual(paths.sort(), [
    '/api/planes-membresia',
    '/api/promociones',
  ]);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'payments' });

  assert.deepEqual(paths.sort(), ['/api/pagos/membresias']);
});

test('admin store shares its resources with inventory and orders', async () => {
  auth.token = token;
  auth.userRole = 'admin';

  const paths = [];

  globalThis.fetch = async url => {
    paths.push(new URL(url, 'http://local').pathname);
    return json([]);
  };

  await gym.fetchFromBackend({ section: 'store' });

  assert.deepEqual(paths.sort(), [
    '/api/clientes',
    '/api/inventario',
    '/api/tienda',
    '/api/tienda/pedidos',
  ]);

  paths.length = 0;
  await gym.fetchFromBackend({ section: 'orders' });

  assert.deepEqual(paths, []);
});

test('trainer views share the pending overview and refresh explicitly after navigation', async () => {
  auth.token = token;
  auth.userRole = 'trainer';

  const pending = deferred();
  let calls = 0;

  globalThis.fetch = async url => {
    assert.ok(url.endsWith('/trainer/overview'));
    calls++;

    if (calls === 1) {
      return pending.promise;
    }

    return json({
      routines: [{ id_rutina: 2 }],
    });
  };

  const first = gym.fetchTrainerOverview();
  const second = gym.fetchTrainerOverview();

  await flush();
  assert.equal(calls, 1);

  pending.resolve(json({
    routines: [{ id_rutina: 1 }],
  }));

  await Promise.all([first, second]);

  await gym.fetchTrainerOverview();
  assert.equal(calls, 1);

  await gym.fetchFromBackend({ section: 'trainer' });
  assert.equal(calls, 1);

  await gym.fetchFromBackend({ section: 'trainer', force: true });

  assert.equal(calls, 2);
  assert.equal(gym.trainerOverview.routines[0].id_rutina, 2);
  assert.equal(gym.isSyncing, false);
});

test('failed client and product deletions keep their rows and surface the server error', async () => {
  auth.token = token;
  gym.members = [{ id: 'SGCLI001', name: 'Ana' }];
  gym.productos_tienda = [{ id_producto: 1, nombre: 'Agua' }];
  globalThis.fetch = async () => json({ detail: 'No se pudo guardar' }, 500);
  await assert.rejects(gym.deleteClient('SGCLI001'), /No se pudo guardar/);
  await assert.rejects(gym.deleteProductoTienda(1), /No se pudo guardar/);
  assert.equal(gym.members.length, 1);
  assert.equal(gym.productos_tienda.length, 1);
});

test('client and product deletion waits for server confirmation', async () => {
  auth.token = token;
  gym.members = [{ id: 'SGCLI001', name: 'Ana' }];
  gym.productos_tienda = [{ id_producto: 1, nombre: 'Agua' }];
  const response = deferred();
  globalThis.fetch = () => response.promise;
  const deleting = Promise.all([gym.deleteClient('SGCLI001'), gym.deleteProductoTienda(1)]);
  await flush();
  assert.equal(gym.members.length, 1);
  assert.equal(gym.productos_tienda.length, 1);
  response.resolve(new Response(null, { status: 204 }));
  await deleting;
  assert.equal(gym.members.length, 0);
  assert.equal(gym.productos_tienda.length, 0);
});

test('logout clears all business state and pending old-session loads cannot restore it', async () => {
  auth.token = token;
  auth.userRole = 'admin';
  gym.members = [{ id: 'SGCLI001', name: 'Ana' }];
  gym.users = [{ id_usuario: 'SGSTA001' }];
  gym.storeOrders = [{ id_pedido: 1 }];
  gym.cart = [{ id_producto: 1, cantidad: 1 }];
  gym.membershipPayments = [{ id_membresia: 1 }];
  const response = deferred();
  globalThis.fetch = async (url) => url.endsWith('/clientes') ? response.promise : json([]);
  const loading = gym.fetchFromBackend({ section: 'clients' }).catch(error => error);
  await flush();
  await auth.signOut();
  for (const key of ['members', 'users', 'storeOrders', 'cart', 'membershipPayments']) assert.equal(gym[key].length, 0, key);
  response.resolve(json([{ id_cliente: 2, nombre: 'Otra sesión' }]));
  assert.match((await loading).message, /sesión ha cambiado/);
  assert.equal(gym.members.length, 0);
  assert.equal(gym.isSyncing, false);
  assert.equal(gym.syncError, '');
});

test('pending user saves cannot restore rows after logout, even if JSON finishes later', async () => {
  auth.token = token;
  const body = deferred();
  globalThis.fetch = async () => ({
    ok: true, status: 200, headers: new Headers({ 'content-type': 'application/json' }), json: () => body.promise,
  });
  const saving = gym.upsertUser({ nombre: 'Ana' }).catch(error => error);
  await flush();
  await auth.signOut();
  body.resolve({ id_usuario: 'SGSTA001', nombre: 'Ana' });
  assert.match((await saving).message, /sesión ha cambiado/);
  assert.equal(gym.users.length, 0);
});

test('provider errors cannot prevent local logout or retain business data', async () => {
  auth.token = token;
  auth.user = profile;
  auth.userRole = 'admin';
  gym.users = [{ id_usuario: 'SGSTA001' }];
  window.google = { accounts: { id: { disableAutoSelect() { throw new Error('Synthetic provider failure'); } } } };
  await auth.signOut();
  assert.equal(auth.isAuthenticated, false);
  assert.equal(auth.token, null);
  assert.equal(gym.users.length, 0);
});

test('logout also cancels queued synchronization tasks before they start another request', async () => {
  auth.token = token;
  auth.userRole = 'admin';
  const response = deferred();
  let calls = 0;
  globalThis.fetch = async () => { calls++; await response.promise; return json([]); };
  const loading = gym.fetchFromBackend({ section: 'all' }).catch(error => error);
  await flush();
  assert.equal(calls, 3);
  await auth.signOut();
  response.resolve();
  assert.match((await loading).message, /sesión ha cambiado/);
  assert.equal(calls, 3);
  for (const key of ['members', 'users', 'inventory', 'planCatalog', 'storeOrders', 'productos_tienda']) {
    assert.equal(gym[key].length, 0, key);
  }
  assert.equal(gym.syncError, '');
});
