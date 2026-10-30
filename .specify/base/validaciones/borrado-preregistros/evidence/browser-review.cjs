// Solo clientes sintéticos y HTTP interceptado; no contacta proveedores ni escribe en Supabase.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const errors = [], deletes = [], results = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => errors.push(error.message));
    const profile = { id: 'SGADM001', name: 'Personal local', email: 'personal@example.test', role: 'admin' };
    let clients = ['Preregistro público', 'Alta administrativa', 'Cliente con historial', 'Respuesta perdida'].map((nombre, i) => ({
      id_cliente: i + 1, id_usuario: `SGCLI00${i + 1}`, nombre, correo: `cliente${i + 1}@example.com`,
      dni: `1234567${i}`, telefono: '999111222', plan: 'MENSUAL', monto_pago: 80,
      origen_registro: i === 1 ? 'ADMIN' : 'PUBLICO', id_membresia: i + 1,
      estado: 'EN_TRAMITE', membership_status: 'EN_TRAMITE', payment_status: 'PENDIENTE',
    }));
    await page.addInitScript(profile => {
      if (window.top !== window) return;
      localStorage.setItem('ac-silver-theme', 'light');
      localStorage.setItem('gym_auth_user', JSON.stringify(profile));
      localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.firma-local`);
    }, profile);
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (!url.pathname.startsWith('/api/')) return route.continue();
      const endpoint = url.pathname.slice(4);
      if (endpoint === '/control204') return route.fulfill({ status: 204, body: '' });
      if (route.request().method() === 'DELETE') {
        const id = Number(endpoint.split('/').pop());
        deletes.push(id);
        if (id === 3) return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({
          detail: 'No se puede completar: el registro tiene historial relacionado (ventas o movimientos).',
        }) });
        clients = clients.filter(client => client.id_cliente !== id);
        if (id === 4) return route.abort('failed');
        return route.fulfill({ status: 204, body: '' });
      }
      assert.equal(route.request().method(), 'GET', 'Este recorrido solo autoriza lecturas y borrados simulados');
      let data = [];
      if (endpoint === '/auth/me') data = profile;
      else if (endpoint === '/clientes') data = clients;
      else if (endpoint === '/planes-membresia') data = [{ id_pm: 1, nombre_plan: 'MENSUAL', precio: 80, activo: true }];
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(base + '/admin/clients');
    await page.waitForLoadState('networkidle');
    await page.locator('.module-loader-overlay').waitFor({ state: 'hidden' });

    const protocol = await page.evaluate(async () => {
      const response = await fetch('/api/control204', { method: 'DELETE' });
      const bodyIsNull = response.body === null;
      let oldFailure = '';
      try { new Response(await response.arrayBuffer(), { status: response.status }); }
      catch (error) { oldFailure = error.name; }
      const { fetchWithTimeout } = await import('/src/infrastructure/services/httpTransport.js');
      const fixed = await fetchWithTimeout('/api/control204', { method: 'DELETE' });
      return { status: response.status, bodyIsNull, oldFailure, fixedStatus: fixed.status };
    });
    assert.equal(protocol.bodyIsNull, false, 'Reproduce el stream vacío de Chromium');
    assert.equal(protocol.oldFailure, 'TypeError');
    assert.equal(protocol.fixedStatus, 204);
    results.push({ scenario: 'Respuesta nativa de Chromium: error anterior y transporte corregido', ...protocol });
    await page.screenshot({ path: path.join(__dirname, 'antes.png'), fullPage: true });

    page.once('dialog', dialog => dialog.dismiss());
    await page.getByRole('button', { name: 'Eliminar a Preregistro público', exact: true }).click();
    assert.deepEqual(deletes, []);
    page.on('dialog', dialog => dialog.accept());
    for (const [id, nombre] of [[1, 'Preregistro público'], [2, 'Alta administrativa']]) {
      await page.getByRole('button', { name: `Eliminar a ${nombre}`, exact: true }).click();
      await page.getByRole('status').filter({ hasText: `Cliente SGCLI00${id} eliminado.` }).waitFor();
      assert.equal(await page.getByRole('button', { name: `Eliminar a ${nombre}`, exact: true }).count(), 0);
      assert.equal(deletes.filter(value => value === id).length, 1);
      results.push({ scenario: `Borrado confirmado de ${nombre}`, status: 'correcto', requests: 1 });
    }
    await page.screenshot({ path: path.join(__dirname, 'borrado-confirmado.png'), fullPage: true });

    await page.getByRole('button', { name: 'Eliminar a Cliente con historial', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'historial relacionado' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Eliminar a Cliente con historial', exact: true }).count(), 1);
    assert.equal(deletes.filter(id => id === 3).length, 1);
    results.push({ scenario: 'Un conflicto real conserva al cliente y muestra el motivo', status: 'correcto' });
    await page.screenshot({ path: path.join(__dirname, 'conflicto-real.png'), fullPage: true });

    await page.getByRole('button', { name: 'Eliminar a Respuesta perdida', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'No se pudo confirmar la operación' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Eliminar a Respuesta perdida', exact: true }).count(), 1);
    assert.equal(deletes.filter(id => id === 4).length, 1, 'Sin reintento automático de un borrado incierto');
    await page.getByRole('button', { name: 'Actualizar', exact: true }).click();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.getByRole('button', { name: 'Eliminar a Respuesta perdida', exact: true }).count(), 0);
    results.push({ scenario: 'Respuesta perdida: aviso, ningún reintento y recarga del resultado real', status: 'correcto' });
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, deletes, errors }, null, 2) + '\n');
    console.log(JSON.stringify({ scenarios: results.length, errors: errors.length, deletes }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
