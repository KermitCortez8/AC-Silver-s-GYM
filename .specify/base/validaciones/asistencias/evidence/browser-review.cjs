// Ejecutar desde la raíz con Vite local en 5173 y Playwright fuera del repositorio.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const dir = __dirname;
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const admin = { id: 'SGUSU001', id_usuario: 'SGUSU001', name: 'Administrador local',
    email: 'admin@example.test', role: 'admin' };
  await page.addInitScript((user) => {
    const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }));
    localStorage.setItem('gym_auth_token', `eyJhbGciOiJIUzI1NiJ9.${payload}.firma-local-simulada`);
    localStorage.setItem('gym_auth_user', JSON.stringify(user));
    localStorage.setItem('ac-silver-theme', 'dark');
  }, admin);
  let registered = false, expired = false, exited = false, entries = 0, exits = 0;
  const warning = 'Ya pasó más de una hora desde el término de la clase. La asistencia queda incompleta.';
  const schedule = { id_horario_servicio: 1, dia: 'jueves', hora_inicio: '10:00', hora_fin: '11:00',
    servicio: 'fitness', rutina_nombre: 'Fuerza general', hoy: true, matriculados: 2, activo: true };
  const other = { ...schedule, id_horario_servicio: 2, dia: 'viernes', hora_inicio: '16:00', hora_fin: '17:00',
    servicio: 'baile', rutina_nombre: 'Ritmos', hoy: false, matriculados: 1 };
  const record = () => ({ id_asistencia: 1, id_matricula: 7, tipo: 'horario', servicio: 'fitness',
    cliente_nombre: 'Ana Torres', cliente_dni: '11111111', fecha: '2026-10-29', hora_entrada: '10:30:00',
    hora_salida: exited ? '12:00:01' : '', estado: expired ? 'incompleta' : 'dentro', aviso: expired ? warning : '',
    limite_salida: '2026-10-29T12:00:00-05:00' });
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
    if (!url.pathname.startsWith('/api/')) return route.continue();
    let data = [];
    if (url.pathname.endsWith('/auth/me')) data = admin;
    else if (url.pathname.endsWith('/asistencia/resumen')) data = {
      fecha: '2026-10-29', entradas: registered ? 1 : 0, salidas: exited ? 1 : 0,
      dentro: registered && !exited ? 1 : 0, capacidad: 30, disponibles: 29,
      pendientes: registered && !exited ? [record()] : [], recientes: registered ? [record()] : [],
    };
    else if (url.pathname.endsWith('/asistencia/horarios')) data = { horarios: [schedule, other], fecha: '2026-10-29' };
    else if (url.pathname.endsWith('/horarios/1/clientes')) data = { horario: schedule, fecha: '2026-10-29', clientes: [
      { id_matricula: 7, cliente: { nombre: 'Ana Torres', dni: '11111111' }, puede_entrar: !registered,
        asistencia: registered ? record() : null, motivo: '' },
      { id_matricula: 8, cliente: { nombre: 'Luis Gómez', dni: '22222222' }, puede_entrar: false,
        asistencia: null, motivo: 'El cliente necesita una membresía activa, pagada y vigente.' },
    ] };
    else if (url.pathname.endsWith('/horarios/2/clientes')) data = { horario: other, fecha: '2026-10-29', clientes: [
      { id_matricula: 9, cliente: { nombre: 'María Pérez', dni: '33333333' }, puede_entrar: false,
        asistencia: null, motivo: 'Este horario no corresponde a hoy.' },
    ] };
    else if (url.pathname.endsWith('/asistencia/entrada')) { registered = true; entries++; data = record(); }
    else if (url.pathname.endsWith('/asistencia/salida')) { exited = true; exits++; data = record(); }
    else if (url.pathname.endsWith('/asistencia/historial')) data = { items: [record()], total: 1, page: 1, page_size: 15 };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
  });
  await page.goto('http://127.0.0.1:5173/admin/attendance');
  await page.getByRole('heading', { name: 'Selecciona una clase' }).waitFor();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'dark');
  await page.getByRole('button', { name: /Ver matriculados de Fitness/ }).click();
  await page.getByText('Ana Torres', { exact: true }).waitFor();
  assert(await page.getByRole('button', { name: 'Registrar entrada de Luis Gómez', exact: true }).isDisabled());
  await page.screenshot({ path: path.join(dir, 'tabla-clientes-escritorio.png'), fullPage: true });
  await page.getByRole('button', { name: 'Registrar entrada de Ana Torres', exact: true }).click();
  await page.getByRole('button', { name: 'Registrar salida de Ana Torres', exact: true }).first().waitFor();
  assert.equal(entries, 1);
  expired = true;
  await page.getByRole('button', { name: 'Actualizar', exact: true }).click();
  await page.getByText(warning, { exact: true }).first().waitFor();
  await page.screenshot({ path: path.join(dir, 'incompleta-escritorio-oscuro.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
  await page.screenshot({ path: path.join(dir, 'incompleta-movil-claro.png'), fullPage: true });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await page.getByRole('button', { name: 'Registrar salida de Ana Torres', exact: true }).first().click();
  await page.getByText('Salida registrada', { exact: true }).waitFor();
  assert.equal(exits, 1);
  assert(await page.getByText(warning, { exact: true }).count() > 0);
  await page.screenshot({ path: path.join(dir, 'salida-tardia-movil.png'), fullPage: true });
  await page.getByRole('button', { name: /Ver matriculados de Baile/ }).click();
  await page.getByText('María Pérez', { exact: true }).waitFor();
  assert(await page.getByRole('button', { name: 'Registrar entrada de María Pérez', exact: true }).isDisabled());
  await page.screenshot({ path: path.join(dir, 'otro-dia-movil.png'), fullPage: true });
  await page.getByRole('tab', { name: 'Historial', exact: true }).click();
  await page.getByRole('heading', { name: 'Historial de asistencia' }).waitFor();
  await page.getByText('Incompleta', { exact: true }).last().waitFor();
  await page.screenshot({ path: path.join(dir, 'historial-incompleta-movil.png'), fullPage: true });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(dir, 'browser-results.json'), JSON.stringify({ entries, exits, pageErrors: errors,
    horizontalOverflow: false, viewports: ['1440x1100', '390x844'], themes: ['dark', 'light'],
    source: 'Ruta real /admin/attendance; API y sesión simuladas localmente, sin proveedores externos.' }, null, 2));
  await browser.close();
  console.log('Tabla, selección, entrada, aviso, salida tardía e historial comprobados en navegador.');
})().catch((error) => { console.error(error); process.exit(1); });
