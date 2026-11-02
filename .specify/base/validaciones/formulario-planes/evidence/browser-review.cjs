// Interacción con la vista real y API simulada, sin escrituras externas.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-limits-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const errors = [], writes = [], results = [];
  const profile = { id: 'SGADM001', name: 'Administrador local', email: 'admin@example.com', role: 'admin' };
  const plans = [{ id_pm: 1, nombre_plan: 'FLEXIBLE', duracion: '45 dias', precio: 0, activo: true, descripcion: 'Plan existente' }];
  let fail = false, releaseSave, holdSave = false;
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(profile => {
      localStorage.setItem('gym_auth_user', JSON.stringify(profile));
      localStorage.setItem('gym_auth_token', `e30.${btoa(JSON.stringify({ exp: Date.now() / 1000 + 3600 }))}.local`);
      localStorage.setItem('ac-silver-theme', 'light');
    }, profile);
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
      if (!url.pathname.startsWith('/api/')) return route.continue();
      let data = [], status = 200;
      if (url.pathname.endsWith('/auth/me')) data = profile;
      else if (url.pathname.endsWith('/planes-membresia')) data = plans;
      if (['POST', 'PUT'].includes(route.request().method()) && url.pathname.includes('/planes-membresia')) {
        const payload = route.request().postDataJSON();
        writes.push({ method: route.request().method(), payload });
        if (holdSave) await new Promise(resolve => { releaseSave = resolve; });
        if (fail) { status = 503; data = { detail: 'No se pudo guardar el plan de prueba.' }; }
        else {
          const saved = { ...payload, id_pm: payload.id_pm || plans.length + 1 };
          const index = plans.findIndex(plan => plan.id_pm === saved.id_pm);
          if (index === -1) plans.push(saved); else plans[index] = saved;
          data = saved;
        }
      }
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto(base + '/admin/plans');
    await page.waitForLoadState('networkidle');
    const dialog = page.getByRole('dialog', { name: 'Detalle del plan' });
    const duration = dialog.locator('select');
    const name = dialog.getByPlaceholder('Nombre del plan');
    const price = dialog.getByPlaceholder('0.00');
    const screenshot = filename => page.screenshot({ path: path.join(__dirname, filename), fullPage: true });

    await page.getByRole('button', { name: 'Nuevo plan', exact: true }).click();
    assert.equal(await duration.inputValue(), '30 días');
    assert.equal(await price.inputValue(), '');
    assert.equal(await dialog.locator('input[placeholder="30 días, 90 días..."]').count(), 0);
    assert.deepEqual(await duration.locator('option:not([disabled])').evaluateAll(options => options.map(option => option.value)), [
      '1 día', '7 días', '15 días', '30 días', '60 días', '90 días', '180 días', '365 días',
    ]);
    results.push('Duración seleccionable con ocho opciones y precio inicialmente vacío.');
    await screenshot('nuevo-plan.png');
    await dialog.getByRole('button', { name: 'Crear plan', exact: true }).click();
    await dialog.locator('#plan-name-error').waitFor();
    await dialog.locator('#plan-price-error').waitFor();
    assert.equal(await name.getAttribute('aria-invalid'), 'true');
    assert.equal(writes.length, 0);
    await screenshot('errores-campos.png');
    results.push('Campos obligatorios con errores asociados: no se envían escrituras inválidas.');

    await name.fill('Plan trimestral');
    await price.fill('79.90');
    await duration.selectOption('90 días');
    await dialog.getByPlaceholder('Descripción visible para administración y clientes').fill('Entrena durante 90 días.');
    await dialog.getByPlaceholder('Acceso, clases, evaluación, etc.').fill('Acceso al gimnasio y clases.');
    holdSave = true;
    const sending = page.waitForRequest(request => request.method() === 'POST' && request.url().endsWith('/planes-membresia'));
    await dialog.getByRole('button', { name: 'Crear plan', exact: true }).click();
    await sending;
    assert.equal(await dialog.locator('fieldset').evaluate(element => element.disabled), true);
    assert.equal(await name.isDisabled(), true);
    await dialog.locator('form').evaluate(form => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
    assert.equal(writes.length, 1);
    releaseSave(); holdSave = false;
    await dialog.waitFor({ state: 'hidden' });
    assert.equal(writes[0].payload.duracion, '90 días');
    assert.equal(writes[0].payload.precio, 79.90);
    results.push('Crear envía duración seleccionada y precio decimal; bloquea envíos duplicados.');

    await page.locator('article').filter({ has: page.getByRole('heading', { name: 'FLEXIBLE', exact: true }) }).getByRole('button', { name: 'Editar', exact: true }).click();
    assert.equal(await duration.inputValue(), '45 dias');
    assert.equal(await price.inputValue(), '0');
    await duration.selectOption('90 días');
    await duration.selectOption('45 dias');
    await screenshot('editar-duracion-actual.png');
    await dialog.getByRole('button', { name: 'Guardar cambios', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    assert.equal(writes.at(-1).payload.duracion, '45 dias');
    assert.equal(writes.at(-1).payload.precio, 0);
    results.push('La edición conserva la duración histórica y el precio cero.');

    await page.getByRole('button', { name: 'Nuevo plan', exact: true }).click();
    assert.equal(await duration.locator('option[value="45 dias"]').count(), 0);
    await name.fill('Plan anual');
    await duration.selectOption('365 días');
    await price.fill('500');
    fail = true;
    await dialog.getByRole('button', { name: 'Crear plan', exact: true }).click();
    await dialog.getByRole('alert').filter({ hasText: 'No se pudo guardar el plan de prueba.' }).waitFor();
    assert.equal(await name.inputValue(), 'Plan anual');
    assert.equal(await duration.inputValue(), '365 días');
    assert.equal(await price.inputValue(), '500');
    fail = false;
    await dialog.getByRole('button', { name: 'Crear plan', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    results.push('Un fallo del servidor conserva el borrador y permite reintentar.');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Nuevo plan', exact: true }).click();
    await duration.selectOption('30 días');
    assert.equal(await dialog.evaluate(element => element.scrollWidth <= element.clientWidth), true);
    await screenshot('nuevo-plan-movil.png');
    await page.evaluate(() => { document.documentElement.dataset.theme = 'dark'; document.documentElement.style.colorScheme = 'dark'; });
    await screenshot('nuevo-plan-oscuro.png');
    results.push('Formulario móvil sin desbordamiento horizontal; revisión de temas claro y oscuro.');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, writes, errors }, null, 2));
    console.log(JSON.stringify({ passed: results.length, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
