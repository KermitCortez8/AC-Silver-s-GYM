// Formularios y rutas reales; todas las API y cuentas se sustituyen por datos sintéticos.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-limits-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';
const output = __dirname;
const profile = { id: 'SGADM001', name: 'Administrador local', email: 'admin@example.com', role: 'admin' };
const plans = [{ id_pm: 1, nombre_plan: 'MENSUAL', duracion: '30 días', precio: 80, activo: true }];
const clients = [{ id_cliente: 1, id_usuario: 'SGCLI001', nombre: 'Ana local', correo: 'ana@example.com',
  dni: '01234567', telefono: '012345678', plan: 'MENSUAL', estado: 'EN_TRAMITE',
  membership_status: 'EN_TRAMITE', payment_status: 'PENDIENTE' }];
const results = [], errors = [], writes = [];
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, permissions: ['clipboard-read', 'clipboard-write'] });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(profile => {
      localStorage.setItem('gym_auth_user', JSON.stringify(profile));
      localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Date.now() / 1000 + 3600 }))}.local`);
      localStorage.setItem('ac-silver-theme', 'light');
      window.google = { accounts: { id: { initialize() {}, renderButton() {} } } };
    }, profile);
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (!url.pathname.startsWith('/api/')) return route.continue();
      const endpoint = url.pathname.slice(4);
      let data = [];
      const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Lima' }).format(new Date());
      const record = { id_asistencia: 1, version: 0, tipo: 'general', servicio: 'gimnasio',
        cliente_nombre: 'Ana local', cliente_dni: '01234567', fecha: today, hora_entrada: '09:00:00',
        hora_salida: '', estado: 'dentro', auditoria: [] };
      if (endpoint === '/auth/me') data = profile;
      else if (endpoint === '/clientes') data = clients;
      else if (endpoint === '/planes-membresia') data = plans;
      else if (endpoint === '/asistencia/resumen') data = { fecha: today, entradas: 1, salidas: 0, dentro: 1, capacidad: 30, disponibles: 29, pendientes: [record], recientes: [record] };
      else if (endpoint === '/asistencia/horarios') data = { horarios: [], fecha: today };
      else if (endpoint === '/asistencia/historial') data = { items: [record], total: 1, page: 1, page_size: 15 };
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON();
        writes.push({ endpoint, payload });
        if (endpoint === '/clientes') { Object.assign(clients[0], payload); data = clients[0]; }
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const navigate = async route => { await page.goto(base + route); await page.waitForLoadState('networkidle'); };
    const check = async (input, maximum, name, character = 'Á') => {
      await input.waitFor({ state: 'visible' });
      assert.equal(await input.getAttribute('maxlength'), String(maximum));
      await input.fill(character.repeat(maximum));
      await input.pressSequentially(character + character);
      assert.equal(await input.inputValue(), character.repeat(maximum));
      await input.fill('');
      await page.evaluate(value => navigator.clipboard.writeText(value), character.repeat(maximum + 10));
      await input.focus();
      await input.press('Control+V');
      assert.equal(await input.inputValue(), character.repeat(maximum));
      results.push({ field: name, maximum, typing: 'passed', paste: 'passed' });
    };
    const screenshot = filename => page.screenshot({ path: path.join(output, filename), fullPage: true });

    await navigate('/admin/clients');
    await page.getByTitle('Editar cliente', { exact: true }).first().click();
    let dialog = page.getByRole('dialog', { name: 'Editar cliente' });
    await check(dialog.locator('input').nth(0), 50, 'cliente.nombre');
    await check(dialog.locator('input[type=email]'), 50, 'cliente.correo', 'a');
    await dialog.locator('input[type=email]').fill('ana@example.com');
    await check(dialog.getByPlaceholder('999111222'), 9, 'cliente.telefono', '0');
    await check(dialog.getByPlaceholder('12345678'), 8, 'cliente.dni', '0');
    await dialog.getByPlaceholder('999111222').fill('01a234567');
    assert.equal(await dialog.getByPlaceholder('999111222').inputValue(), '01234567');
    await dialog.getByPlaceholder('999111222').fill('012345678');
    await screenshot('clientes.png');
    await dialog.getByRole('button', { name: 'Guardar cambios' }).click();
    await page.waitForFunction(() => !document.querySelector('dialog[open]'));
    assert.equal(writes.at(-1).payload.telefono, '012345678');
    assert.equal(writes.at(-1).payload.dni, '00000000');

    await navigate('/admin/users');
    await page.getByRole('button', { name: 'Nuevo usuario', exact: true }).click();
    dialog = page.getByRole('dialog', { name: 'Nuevo usuario' });
    await check(dialog.getByPlaceholder('Nombre y apellidos'), 50, 'usuario.nombre');
    await check(dialog.getByPlaceholder('999111222'), 9, 'usuario.telefono', '0');
    await check(dialog.getByPlaceholder('12345678'), 8, 'usuario.dni', '0');
    await screenshot('usuarios.png');

    await navigate('/admin/plans');
    await page.getByRole('button', { name: 'Nuevo plan', exact: true }).click();
    await check(page.getByPlaceholder('Nombre del plan'), 50, 'plan.nombre');
    await check(page.getByPlaceholder('Descripción visible para administración y clientes'), 150, 'plan.descripcion');
    await check(page.getByPlaceholder('Acceso, clases, evaluación, etc.'), 150, 'plan.beneficios');
    await screenshot('membresias.png');

    await navigate('/admin/promotions');
    await page.getByRole('button', { name: 'Nueva promoción', exact: true }).click();
    await check(page.getByPlaceholder('Ej. Promo Verano'), 50, 'promocion.nombre');
    await check(page.getByPlaceholder('Detalle o notas internas del descuento...'), 150, 'promocion.descripcion');
    await check(page.getByPlaceholder('Ej. NAVIDAD, VERANO, FLASH'), 50, 'promocion.palabra_clave', 'A');
    await screenshot('promociones.png');
    assert.equal(await page.locator('.card-preview span.truncate').evaluate(element => element.getBoundingClientRect().right <= element.closest('.card-preview').getBoundingClientRect().right), true);

    await navigate('/admin/service-schedules');
    await page.getByRole('button', { name: 'Nuevo horario', exact: true }).click();
    await check(page.getByPlaceholder('LUN', { exact: true }), 50, 'horario.codigo_dia', 'A');
    await screenshot('horarios.png');

    await navigate('/admin/attendance');
    await page.getByRole('tab', { name: 'Historial', exact: true }).click();
    await page.getByRole('button', { name: 'Corregir asistencia de Ana local' }).click();
    await check(page.getByPlaceholder('Explica qué ocurrió con este registro'), 150, 'asistencia.motivo');
    await screenshot('asistencia.png');

    await navigate('/admin/users');
    await check(page.locator('input[type=search]').first(), 50, 'busqueda.general');
    assert.equal(await page.locator('input[type=search]').first().getAttribute('title'), null);

    await context.clearCookies();
    await page.evaluate(() => { localStorage.removeItem('gym_auth_user'); localStorage.removeItem('gym_auth_token'); });
    // Página pública con sesión aislada: la misma política se aplica al registro.
    const publicPage = await browser.newPage({ viewport: { width: 390, height: 844 } });
    publicPage.on('pageerror', error => errors.push(error.message));
    await publicPage.addInitScript(() => { window.google = { accounts: { id: { initialize() {}, renderButton() {} } } }; });
    await publicPage.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (!url.pathname.startsWith('/api/')) return route.continue();
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(url.pathname.endsWith('/planes-membresia') ? plans : []) });
    });
    await publicPage.goto(base + '/registro');
    await publicPage.waitForLoadState('networkidle');
    assert.equal(await publicPage.locator('input[type=email]').getAttribute('maxlength'), '50');
    assert.equal(await publicPage.locator('input[autocomplete=tel]').getAttribute('maxlength'), '9');
    const publicPhone = publicPage.locator('input[autocomplete=tel]');
    await publicPhone.fill('012345678');
    await publicPhone.pressSequentially('90');
    assert.equal(await publicPhone.inputValue(), '012345678');
    const publicDni = publicPage.getByPlaceholder('12345678');
    await publicDni.fill('01234567');
    await publicDni.pressSequentially('89');
    assert.equal(await publicDni.inputValue(), '01234567');
    results.push({ field: 'registro.telefono_y_dni_movil', phone: 9, dni: 8, typing: 'passed' });
    await publicPage.screenshot({ path: path.join(output, 'registro-movil.png'), fullPage: true });
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify({ results, errors, writes }, null, 2));
    console.log(JSON.stringify({ passed: results.length, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
