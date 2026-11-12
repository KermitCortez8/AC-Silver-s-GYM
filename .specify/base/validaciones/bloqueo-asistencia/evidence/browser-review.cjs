// Interfaz real con sesiones y API sintéticas; no accede a cuentas ni escribe en Supabase.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-visual/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_REVIEW_URL || 'http://127.0.0.1:5173';
const output = __dirname;
const day = '2026-11-09';
const profile = { id: 'SGADM-VISUAL', id_usuario: 'SGADM-VISUAL', role: 'admin', name: 'Revisión visual', email: 'visual@example.com' };
const customer = { id_cliente: 999, nombre: 'Cliente de prueba', dni: '12345678', estado: 'ACTIVO', plan: 'MENSUAL' };
const schedule = { id_horario_servicio: 1, servicio: 'fitness', dia: 'lunes', hora_inicio: '10:00', hora_fin: '12:00',
  activo: true, cupos: 10, matriculados: 1, rutina_nombre: 'Clase de prueba', ocupacion_por_fecha: { [day]: 1 } };
const scenarios = [];
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    for (const mobile of [false, true]) for (const first of ['horario', 'general']) {
      const context = await browser.newContext({ viewport: { width: mobile ? 390 : 1440, height: mobile ? 844 : 1050 } });
      await context.addInitScript(({ profile, mobile }) => {
        localStorage.setItem('gym_auth_user', JSON.stringify(profile));
        localStorage.setItem('gym_auth_token', 'sesion-visual-simulada');
        localStorage.setItem('gym_auth_token_expiry', String(Date.now() + 3600000));
        localStorage.setItem('ac-silver-theme', mobile ? 'dark' : 'light');
      }, { profile, mobile });
      let open = { id_asistencia: 1, id_cliente_num: 999, id_matricula: first === 'horario' ? 7 : null,
        id_horario_servicio: first === 'horario' ? 1 : null, tipo: first, servicio: first === 'general' ? 'gimnasio' : 'fitness',
        estado: 'dentro', fecha: day, hora_entrada: '10:30:00', hora_salida: '', version: 1,
        cliente_nombre: customer.nombre, cliente_dni: customer.dni };
      let lastSchedule = first === 'horario' ? open : null;
      let exits = 0, entries = 0;
      const message = () => open ? `El cliente tiene una entrada sin salida en la asistencia ${open.tipo === 'general' ? 'general' : 'por horarios'}. Registra la salida de esa asistencia antes de registrar otra entrada.` : '';
      const roster = () => ({ horario: schedule, fecha: day, server_now: `${day}T10:40:00-05:00`, clientes: [{
        id_matricula: 7, cliente: customer, asistencia: lastSchedule, asistencia_abierta: open,
        puede_entrar: !open && !lastSchedule, motivo: message(),
      }] });
      await context.route('**/*', async route => {
        if (new URL(route.request().url()).origin !== new URL(base).origin) return route.abort();
        return route.fallback();
      });
      await context.route('**/api/**', async route => {
        const request = route.request(), pathname = new URL(request.url()).pathname;
        if (pathname === '/api/auth/me') return route.fulfill({ json: profile });
        if (pathname === '/api/asistencia/resumen') return route.fulfill({ json: { fecha: day,
          entradas: 1 + entries, salidas: exits, dentro: open ? 1 : 0, capacidad: 30,
          disponibles: open ? 29 : 30, pendientes: open ? [open] : [], recientes: [] } });
        if (pathname === '/api/asistencia/horarios') return route.fulfill({ json: { fecha: day, horarios: [schedule] } });
        if (pathname === '/api/asistencia/horarios/1/clientes') return route.fulfill({ json: roster() });
        if (pathname === '/api/asistencia/cliente') return route.fulfill({ json: { fecha: day, cliente: customer,
          membresia: { fecha_fin: '2026-12-09' }, horarios: [], general: {
            puede_entrar: !open, motivo: message(), asistencia_abierta: open } } });
        if (pathname === '/api/asistencia/salida') {
          assert.equal(request.postDataJSON().id_asistencia, 1);
          assert.ok(open, 'Debe cerrar la visita pendiente, sin duplicar salida');
          const closed = { ...open, hora_salida: '10:40:00', estado: 'completada' };
          if (open.tipo === 'horario') lastSchedule = closed;
          open = null; exits++;
          return route.fulfill({ json: closed });
        }
        if (['/api/asistencia/entrada', '/api/asistencia/general/entrada'].includes(pathname)) {
          if (open) return route.fulfill({ status: 409, json: { detail: message() } });
          entries++;
          open = { id_asistencia: 2, id_cliente_num: 999, tipo: pathname.includes('/general/') ? 'general' : 'horario',
            servicio: pathname.includes('/general/') ? 'gimnasio' : 'fitness', fecha: day, estado: 'dentro',
            hora_entrada: '10:41:00', hora_salida: '', cliente_nombre: customer.nombre, cliente_dni: customer.dni };
          if (open.tipo === 'horario') lastSchedule = open;
          return route.fulfill({ json: open });
        }
        if (pathname === '/api/asistencia/historial') return route.fulfill({ json: { items: [], total: 0 } });
        return route.fulfill({ json: [] });
      });
      const page = await context.newPage();
      const errors = []; page.on('pageerror', e => errors.push(e.message));
      await page.goto(`${base}/admin/attendance`);
      await page.waitForFunction(theme => document.documentElement.dataset.theme === theme, mobile ? 'dark' : 'light');
      let entry, exit;
      if (first === 'horario') {
        await page.getByRole('tab', { name: 'Gimnasio general', exact: true }).click();
        await page.getByLabel('DNI del cliente', { exact: true }).fill(customer.dni);
        await page.getByText('Entrada en asistencia por horarios', { exact: true }).waitFor();
        assert.equal(await page.getByRole('button', { name: 'Registrar entrada al gimnasio', exact: true }).count(), 0);
        exit = page.locator('.att-general-visit').getByRole('button', { name: 'Registrar salida', exact: true });
      } else {
        await page.getByRole('button', { name: /Clase de prueba/ }).first().click();
        entry = page.getByRole('button', { name: 'Registrar entrada de Cliente de prueba', exact: true });
        await entry.waitFor(); assert.equal(await entry.isDisabled(), true);
        exit = page.getByRole('button', { name: 'Registrar salida pendiente de Cliente de prueba', exact: true });
      }
      await page.getByText(message(), { exact: true }).first().waitFor();
      await exit.scrollIntoViewIfNeeded();
      const filename = `${first}-bloquea-${first === 'general' ? 'horario' : 'general'}-${mobile ? 'movil' : 'escritorio'}.png`;
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: path.join(output, filename), fullPage: true });
      assert.equal(entries, 0);
      await exit.click();
      if (first === 'horario') entry = page.getByRole('button', { name: 'Registrar entrada al gimnasio', exact: true });
      await entry.waitFor();
      await page.waitForFunction(() => [...document.querySelectorAll('button')].some(b =>
        /Registrar entrada/.test(b.textContent) && !b.disabled));
      assert.equal(await entry.isDisabled(), false);
      await entry.click();
      await page.waitForFunction(() => document.body.innerText.includes('Entrada registrada correctamente.') || document.body.innerText.includes('Entrada general registrada correctamente.'));
      assert.equal(exits, 1); assert.equal(entries, 1);
      assert.equal(open.tipo, first === 'horario' ? 'general' : 'horario');
      assert.deepEqual(errors, []);
      scenarios.push({ origen: first, destino: open.tipo, ancho: mobile ? 390 : 1440, tema: mobile ? 'oscuro' : 'claro', bloqueado_antes_de_salida: true,
        salidas: exits, entradas_nuevas: entries, errores: errors, captura: filename });
      await context.close();
    }
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify(scenarios, null, 2));
    console.log(JSON.stringify(scenarios, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exit(1); });
