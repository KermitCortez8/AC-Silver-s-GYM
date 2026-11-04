// Sesiones y API sintéticas: no conecta con autenticación ni datos reales.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const errors = [], results = [];
  try {
    const check = async (role) => {
      const mobile = role === 'user';
      const page = await browser.newPage({ viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 } });
      page.setDefaultTimeout(15000);
      page.on('pageerror', (error) => errors.push(`${role}: ${error.message}`));
      let expired = false, passwordRequests = 0;
      const profile = { id: role === 'user' ? 'SGCLI001' : 'SGUSU001', name: 'Sesión local',
        email: 'local@example.test', role, id_cliente: role === 'user' ? 1 : null };
      const token = `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.firma-local`;
      const panel = ['admin', 'staff'].includes(role) ? '/admin/dashboard'
        : role === 'trainer' ? '/trainer/dashboard' : '/user/dashboard';
      await page.addInitScript(() => {
        if (window.top !== window) return;
        localStorage.setItem('ac-silver-theme', 'light');
        window.google = { accounts: { id: { initialize() {}, renderButton() {}, disableAutoSelect() {} } } };
      });
      await page.route('**/*', async (route) => {
        const url = new URL(route.request().url());
        if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
        if (!url.pathname.startsWith('/api/')) return route.continue();
        const endpoint = url.pathname.slice(4);
        let data = [], status = 200;
        if (endpoint === '/auth/password') {
          passwordRequests++;
          assert.equal(route.request().postDataJSON().correo, profile.email);
          data = { token, user: profile, expiresIn: 3600 };
        } else if (endpoint === '/auth/me') {
          data = expired ? { detail: { code: 'membership_expired', message: 'Membresía vencida' } } : profile;
          status = expired ? 403 : 200;
        } else if (endpoint === '/clientes/me') data = { id_cliente: 1, id_usuario: 'SGCLI001',
          nombre: profile.name, correo: profile.email, estado: 'ACTIVO', membership_status: 'ACTIVA',
          payment_status: 'PAGADO', membership_start: '2026-01-01', membership_end: '2027-12-31' };
        else if (endpoint === '/gym/resumen') data = {};
        else if (endpoint === '/gym/configuracion') data = { capacidad_total: 30, capacidad_por_hora: 10 };
        else if (endpoint === '/trainer/overview') data = { stats: {}, routines: [], schedule_monitor: [], routine_supervision: [] };
        await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
      });
      const hero = () => page.getByRole('heading', { name: /Entrena fuerte/ });
      const enter = () => page.locator('main').getByRole('link', { name: 'Acceso a plataforma digital', exact: true });

      // Recorrido real de contraseña y botón Atrás del navegador.
      await page.goto(base + '/');
      await hero().waitFor();
      await enter().click();
      await page.waitForURL(base + '/login');
      await page.getByPlaceholder('cliente@correo.com').fill(profile.email);
      await page.locator('input[autocomplete="current-password"]').fill('ClaveDePrueba123!');
      await page.getByRole('button', { name: 'Entrar con correo', exact: true }).click();
      await page.waitForURL(base + panel);
      await page.goBack();
      await page.waitForURL(base + '/');
      await hero().waitFor();
      assert(await page.evaluate(() => Boolean(localStorage.getItem('gym_auth_token'))));
      await page.screenshot({ path: path.join(__dirname, `landing-${role}.png`), fullPage: false, animations: 'disabled' });

      // Enlaces públicos con ancla, recarga y retorno explícito al panel.
      await page.evaluate(async () => {
        const { default: router } = await import('/src/presentation/router/index.js');
        await router.push('/#membresias');
      });
      await page.waitForURL(base + '/#membresias');
      await page.reload();
      await hero().waitFor();
      assert.equal(page.url(), base + '/#membresias');
      await enter().click();
      await page.waitForURL(base + panel);
      await page.goto(base + '/');
      await hero().waitFor();
      assert.equal(page.url(), base + '/');
      assert.equal(passwordRequests, 1);

      if (role === 'user') {
        // App.vue debe mantener la página pública si vence la sesión en segundo plano.
        expired = true;
        await page.evaluate(async () => {
          const { useAuthStore } = await import('/src/application/stores/authStore.js');
          await useAuthStore().initializeAuth({ force: true });
        });
        await page.waitForLoadState('networkidle');
        assert.equal(page.url(), base + '/');
        await hero().waitFor();
        assert.equal(await page.evaluate(() => localStorage.getItem('gym_auth_token')), null);
        await page.screenshot({ path: path.join(__dirname, 'landing-sesion-vencida.png'), animations: 'disabled' });
        await page.evaluate(async () => {
          const { default: router } = await import('/src/presentation/router/index.js');
          await router.push('/user/dashboard');
        });
        await page.waitForURL(base + '/login?reason=membership_expired');
        await page.getByText(/Tu membresía ha vencido y tu acceso está bloqueado/).waitFor();
        await page.goto(base + '/');
        await hero().waitFor();
        assert.equal(page.url(), base + '/');
      }
      results.push({ role, passwordLogin: true, backToLanding: true, sessionPreserved: true,
        hashAndReload: true, directLanding: true, explicitPanelReturn: true,
        publicPageAfterExpiration: role === 'user' ? true : null,
        privatePanelBlockedAfterExpiration: role === 'user' ? true : null });
      await page.close();
      console.log(`Navegación verificada: ${role}`);
    };
    await Promise.all(['admin', 'staff'].map(check));
    await Promise.all(['trainer', 'user'].map(check));
    assert.deepEqual(errors, []);
    results.sort((a, b) => a.role.localeCompare(b.role));
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, pageErrors: errors,
      source: 'Navegador con rutas, formulario y stores reales; autenticación y API simuladas.' }, null, 2) + '\n');
    console.log('Landing accesible antes y después de iniciar sesión; caducidad y paneles protegidos verificados.');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
