// Vite en 5173; Playwright externo. Sesiones y API sintéticas, sin proveedores.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const appUrl = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5173';

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const errors = [], requests = [], creates = [], cancellations = [];
  const first = '2026-11-02', second = '2026-11-09';
  const schedule = { id_horario_servicio: 1, servicio: 'fitness', dia: 'lunes',
    hora_inicio: '10:00', hora_fin: '11:00', cupos: 5, activo: true, rutina_nombre: 'Fuerza por sesión' };
  const clients = [1, 2].map((id) => ({ id_cliente: id, id_usuario: `SGCLI00${id}`,
    nombre: id === 1 ? 'Ana Torres' : 'Luis Gómez', correo: `cliente${id}@example.test`,
    dni: String(id).repeat(8), estado: 'ACTIVO', estado_pago: 'PAGADO',
    estado_membresia: 'ACTIVA', fecha_fin: '2026-12-31' }));
  const enrollment = (id, client, fecha) => ({ ...schedule, id_matricula: id,
    id_cliente: client, fecha_clase: fecha, fecha_matricula: first, estado: 'ACTIVA', asistencias: [] });
  let enrollments = [enrollment(1, 1, first)], failRoster = false;
  const catalog = () => [{ ...schedule, cupos_usados: 1, ocupacion_por_fecha: Object.fromEntries(
    [first, second].map((fecha) => [fecha, enrollments.filter((e) => e.estado === 'ACTIVA' && e.fecha_clase === fecha).length])) }];
  const open = async (role, target) => {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    page.setDefaultTimeout(15000);
    await page.clock.install({ time: new Date('2026-11-02T10:30:00-05:00') });
    page.on('pageerror', (error) => errors.push(error.message));
    const user = role === 'user' ? { id: 'SGCLI001', id_usuario: 'SGCLI001', id_cliente: 1,
      name: 'Ana Torres', email: 'cliente1@example.test', role } : {
      id: 'SGADM001', id_usuario: 'SGADM001', name: 'Admin local', email: 'admin@example.test', role };
    await page.addInitScript((profile) => {
      localStorage.setItem('gym_auth_user', JSON.stringify(profile));
      localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now()/1000) + 3600 }))}.firma-local`);
      localStorage.setItem('ac-silver-theme', 'dark');
    }, user);
    await page.route('**/*', async (route) => {
      const request = route.request(), url = new URL(request.url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (!url.pathname.startsWith('/api/')) return route.continue();
      let data = [], status = 200;
      if (url.pathname.endsWith('/auth/me')) data = user;
      else if (url.pathname.endsWith('/clientes/me')) data = clients[0];
      else if (url.pathname === '/api/clientes') data = clients;
      else if (url.pathname.endsWith('/gym/horarios-servicio')) data = catalog();
      else if (url.pathname.endsWith('/gym/matriculas')) {
        if (request.method() === 'POST') {
          const body = request.postDataJSON();
          creates.push(body);
          assert.equal(body.fecha_clase, second);
          data = enrollment(2, body.id_cliente, body.fecha_clase);
          enrollments.push(data);
        } else data = enrollments.filter((e) => e.estado === 'ACTIVA' && (role !== 'user' || e.id_cliente === 1));
      } else if (url.pathname.endsWith('/gym/matriculas/2') && request.method() === 'DELETE') {
        cancellations.push(2);
        enrollments = enrollments.filter((e) => e.id_matricula !== 2);
      } else if (url.pathname.endsWith('/asistencia/resumen')) data = {
        fecha: first, entradas: 0, salidas: 0, dentro: 0, capacidad: 30, disponibles: 30, pendientes: [], recientes: [] };
      else if (url.pathname.endsWith('/asistencia/horarios')) data = { fecha: first, horarios: catalog() };
      else if (url.pathname.endsWith('/horarios/1/clientes')) {
        const fecha = url.searchParams.get('fecha');
        requests.push(fecha);
        if (failRoster) { status = 503; data = { detail: 'Consulta temporalmente no disponible.' }; }
        else data = { horario: schedule, fecha, clientes: enrollments.filter((e) => e.estado === 'ACTIVA' && e.fecha_clase === fecha)
          .map((e) => ({ id_matricula: e.id_matricula, cliente: clients.find((c) => c.id_cliente === e.id_cliente),
            asistencia: null, puede_entrar: fecha === first,
            motivo: fecha === first ? '' : 'La entrada se habilita el día de esta sesión (hora de Perú).' })) };
      }
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(`${appUrl}${target}`);
    return page;
  };
  const shot = (page, name) => page.screenshot({ path: path.join(__dirname, name), fullPage: true, animations: 'disabled' });
  const userPage = await open('user', `/user/schedule?fecha=${first}`);
  await userPage.getByText('1 clase en el horario actual.', { exact: true }).waitFor();
  await shot(userPage, 'matricula-semana-original.png');
  await userPage.getByRole('button', { name: /Semana 3/ }).click();
  await userPage.getByText('Aún no hay clases agregadas a este horario.', { exact: true }).waitFor();
  assert.equal(await userPage.locator('.fc-event').count(), 0);
  await userPage.getByRole('button', { name: 'Elegir horario', exact: true }).click();
  const picker = userPage.getByRole('dialog');
  await picker.getByRole('button', { name: /Fuerza por sesión.*Seleccionar horario/ }).click();
  await picker.getByRole('button', { name: 'Agregar a mi horario', exact: true }).click();
  await picker.getByRole('button', { name: 'Quitar de mi horario', exact: true }).waitFor();
  assert.equal(creates.length, 1);
  assert.equal(creates[0].fecha_clase, second);
  await picker.getByRole('button', { name: 'Quitar de mi horario', exact: true }).click();
  await picker.getByRole('button', { name: 'Agregar a mi horario', exact: true }).waitFor();
  await userPage.getByRole('button', { name: 'Cerrar selector de horario', exact: true }).click();
  assert.deepEqual(cancellations, [2]);
  assert.deepEqual(enrollments.map((e) => e.fecha_clase), [first]);
  await shot(userPage, 'matricula-otra-semana-vacia.png');
  await userPage.getByRole('button', { name: /Semana 2/ }).click();
  await userPage.getByText('1 clase en el horario actual.', { exact: true }).waitFor();

  enrollments.push(enrollment(3, 2, second));
  const adminPage = await open('admin', '/admin/attendance');
  await adminPage.getByRole('button', { name: /Fuerza por sesión.*Seleccionar horario/ }).click();
  await adminPage.locator('.att-roster').getByText('Ana Torres', { exact: true }).waitFor();
  assert.equal(await adminPage.locator('.att-roster').getByText('Luis Gómez', { exact: true }).count(), 0);
  await shot(adminPage, 'asistencia-fecha-original.png');
  await adminPage.getByRole('button', { name: /Semana 3/ }).click();
  await adminPage.getByText('Selecciona un horario para ver sus matriculados.', { exact: true }).waitFor();
  await adminPage.getByRole('button', { name: /Fuerza por sesión.*Seleccionar horario/ }).click();
  await adminPage.locator('.att-roster').getByText('Luis Gómez', { exact: true }).waitFor();
  assert.equal(await adminPage.locator('.att-roster').getByText('Ana Torres', { exact: true }).count(), 0);
  assert(await adminPage.getByRole('button', { name: 'Registrar entrada de Luis Gómez', exact: true }).isDisabled());
  await shot(adminPage, 'asistencia-otra-semana.png');
  await adminPage.setViewportSize({ width: 390, height: 844 });
  await adminPage.getByRole('button', { name: 'Cambiar a tema claro', exact: true }).click();
  await adminPage.locator('.agenda-event').waitFor();
  await adminPage.evaluate(() => scrollTo(0, 0));
  await shot(adminPage, 'asistencia-fecha-movil.png');
  assert(await adminPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  failRoster = true;
  await adminPage.locator('.agenda-event').click();
  await adminPage.getByRole('alert').filter({ hasText: 'Consulta temporalmente no disponible.' }).waitFor();
  assert.equal(await adminPage.locator('.att-roster').getByText('Luis Gómez', { exact: true }).count(), 0);
  assert(requests.includes(first) && requests.includes(second));
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ creates, cancellations,
    rosterDates: requests, pageErrors: errors, horizontalOverflow: false,
    checked: ['matrícula solo en su fecha', 'alta explícita de otra sesión', 'cancelación aislada',
      'lista distinta entre semanas', 'entrada futura bloqueada', 'fallo de consulta sin mostrar clientes anteriores'],
    api: 'Sintética local; reglas y RPC comprobadas por separado.' }, null, 2));
  await browser.close();
  console.log('Matrículas y asistencia separadas por fecha, cancelación y errores comprobados en navegador.');
})().catch((error) => { console.error(error); process.exit(1); });
