// Revisión local: API y sesiones sintéticas. No envía datos a proveedores.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const currentUrl = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';
const baselineUrl = process.env.GYM_VIEWS_BASELINE_URL;
const temporary = '/tmp/gym-views-visual';
fs.mkdirSync(temporary, { recursive: true });

const cases = [
  ['clientes', 'admin', '/admin/clients'], ['matriculas', 'user', '/user/schedule?fecha=2026-11-02'],
  ['panel', 'admin', '/admin/dashboard'], ['movimientos', 'admin', '/admin/inventory?tab=movimientos'],
  ['inventario', 'admin', '/admin/inventory'], ['inicio', '', '/'], ['login', '', '/login'],
  ['promociones', 'admin', '/admin/promotions'], ['registro', '', '/registro'],
  ['horarios', 'admin', '/admin/service-schedules'], ['tienda', 'admin', '/admin/store'],
  ['tienda-cliente', 'user', '/user/store'], ['rutinas', 'trainer', '/trainer/routines'], ['usuarios', 'admin', '/admin/users'],
];
const member = { id_cliente: 1, id_usuario: 'SGCLI001', nombre: 'Ana local', correo: 'ana@example.test',
  dni: '11111111', estado: 'ACTIVO', plan: 'Mensual', membership_status: 'ACTIVA',
  membership_start: '2026-11-01', membership_end: '2026-12-31', payment_status: 'PAGADO', monto_pago: 100 };
const plan = { id_pm: 1, nombre_plan: 'Mensual', duracion: '1 mes', precio: 100, activo: true };
const schedule = { id_horario_servicio: 1, servicio: 'fitness', id_rutina: 7, dia: 'lunes',
  hora_inicio: '10:00', hora_fin: '11:00', cupos: 10, cupos_usados: 1, activo: true,
  rutina_nombre: 'Fuerza local', ocupacion_por_fecha: { '2026-11-02': 1 } };
const product = { id_producto: 1, id_item: 1, nombre_producto: 'Agua local', categoria: 'Bebidas',
  descripcion: 'Agua para el entrenamiento', precio_venta: 3, cantidad_stock: 5, stock_minimo: 0,
  estado: 'Disponible', unidad_venta: 'unidad' };
const routine = { id_rutina: 7, nombre_rutina: 'Fuerza local', servicio: 'fitness', zonas_musculares: 'Pierna',
  ejercicios: [{ id_ejercicio: 1, nombre_ejercicio: 'Sentadilla', grupo_muscular: 'Pierna', series: 3,
    repeticiones: '10', descanso_segundos: 60, peso_sugerido_kg: 10 }] };

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const pageErrors = [], vueWarnings = [], results = [], writes = [];
  const open = async (base, [name, role, target], mobile = false) => {
    const page = await browser.newPage({ viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1100 } });
    page.setDefaultTimeout(15000);
    await page.clock.install({ time: new Date('2026-11-02T10:30:00-05:00') });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    page.on('pageerror', (e) => pageErrors.push(`${name}: ${e.message}`));
    page.on('console', (msg) => {
      if (/\[Vue warn\].*(Invalid prop|not defined|readonly|Missing required)/.test(msg.text())) vueWarnings.push(`${name}: ${msg.text()}`);
    });
    const profile = { id: role === 'user' ? 'SGCLI001' : 'SGUSU001', id_usuario: role === 'user' ? 'SGCLI001' : 'SGUSU001',
      id_cliente: role === 'user' ? 1 : null, name: 'Sesión local', email: 'local@example.test', role };
    await page.addInitScript(({ profile, mobile }) => {
      if (window.top !== window) return;
      localStorage.setItem('ac-silver-theme', mobile ? 'light' : 'dark');
      if (profile.role) {
        localStorage.setItem('gym_auth_user', JSON.stringify(profile));
        localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now()/1000)+3600 }))}.firma-local`);
      }
    }, { profile, mobile });
    const routines = [structuredClone(routine)];
    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (!url.pathname.startsWith('/api/')) return route.continue();
      const endpoint = url.pathname.slice(4), request = route.request();
      let data = [];
      if (endpoint === '/auth/me') data = profile;
      else if (endpoint === '/clientes/me') data = member;
      else if (endpoint === '/clientes') data = [member];
      else if (endpoint === '/planes-membresia') data = [plan];
      else if (['/promociones', '/promociones/vigentes-publico'].includes(endpoint)) data = [];
      else if (['/gym/horarios-servicio', '/gym/horarios-publicos'].includes(endpoint)) data = [schedule];
      else if (endpoint === '/gym/matriculas') data = [{ ...schedule, id_matricula: 1, id_cliente: 1,
        fecha_matricula: '2026-11-01', fecha_clase: '2026-11-02', estado: 'ACTIVA', asistencias: [] }];
      else if (endpoint === '/gym/rutinas') data = routines;
      else if (endpoint === '/inventario') data = [{ id_item: 1, nombre_item: 'Agua almacén', tipo: 'Tienda',
        cantidad_stock: 20, stock_minimo: 0, estado: 'Operativo', unidad_venta: 'unidad' }];
      else if (endpoint === '/tienda') data = [product];
      else if (endpoint === '/usuarios') data = [{ id_usuario: 'SGUSU001', nombre: 'Personal local',
        correo: 'personal@example.test', rol: 'staff', estado: 'ACTIVO' }];
      else if (endpoint === '/trainer/overview') data = { routines, stats: {}, schedule_monitor: [], routine_supervision: [] };
      else if (endpoint === '/gym/configuracion') data = { capacidad_total: 30, capacidad_por_hora: 10 };
      else if (endpoint === '/gym/resumen') data = {};
      if (request.method() === 'POST') {
        const payload = request.postDataJSON();
        writes.push({ endpoint, payload });
        if (endpoint === '/trainer/rutinas') {
          data = { ...payload, id_rutina: 8 };
          routines.push(data);
        } else if (endpoint === '/tienda') data = { ...product, ...payload, id_producto: 1 };
        else if (endpoint === '/promociones') data = { ...payload, id_promocion: 2 };
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(base + target);
    if (name === 'movimientos') {
      await page.evaluate(async () => {
        const { default: router } = await import('/src/presentation/router/index.js');
        router.addRoute({ path: '/revision-movimientos', component: () => import('/src/presentation/views/InventoryMovementsView.vue'),
          meta: { requiresAuth: true } });
        await router.push('/revision-movimientos');
      });
    }
    await page.locator('h1:visible').first().waitFor();
    await page.waitForLoadState('networkidle');
    await page.locator('.module-loader-overlay').waitFor({ state: 'hidden' });
    if (['matriculas', 'horarios'].includes(name)) await page.locator('.fc-event').first().waitFor();
    return page;
  };
  for (let offset = 0; offset < cases.length; offset += 3) {
    await Promise.all(cases.slice(offset, offset + 3).map(async (entry) => {
      const [name] = entry;
      let original;
      if (baselineUrl) {
        const before = await open(baselineUrl, entry);
        original = await before.locator('main').count() ? await before.locator('main').first().innerText() : await before.locator('body').innerText();
        await before.screenshot({ path: path.join(temporary, `${name}-antes.png`), fullPage: true, animations: 'disabled' });
        await before.close();
      }
      const page = await open(currentUrl, entry);
      const text = await page.locator('main').count() ? await page.locator('main').first().innerText() : await page.locator('body').innerText();
      if (original !== undefined) assert.equal(text, original, `Contenido visible distinto en ${name}`);
      await page.screenshot({ path: path.join(temporary, `${name}-despues.png`), fullPage: true, animations: 'disabled' });
      results.push({ view: name, sameVisibleContent: original === undefined ? null : true });
      await page.close();
      console.log(`Vista verificada: ${name}`);
    }));
  }

  const store = await open(currentUrl, cases.find(([n]) => n === 'tienda'));
  await store.getByRole('searchbox', { name: 'Buscar productos por N° o nombre' }).fill('no existe');
  await store.getByText('Sin resultados', { exact: true }).waitFor();
  await store.getByRole('searchbox', { name: 'Buscar productos por N° o nombre' }).fill('Agua');
  await store.getByRole('button', { name: 'Detalles', exact: true }).click();
  await store.getByRole('button', { name: 'Editar producto', exact: true }).click();
  await store.getByRole('button', { name: 'Guardar cambios', exact: true }).waitFor();
  await store.screenshot({ path: path.join(__dirname, 'tienda-editor.png'), fullPage: true, animations: 'disabled' });
  await store.close();

  const clientStore = await open(currentUrl, cases.find(([n]) => n === 'tienda-cliente'), true);
  await clientStore.getByRole('button', { name: 'Agregar Agua local a favoritos', exact: true }).click();
  await clientStore.getByRole('button', { name: 'Quitar Agua local de favoritos', exact: true }).waitFor();
  await clientStore.getByRole('button', { name: 'Agregar', exact: true }).click();
  await clientStore.getByRole('button', { name: 'Aumentar cantidad de Agua local', exact: true }).click();
  assert.equal(await clientStore.getByLabel('Cantidad de Agua local en el carrito').inputValue(), '2');
  await clientStore.screenshot({ path: path.join(__dirname, 'tienda-cliente-movil.png'), fullPage: true, animations: 'disabled' });
  await clientStore.getByRole('button', { name: 'Limpiar carrito', exact: true }).click();
  await clientStore.getByText('Tu carrito está vacío.', { exact: true }).waitFor();
  assert(await clientStore.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await clientStore.close();

  const trainer = await open(currentUrl, cases.find(([n]) => n === 'rutinas'));
  await trainer.getByRole('button', { name: 'Crear nueva rutina', exact: true }).click();
  await trainer.getByPlaceholder('Ej. Hipertrofia Tren Superior').fill('Rutina de revisión');
  await trainer.getByRole('button', { name: 'Pierna', exact: true }).click();
  await trainer.getByRole('button', { name: 'Agregar Ejercicio', exact: true }).click();
  await trainer.getByPlaceholder('Ej. Press de Banca Plano').fill('Ejercicio de revisión');
  await trainer.screenshot({ path: path.join(__dirname, 'rutina-editor.png'), fullPage: true, animations: 'disabled' });
  await trainer.getByRole('button', { name: 'Guardar Rutina', exact: true }).click();
  await trainer.getByText('Rutina de revisión', { exact: true }).first().waitFor();
  assert(writes.some((w) => w.endpoint === '/trainer/rutinas' && w.payload.ejercicios.length === 1));
  await trainer.close();

  const promotions = await open(currentUrl, cases.find(([n]) => n === 'promociones'));
  await promotions.getByRole('button', { name: 'Nueva promoción', exact: true }).click();
  await promotions.getByPlaceholder('Ej. Promo Verano').fill('Promo de revisión');
  await promotions.locator('form').getByText('Mensual', { exact: true }).first().click();
  await promotions.screenshot({ path: path.join(__dirname, 'promocion-editor.png'), fullPage: true, animations: 'disabled' });
  await promotions.getByRole('button', { name: 'Guardar y Activar Regla', exact: true }).click();
  await promotions.getByText('¡Promoción Guardada!', { exact: true }).waitFor();
  assert(writes.some((w) => w.endpoint === '/promociones'));
  await promotions.close();
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(vueWarnings, []);
  results.sort((a, b) => cases.findIndex(([name]) => name === a.view) - cases.findIndex(([name]) => name === b.view));
  fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, pageErrors, vueWarnings,
    writes, screenshots: temporary, horizontalOverflow: false,
    source: 'Rutas reales con sesión y API sintéticas; InventoryMovementsView se monta en una ruta de revisión temporal.' }, null, 2));
  await browser.close();
  console.log('Vistas, formularios extraídos, filtros, favoritos y carrito verificados en navegador.');
})().catch((error) => { console.error(error); process.exit(1); });
