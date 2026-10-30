// Ruta real del cliente con respuestas de API sintéticas; no contacta proveedores.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.clock.install({ time: new Date('2026-10-29T15:30:00-05:00') });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const user = { id: 'SGCLI001', id_usuario: 'SGCLI001', id_cliente: 1,
    name: 'Ana Torres', email: 'ana@example.com', role: 'user' };
  await page.addInitScript((profile) => {
    localStorage.setItem('gym_auth_user', JSON.stringify(profile));
    localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.firma-local`);
    localStorage.setItem('ac-silver-theme', 'dark');
  }, user);
  const schedules = [{ id_horario_servicio: 1, servicio: 'fitness', dia: 'jueves',
    hora_inicio: '10:00', hora_fin: '11:00', cupos: 10, activo: true, rutina_nombre: 'Fuerza local' },
  { id_horario_servicio: 2, servicio: 'baile', dia: 'viernes', hora_inicio: '16:00',
    hora_fin: '17:00', cupos: 10, activo: true, rutina_nombre: 'Ritmos local' }];
  const enrollment = (id) => ({ ...schedules[id - 1], id_matricula: id,
    id_cliente: 1, estado: 'ACTIVA', fecha_matricula: '2026-10-01', asistencias: [] });
  let enrolled = [], reads = 0;
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
    if (!url.pathname.startsWith('/api/')) return route.continue();
    let data = [];
    if (url.pathname.endsWith('/auth/me')) data = user;
    else if (url.pathname.endsWith('/clientes/me')) data = { id_cliente: 1, id_usuario: 'SGCLI001',
      nombre: 'Ana Torres', correo: 'ana@example.com', dni: '11111111', estado: 'ACTIVO',
      estado_membresia: 'ACTIVA', estado_pago: 'PAGADO', fecha_fin: '2026-12-31' };
    else if (url.pathname.endsWith('/gym/horarios-servicio')) data = schedules;
    else if (url.pathname.endsWith('/gym/matriculas')) { reads++; data = enrolled; }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
  });
  const navigate = async (target) => {
    await page.evaluate(async (to) => {
      const { default: router } = await import('/src/presentation/router/index.js');
      await router.push(to);
    }, target);
  };
  await page.goto('http://127.0.0.1:5173/user/dashboard');
  await page.getByText(/Actualizado a las/).waitFor();
  await navigate('/user/schedule?fecha=2026-10-29');
  await page.getByText('Aún no hay clases agregadas a este horario.', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Actualizar', exact: true }).waitFor();
  enrolled = [enrollment(1)];
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await page.getByText('1 clase en el horario actual.', { exact: true }).waitFor();
  await page.locator('.fc-event').first().waitFor({ state: 'visible' });
  await page.screenshot({ path: path.join(__dirname, 'horario-actualizado-escritorio.png'), fullPage: true });
  await navigate('/user/dashboard');
  await page.getByText(/Actualizado a las/).waitFor();
  const firstReads = reads;
  // Regresa al panel antes de los 30 segundos de caché con una matrícula cambiada fuera de esta sesión.
  await navigate('/user/schedule?fecha=2026-10-29');
  await page.getByText('1 clase en el horario actual.', { exact: true }).waitFor();
  enrolled = [enrollment(1), enrollment(2)];
  await navigate('/user/dashboard');
  await page.getByText(/Actualizado a las/).waitFor();
  await page.waitForFunction(() => document.querySelectorAll('.fc-event').length === 2);
  assert(reads > firstReads);
  await navigate('/user/schedule?fecha=2026-10-29');
  await page.getByText('2 clases en el horario actual.', { exact: true }).waitFor();
  enrolled = [enrollment(2)];
  await page.clock.runFor(31000);
  await page.getByText('1 clase en el horario actual.', { exact: true }).waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
  await page.getByText('Ritmos local', { exact: true }).first().waitFor();
  await page.screenshot({ path: path.join(__dirname, 'horario-actualizado-movil.png'), fullPage: true });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  // Un error de lectura mantiene la última matrícula visible y muestra el error existente.
  await page.route('**/api/gym/matriculas*', (route) => route.fulfill({ status: 503,
    contentType: 'application/json', body: JSON.stringify({ detail: 'Consulta temporalmente no disponible.' }) }));
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await page.getByText('Consulta temporalmente no disponible.', { exact: true }).waitFor();
  await page.getByText('1 clase en el horario actual.', { exact: true }).waitFor();
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ reads,
    focusRefresh: true, periodicRefresh: true, freshDashboardNavigation: true,
    retainsLastScheduleOnError: true, horizontalOverflow: false, pageErrors: errors,
    viewports: ['1440x1000', '390x844'], api: 'Sintética local; sin proveedores externos.' }, null, 2));
  await browser.close();
  console.log('Cliente: matrícula añadida y cancelada, foco, intervalo, regreso al panel y fallo temporal verificados.');
})().catch((error) => { console.error(error); process.exit(1); });
