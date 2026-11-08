// Rutas y formularios reales; catálogos, clientes y guardados sintéticos.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';
const plans = [
  { id_pm: 41, nombre_plan: 'PLAN MAÑANA', duracion: '45 días', precio: 100, activo: true },
  { id_pm: 52, nombre_plan: 'FIN DE SEMANA', duracion: '90 días', precio: 200, activo: true },
  { id_pm: 63, nombre_plan: 'RETIRADO', duracion: '30 días', precio: 50, activo: false },
];
const promotions = [
  { id_promocion: 8, nombre: 'Oferta actual', planes_aplicables: [41], tipo_descuento: 'porcentaje', valor_descuento: 20, activo: true },
  { id_promocion: 9, nombre: 'Oferta de fin de semana', planes_aplicables: [52], tipo_descuento: 'monto', valor_descuento: 30, activo: true },
  { id_promocion: 10, nombre: 'Oferta futura', fecha_inicio: '2999-01-01', activo: true, valor_descuento: 10 },
];
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const errors = [], results = [], writes = [];
  try {
    const open = async (admin) => {
      const page = await browser.newPage({ viewport: admin ? { width: 1440, height: 1100 } : { width: 390, height: 844 } });
      page.setDefaultTimeout(15000);
      await page.emulateMedia({ reducedMotion: 'reduce' });
      page.on('pageerror', e => errors.push(e.message));
      const state = { fail: false, empty: false, reads: [] };
      const profile = { id: 'SGUSU001', name: 'Personal local', email: 'local@example.test', role: 'admin' };
      const clients = [{ id_cliente: 1, id_usuario: 'SGCLI001', nombre: 'Ana local', correo: 'ana@example.com', dni: '12345678',
        telefono: '999111222', plan: 'PLAN MAÑANA', promocion: 'Oferta actual', id_promocion: 8,
        id_membresia: 1, monto_pago: 80, estado: 'EN_TRAMITE', membership_status: 'EN_TRAMITE', payment_status: 'PENDIENTE' }];
      await page.addInitScript(({ admin, profile }) => {
        if (window.top !== window) return;
        localStorage.setItem('ac-silver-theme', 'light');
        window.google = { accounts: { id: { initialize() {}, renderButton() {} } } };
        if (admin) {
          localStorage.setItem('gym_auth_user', JSON.stringify(profile));
          localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.firma-local`);
        }
      }, { admin, profile });
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
        if (!url.pathname.startsWith('/api/')) return route.continue();
        const endpoint = url.pathname.slice(4);
        let data = [], status = 200;
        state.reads.push(endpoint);
        if (endpoint === '/auth/me') data = profile;
        else if (endpoint === '/clientes') data = clients;
        else if (endpoint === '/planes-membresia') data = state.empty ? [] : plans;
        else if (endpoint.startsWith('/promociones')) {
          data = state.fail ? { detail: 'Catálogo temporalmente indisponible' } : promotions;
          status = state.fail ? 503 : 200;
        }
        if (route.request().method() === 'POST') {
          const payload = route.request().postDataJSON();
          writes.push({ endpoint, payload });
          if (endpoint === '/clientes') {
            Object.assign(clients[0], payload);
            data = clients[0];
          } else if (endpoint === '/clientes/registro-admin') {
            const created = { ...payload, id_cliente: 2, id_usuario: 'SGCLI002', estado: 'EN_TRAMITE' };
            clients.push(created);
            data = { cliente: created, membresia: { id_membresia: 2, id_promocion: payload.id_promocion,
              monto_pago: 80, estado: 'EN_TRAMITE', estado_pago: 'PENDIENTE' } };
          }
        }
        await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
      });
      await page.goto(base + (admin ? '/admin/clients' : '/registro'));
      await page.waitForLoadState('networkidle');
      return { page, state };
    };

    const { page: admin, state } = await open(true);
    const previousPlans = state.reads.filter(p => p === '/planes-membresia').length;
    await admin.getByTitle('Editar cliente', { exact: true }).first().click();
    const edit = admin.getByRole('dialog', { name: 'Editar cliente', exact: true });
    await edit.getByRole('button', { name: 'Guardar cambios', exact: true }).waitFor({ state: 'visible' });
    await admin.waitForLoadState('networkidle');
    assert(state.reads.filter(p => p === '/planes-membresia').length > previousPlans);
    assert((await edit.locator('select').first().locator('option').allTextContents()).some(t => t.includes('PLAN MAÑANA')));
    assert.equal(await edit.locator('select').nth(1).inputValue(), '8');
    assert(await edit.locator('select').first().isDisabled());
    assert((await edit.innerText()).includes('80.00'));
    await edit.screenshot({ path: path.join(__dirname, 'editar-cliente.png'), animations: 'disabled' });
    await edit.getByLabel('Nombre', { exact: true }).fill('Ana editada');
    await edit.getByRole('button', { name: 'Guardar cambios', exact: true }).click();
    await edit.waitFor({ state: 'hidden' });
    assert(writes.some(w => w.endpoint === '/clientes' && w.payload.promocion === 'Oferta actual' && w.payload.plan === 'PLAN MAÑANA'));
    results.push('Edición: nueva consulta, plan y promoción seleccionados, importe contratado y guardado personal conservados.');

    await admin.waitForLoadState('networkidle');
    state.fail = true;
    await admin.getByTitle('Editar cliente', { exact: true }).first().click();
    await edit.getByRole('button', { name: 'Reintentar carga', exact: true }).waitFor();
    await edit.getByLabel('Nombre', { exact: true }).fill('Borrador conservado');
    assert(await edit.getByRole('button', { name: 'Guardar cambios', exact: true }).isDisabled());
    await edit.screenshot({ path: path.join(__dirname, 'error-catalogo.png'), animations: 'disabled' });
    state.fail = false;
    await edit.getByRole('button', { name: 'Reintentar carga', exact: true }).click();
    await admin.waitForLoadState('networkidle');
    assert.equal(await edit.getByLabel('Nombre', { exact: true }).inputValue(), 'Borrador conservado');
    assert(await edit.getByRole('button', { name: 'Guardar cambios', exact: true }).isEnabled());
    await edit.getByRole('button', { name: 'Cerrar', exact: true }).click();
    results.push('Error y reintento: guardado bloqueado y borrador conservado.');

    await admin.getByRole('button', { name: 'Nuevo cliente', exact: true }).first().click();
    const create = admin.getByRole('dialog', { name: 'Nuevo cliente', exact: true });
    await admin.waitForLoadState('networkidle');
    await create.locator('select').first().selectOption('FIN DE SEMANA');
    await create.locator('select').nth(1).selectOption('9');
    await create.locator('select').first().selectOption('PLAN MAÑANA');
    assert.equal(await create.locator('select').nth(1).inputValue(), '0');
    await create.locator('select').nth(1).selectOption('8');
    assert((await create.innerText()).includes('80.00'));
    await create.getByLabel('Nombre', { exact: true }).fill('Cliente nuevo');
    await create.getByLabel('Correo', { exact: true }).fill('nuevo@example.com');
    await create.getByLabel('Contraseña', { exact: true }).fill('clave123');
    await create.getByLabel('DNI', { exact: true }).fill('87654321');
    await create.screenshot({ path: path.join(__dirname, 'nuevo-cliente.png'), animations: 'disabled' });
    await create.getByRole('button', { name: 'Registrar cliente', exact: true }).click();
    await create.waitFor({ state: 'hidden' });
    assert(writes.some(w => w.endpoint === '/clientes/registro-admin' && w.payload.id_promocion === 8 && w.payload.plan === 'PLAN MAÑANA'));
    results.push('Alta administrativa: planes personalizados, promociones por plan y payload correctos.');
    await admin.close();

    const { page: registration, state: publicState } = await open(false);
    await registration.getByText('Plan Mañana', { exact: true }).waitFor();
    assert(publicState.reads.includes('/planes-membresia') && publicState.reads.includes('/promociones/vigentes-publico'));
    assert((await registration.locator('body').innerText()).includes('S/ 80'));
    assert(!((await registration.locator('body').innerText()).includes('RETIRADO')));
    await registration.screenshot({ path: path.join(__dirname, 'registro-publico-movil.png'), fullPage: true, animations: 'disabled' });
    results.push('Registro público: catálogo remoto y promoción aplicable visibles en móvil.');
    publicState.fail = true;
    await registration.reload();
    await registration.getByRole('button', { name: 'Reintentar carga', exact: true }).waitFor();
    assert(await registration.getByRole('button', { name: 'Pagar con Stripe', exact: true }).isDisabled());
    publicState.fail = false;
    await registration.getByRole('button', { name: 'Reintentar carga', exact: true }).click();
    await registration.getByText('Plan Mañana', { exact: true }).waitFor();
    publicState.empty = true;
    await registration.reload();
    await registration.getByText('Planes pendientes de configuración.', { exact: true }).waitFor();
    assert(await registration.getByRole('button', { name: 'Pagar con Stripe', exact: true }).isDisabled());
    assert(!((await registration.locator('body').innerText()).includes('Plan Mañana')));
    results.push('Registro público vacío/fallido: sin planes locales; reintento y bloqueo del alta correctos.');
    await registration.close();
    assert.deepEqual(errors, []);
    const safeWrites = writes.map(({ endpoint, payload }) => ({ endpoint,
      payload: { ...payload, password: payload.password ? '[contraseña sintética omitida]' : '' },
    }));
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, pageErrors: errors, writes: safeWrites,
      source: 'Interfaz real con API y perfiles sintéticos; ningún guardado ni cobro real.' }, null, 2) + '\n');
    console.log('Modal de edición, alta administrativa, registro público, guardados y errores verificados.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
