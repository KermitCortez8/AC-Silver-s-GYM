// Revisión de textos con API y perfiles sintéticos, sin proveedores externos.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-attendance-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';
const cases = [
  ['landing', '/', '', ['Membresías', 'Ubicación', 'acompañe', 'musculación']],
  ['nosotros', '/nosotros', '', ['Misión', 'Visión', 'Por qué entrenar aquí', 'acompaña']],
  ['preguntas', '/preguntas-frecuentes', '', ['membresías', 'Ubicación']],
  ['registro', '/registro', '', ['Teléfono', 'Contraseña']],
  ['inventario', '/admin/inventory', 'admin', ['Gestión de inventario', 'Categoría', 'Ubicación', 'Artículo']],
  ['tienda', '/admin/store', 'admin', ['Catálogo', 'Sesión activa', 'Navegación']],
  ['carrito', '/user/store', 'user', ['Tu carrito está vacío.', 'Categoría', 'Catálogo']],
];
const pending = /\b(?:sesion|catalogo|membresias?|articulos?|descripcion|ubicacion|musculacion|informacion|navegacion|configuracion|imagenes|acompan[ae]|disenio|diseno)\b/iu;

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const errors = [], results = [];
  try {
    const check = async ([name, target, role, expected]) => {
      const page = await browser.newPage({ viewport: name === 'carrito' ? { width: 390, height: 844 } : { width: 1440, height: 1000 } });
      page.setDefaultTimeout(15000);
      await page.emulateMedia({ reducedMotion: 'reduce' });
      page.on('pageerror', (error) => errors.push(`${name}: ${error.message}`));
      const profile = { id: role === 'user' ? 'SGCLI001' : 'SGUSU001', name: 'Sesión local', email: 'local@example.test', role,
        id_cliente: role === 'user' ? 1 : null };
      await page.addInitScript(({ profile }) => {
        if (window.top !== window) return;
        localStorage.setItem('ac-silver-theme', 'light');
        if (profile.role) {
          localStorage.setItem('gym_auth_user', JSON.stringify(profile));
          localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.firma-local`);
        }
      }, { profile });
      await page.route('**/*', async (route) => {
        const url = new URL(route.request().url());
        if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
        if (!url.pathname.startsWith('/api/')) return route.continue();
        let data = [];
        if (url.pathname === '/api/auth/me') data = profile;
        else if (url.pathname === '/api/clientes/me') data = { id_cliente: 1, nombre: profile.name, estado: 'ACTIVO',
          membership_status: 'ACTIVA', payment_status: 'PAGADO', membership_end: '2027-12-31' };
        else if (url.pathname === '/api/gym/horarios-publicos') data = ['miercoles', 'sabado'].map((dia, i) => ({
          id_horario_servicio: i + 1, dia, servicio: 'musculacion', hora_inicio: '10:00', hora_fin: '11:00',
          rutina_nombre: 'Fuerza local', cupos: 10, activo: true,
        }));
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
      });
      await page.goto(base + target);
      await page.locator('h1:visible').first().waitFor().catch(async (error) => {
        throw new Error(`${name} en ${page.url()}: ${error.message}; errores: ${JSON.stringify(errors)}; texto: ${(await page.locator('body').innerText()).slice(0, 400)}`);
      });
      await page.waitForLoadState('networkidle');
      await page.locator('.module-loader-overlay').waitFor({ state: 'hidden' });
      const text = await page.locator('body').innerText();
      for (const label of expected) assert(text.toLocaleLowerCase('es').includes(label.toLocaleLowerCase('es')), `${name}: falta «${label}»`);
      assert(!pending.test(text), `${name}: texto pendiente: ${text.match(pending)?.[0]}`);

      if (name === 'landing') {
        await page.getByRole('heading', { name: 'Musculación', exact: true }).click();
        await page.getByText('Miércoles', { exact: true }).waitFor();
        await page.getByText('Sábado', { exact: true }).waitFor();
        await page.locator('.schedule-panel-enter-active').waitFor({ state: 'hidden' });
        await page.screenshot({ path: path.join(__dirname, 'landing-horarios.png'), fullPage: true, animations: 'disabled' });
      } else if (name === 'inventario') {
        await page.getByRole('button', { name: /Ingresar Nuevo Artículo/ }).click();
        await page.getByText('Información general', { exact: true }).first().waitFor();
        assert((await page.locator('body').innerText()).toLocaleLowerCase('es').includes('stock mínimo'));
        await page.waitForFunction(() => {
          const modal = document.querySelector('.rm-backdrop');
          return modal && getComputedStyle(modal).opacity === '1' && !modal.classList.contains('rm-fade-enter-active');
        });
        await page.screenshot({ path: path.join(__dirname, 'inventario-editor.png'), animations: 'disabled' });
      } else if (name === 'tienda') {
        await page.getByRole('button', { name: 'Ingresar Nuevo Artículo', exact: true }).click();
        await page.getByText('Ítem de inventario', { exact: true }).waitFor();
        assert((await page.locator('body').innerText()).toLocaleLowerCase('es').includes('información del producto'));
        await page.waitForFunction(() => {
          const modal = document.querySelector('.rm-backdrop');
          return modal && getComputedStyle(modal).opacity === '1' && !modal.classList.contains('rm-fade-enter-active');
        });
        await page.screenshot({ path: path.join(__dirname, 'tienda-editor.png'), animations: 'disabled' });
      } else if (['nosotros', 'carrito'].includes(name)) {
        await page.screenshot({ path: path.join(__dirname, `${name}.png`), fullPage: true, animations: 'disabled' });
      }
      results.push({ view: name, expected, correctedTextVisible: true });
      await page.close();
      console.log(`Ortografía verificada: ${name}`);
    };
    for (let i = 0; i < cases.length; i += 3) await Promise.all(cases.slice(i, i + 3).map(check));
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, pageErrors: errors,
      rawScheduleCodes: ['miercoles', 'sabado', 'musculacion'], visibleScheduleLabels: ['Miércoles', 'Sábado', 'Musculación'],
      source: 'Textos, rutas y formularios reales con API y sesiones sintéticas; recursos externos bloqueados.' }, null, 2) + '\n');
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
