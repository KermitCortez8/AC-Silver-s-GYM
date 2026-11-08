// Vista administrativa real con catálogo sintético y todas las API interceptadas.
const { chromium } = require(process.env.GYM_PLAYWRIGHT_MODULE || '/tmp/gym-limits-browser/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.GYM_FRONTEND_URL || 'http://127.0.0.1:5174';
const original = [
  { id_pm: 1, nombre_plan: 'MENSUAL', duracion: '30 días', precio: 80, activo: true, descripcion: 'Tu entrenamiento, a tu ritmo. Un mes para avanzar hacia tus objetivos.', beneficios: 'Acceso al gimnasio y clases grupales.' },
  { id_pm: 2, nombre_plan: 'TRIMESTRAL', duracion: '90 días', precio: 210, activo: true, descripcion: 'Más tiempo para construir el hábito y seguir progresando.', beneficios: 'Acceso completo, evaluación y seguimiento.' },
  { id_pm: 3, nombre_plan: 'ANUAL', duracion: '365 días', precio: 720, activo: false, descripcion: 'Un año de entrenamiento para acompañar cada una de tus metas.', beneficios: 'Gimnasio, clases y evaluaciones periódicas.' },
  { id_pm: 4, nombre_plan: 'ACTIVACIÓN', duracion: '1 día', precio: 0, activo: true, descripcion: 'Conoce el gimnasio y descubre tu próxima rutina.', beneficios: 'Una visita de prueba.' },
];
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const results = [], errors = [], mutations = [];
  let plans = structuredClone(original), loadFailure = false, deleteFailure = false;
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    page.setDefaultTimeout(15000);
    page.on('pageerror', error => errors.push(error.message));
    const profile = { id: 'SGADM001', name: 'Administrador local', email: 'admin@example.com', role: 'admin' };
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
      else if (url.pathname.endsWith('/planes-membresia')) {
        if (loadFailure) { status = 503; data = { detail: 'Servicio de planes temporalmente indisponible.' }; }
        else data = plans;
      }
      if (route.request().method() === 'DELETE') {
        mutations.push({ method: 'DELETE', path: url.pathname });
        if (deleteFailure) { status = 503; data = { detail: 'No se pudo eliminar el plan de prueba.' }; }
        else { plans = plans.filter(plan => plan.id_pm !== Number(url.pathname.split('/').at(-1))); return route.fulfill({ status: 204 }); }
      }
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const navigate = async () => { await page.goto(base + '/admin/plans'); await page.waitForLoadState('networkidle'); };
    const cards = page.locator('.plan-card');
    const screenshot = filename => page.screenshot({ path: path.join(__dirname, filename), fullPage: page.viewportSize().width > 640, animations: 'disabled' });
    await navigate();
    assert.equal(await cards.count(), 4);
    assert.equal(await page.getByRole('list', { name: 'Resumen de planes' }).locator('strong').allTextContents().then(values => values.join(',')), '4,3,1');
    await screenshot('catalogo-escritorio.png');
    results.push('Catálogo y resumen: cuatro planes, tres activos y uno inactivo.');

    await page.getByRole('searchbox', { name: 'Buscar planes' }).fill('evaluacion');
    assert.equal(await cards.count(), 2);
    await page.getByRole('group', { name: 'Filtrar planes por estado' }).getByRole('button', { name: /^Inactivos/ }).click();
    assert.equal(await cards.count(), 1);
    assert.equal(await cards.locator('h3').innerText(), 'ANUAL');
    await page.getByRole('button', { name: 'Limpiar filtros', exact: true }).click();
    assert.equal(await cards.count(), 4);
    await page.getByRole('combobox', { name: 'Ordenar planes' }).selectOption('price-asc');
    assert.equal(await cards.first().locator('h3').innerText(), 'ACTIVACIÓN');
    assert.match(await cards.first().locator('.plan-price p').innerText(), /0\.00/);
    await page.getByRole('combobox', { name: 'Ordenar planes' }).selectOption('price-desc');
    assert.equal(await cards.first().locator('h3').innerText(), 'ANUAL');
    results.push('Búsqueda sin tildes, filtros combinados y orden de precios que conserva cero.');

    await page.getByRole('searchbox', { name: 'Buscar planes' }).fill('sin coincidencias');
    await page.getByRole('heading', { name: 'No encontramos planes', exact: true }).waitFor();
    await screenshot('sin-resultados.png');
    await page.locator('.plan-empty').getByRole('button', { name: 'Limpiar filtros' }).click();
    await page.getByRole('button', { name: 'Cambiar a tema oscuro', exact: true }).click();
    await screenshot('catalogo-oscuro.png');
    await page.getByRole('button', { name: 'Cambiar a tema claro', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => scrollTo(0, 0));
    await screenshot('catalogo-movil.png');
    await cards.first().scrollIntoViewIfNeeded();
    await screenshot('tarjeta-movil.png');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    results.push('Estados sin coincidencias y revisión de escritorio, móvil y ambos temas.');

    page.on('dialog', dialog => dialog.accept());
    deleteFailure = true;
    await page.getByRole('button', { name: 'Eliminar ANUAL', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: 'No se pudo eliminar el plan de prueba.' }).waitFor();
    assert.equal(await cards.count(), 4);
    deleteFailure = false;
    await page.getByRole('button', { name: 'Eliminar ANUAL', exact: true }).click();
    await page.waitForFunction(() => document.querySelectorAll('.plan-card').length === 3);
    assert.equal(await cards.count(), 3);
    results.push('La eliminación fallida conserva la tarjeta y la confirmada actualiza el catálogo.');

    loadFailure = true;
    await navigate();
    await page.getByRole('alert').filter({ hasText: 'No se pudieron actualizar los planes.' }).waitFor();
    await screenshot('error-carga.png');
    loadFailure = false;
    await page.locator('.plan-load-error').getByRole('button', { name: 'Reintentar', exact: true }).click();
    await cards.first().waitFor();
    assert.equal(await cards.count(), 3);
    assert.equal(await page.getByRole('alert').count(), 0);
    results.push('El error de carga es visible y el reintento recupera el catálogo.');

    plans = [];
    await navigate();
    await page.getByRole('heading', { name: 'Tu catálogo empieza aquí' }).waitFor();
    await page.locator('.plan-empty').scrollIntoViewIfNeeded();
    await screenshot('catalogo-vacio.png');
    await page.getByRole('button', { name: 'Crear primer plan' }).click();
    await page.getByRole('dialog', { name: 'Detalle del plan' }).waitFor();
    assert.equal(await page.getByRole('dialog').locator('select').inputValue(), '30 días');
    await page.getByRole('dialog').getByRole('button', { name: 'Cerrar', exact: true }).click();
    results.push('El catálogo vacío ofrece crear un plan con el selector de duración.');

    plans = [{ ...original[0], nombre_plan: 'A'.repeat(50), descripcion: 'B'.repeat(150), beneficios: 'C'.repeat(150) }];
    await navigate();
    assert.equal(await cards.first().evaluate(element => element.scrollWidth <= element.clientWidth), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    results.push('Nombres y textos en el máximo permitido no desbordan la tarjeta móvil.');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'browser-results.json'), JSON.stringify({ results, mutations, errors }, null, 2));
    console.log(JSON.stringify({ passed: results.length, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
