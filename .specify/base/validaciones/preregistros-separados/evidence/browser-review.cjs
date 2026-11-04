// Navegador y API real aislada en memoria; todas las URLs externas están bloqueadas.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const front = 'http://127.0.0.1:5174', api = 'http://127.0.0.1:8001';

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const results = [], errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      if (window.top !== window) return;
      localStorage.setItem('ac-silver-theme', 'light');
      window.google = { accounts: { id: { initialize() {}, renderButton() {} } } };
    });
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (url.pathname.startsWith('/api/')) {
        const response = await route.fetch({ url: api + url.pathname + url.search });
        return route.fulfill({ response });
      }
      return route.continue();
    });
    const counts = async () => (await page.request.get(api + '/control/counts')).json();
    const fill = async (suffix = '1') => {
      await page.getByLabel('Nombre completo', { exact: true }).fill('Cliente de prueba');
      await page.locator('input[type="email"]').fill(`solicitud${suffix}@example.com`);
      await page.getByLabel('Teléfono', { exact: true }).fill('999111222');
      await page.getByLabel('DNI', { exact: true }).fill(`1234567${suffix}`);
      await page.getByLabel('Contraseña', { exact: true }).fill('clave-local');
    };
    const submit = () => page.getByRole('button', { name: 'Pagar con Stripe', exact: true }).click();
    await page.request.post(api + '/control/reset');
    await page.request.post(api + '/control/fail/1');
    await page.goto(front + '/registro');
    await page.waitForLoadState('networkidle');
    await fill();
    await submit();
    await page.getByText('Solicitud pendiente de pago', { exact: true }).waitFor();
    assert.deepEqual(await counts(), { clients: 0, memberships: 0, pending: 1, expired: 0, sessions: 0 });
    assert.equal(await page.getByText(/Código: SGCLI/).count(), 0);
    await page.screenshot({ path: path.join(__dirname, 'solicitud-temporal.png'), fullPage: true });
    results.push('Fallo de checkout conserva solicitud y borrador sin crear cliente ni membresía');

    await page.request.post(api + '/control/fail/0');
    await submit();
    await page.waitForURL(api + '/checkout/**');
    const firstSession = page.url();
    await page.getByRole('link', { name: 'Abandonar pago' }).click();
    await page.getByRole('heading', { name: 'El pago no se completó' }).waitFor();
    assert.match(await page.locator('main').innerText(), /Solicitud [0-9a-f]{8}/);
    assert.equal((await counts()).clients, 0);
    await page.screenshot({ path: path.join(__dirname, 'checkout-interrumpido.png'), fullPage: true });
    results.push('Abandonar checkout muestra solicitud temporal, sin código ficticio ni cliente');

    await page.getByRole('link', { name: 'Intentar nuevamente', exact: true }).click();
    await page.waitForLoadState('networkidle');
    await fill();
    await submit();
    await page.waitForURL(api + '/checkout/**');
    assert.equal(page.url(), firstSession);
    assert.equal((await counts()).sessions, 1);
    await page.getByRole('button', { name: 'Simular pago aprobado' }).click();
    await page.waitForURL(front + '/registro/pago/**');
    await page.getByRole('heading', { name: 'Pago confirmado', exact: true }).waitFor();
    assert.match(await page.locator('main').innerText(), /SGCLI001/);
    assert.deepEqual(await counts(), { clients: 1, memberships: 1, pending: 0, expired: 0, sessions: 1 });
    await page.screenshot({ path: path.join(__dirname, 'pago-confirmado.png'), fullPage: true });
    results.push('Reintento reutiliza checkout; webhook y retorno crean un solo cliente pagado pendiente de activación');

    await page.goto(front + '/registro');
    await page.waitForLoadState('networkidle');
    await fill('2');
    await submit();
    await page.waitForURL(api + '/checkout/**');
    await page.request.post(api + '/control/archive');
    assert.deepEqual(await counts(), { clients: 1, memberships: 1, pending: 0, expired: 1, sessions: 2 });
    results.push('Caducidad archiva la solicitud impaga y conserva el cliente pagado');

    await page.goto(front + '/');
    await page.evaluate(() => {
      localStorage.setItem('gym_auth_user', JSON.stringify({ id: 'SGADM001', name: 'Personal local', email: 'local@example.test', role: 'admin' }));
      localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.firma-local`);
    });
    await page.goto(front + '/admin/clients');
    await page.waitForLoadState('networkidle');
    await page.locator('.module-loader-overlay').waitFor({ state: 'hidden' });
    assert.equal(await page.getByRole('button', { name: 'Eliminar a Cliente de prueba', exact: true }).count(), 1);
    assert.equal(await page.locator('tbody').getByText('Pagado', { exact: true }).count(), 1);
    await page.screenshot({ path: path.join(__dirname, 'directorio-tras-pago.png'), fullPage: true });
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, counts: await counts(), errors }, null, 2) + '\n');
    console.log(JSON.stringify({ scenarios: results.length, errors: errors.length }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
