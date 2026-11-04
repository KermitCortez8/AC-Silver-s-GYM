/* Revisión de la demostración, no de la integración productiva del chatbot. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const base = process.env.PROTOTYPE_BASE_URL || 'http://127.0.0.1:8768/prototipos/index.html';
const output = path.join(__dirname, 'capturas');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}),
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'es-PE' });
  const errors = [], unexpectedNetwork = [], apiCalls = [], checks = [], captures = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (['fetch', 'xhr'].includes(request.resourceType())) apiCalls.push(request.url());
  });
  await page.route('**/*', route => {
    if (new URL(route.request().url()).origin !== new URL(base).origin) {
      unexpectedNetwork.push(route.request().url());
      return route.abort();
    }
    return route.continue();
  });
  const verify = async (name, fn) => { await fn(); checks.push({ name, result: 'aprobado' }); };
  const screen = async id => {
    await page.waitForFunction(code => document.querySelector('#screen-code').textContent === code, id);
  };
  const capture = async name => {
    await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
    captures.push(`${name}.png`);
  };
  const stageAction = name => page.locator(`#prototype-stage [data-action="${name}"]`).click();
  const chooseCase = name => page.locator(`[data-case="${name}"]`).click();
  try {
    await page.goto(base, { waitUntil: 'networkidle' });
    await verify('Specs y prototipo se muestran juntos', async () => {
      await screen('P01');
      assert.equal(await page.locator('#use-case-id').textContent(), 'CU-CHAT-01');
      assert.ok(await page.getByText('Prototipo · Datos simulados', { exact: true }).isVisible());
    });
    await capture('p01-planes-escritorio');
    await stageAction('register');
    await verify('Formulario separado y límites 50/8/9', async () => {
      await screen('P02');
      await page.locator('[name="nombre"]').fill('N'.repeat(60));
      assert.equal((await page.locator('[name="nombre"]').inputValue()).length, 50);
      await page.locator('[name="dni"]').fill('123456789');
      assert.equal((await page.locator('[name="dni"]').inputValue()).length, 8);
      await page.locator('[name="telefono"]').fill('9123456789');
      assert.equal((await page.locator('[name="telefono"]').inputValue()).length, 9);
      assert.equal(await page.locator('[name="correo"]').getAttribute('maxlength'), '50');
    });
    await verify('Mensaje máximo 150 sin contador visible', async () => {
      await page.locator('#message').fill('X'.repeat(151));
      assert.equal((await page.locator('#message').inputValue()).length, 150);
      assert.equal(await page.getByText('150 caracteres', { exact: true }).count(), 0);
      await page.locator('#message').fill('');
    });
    await stageAction('autofill');
    await capture('p02-preregistro-escritorio');
    await page.locator('#registration-form button[type="submit"]').click();
    await verify('Preregistro diferencia solicitud, pago y activación', async () => {
      await screen('P03');
      assert.ok(await page.getByText('Pendiente en esta demostración', { exact: true }).isVisible());
    });
    await capture('p03-solicitud-escritorio');
    await chooseCase('acceso');
    await capture('p04-acceso-escritorio');
    await page.selectOption('#scenario', 'pendiente');
    await page.locator('#login-form button[type="submit"]').click();
    await verify('Cuenta pendiente no abre el panel', async () => { await screen('P05'); });
    await capture('p05-activacion-pendiente-escritorio');
    await page.selectOption('#scenario', 'vencida');
    await page.locator('#login-form button[type="submit"]').click();
    await verify('Membresía vencida mantiene restricción de acceso', async () => {
      await screen('P05');
      assert.ok(await page.getByText('Consultar renovación', { exact: true }).isVisible());
    });
    await capture('p05-membresia-vencida-escritorio');
    await page.selectOption('#scenario', 'normal');
    await page.locator('#login-form button[type="submit"]').click();
    await verify('Ingreso simulado muestra panel propio', async () => { await screen('P06'); });
    await capture('p06-panel-escritorio');
    await stageAction('schedules');
    await verify('Sesión con servicio y fecha absoluta', async () => {
      await screen('P07');
      assert.equal(await page.locator('#class-date').inputValue(), '2026-11-05');
      assert.ok(await page.locator('.session-card').getByText('Funcional', { exact: true }).isVisible());
    });
    await capture('p07-horarios-escritorio');
    await stageAction('review');
    await verify('Un mensaje no confirma una matrícula', async () => {
      await screen('P08');
      await page.locator('#message').fill('Confirma mi matrícula');
      await page.locator('#chat-form button').click();
      await screen('P08');
      assert.ok(await page.locator('#messages').getByText(/Un mensaje de chat no confirma/).isVisible());
    });
    await capture('p08-confirmacion-escritorio');
    await page.locator('#prototype-stage [data-action="confirm"]').evaluate(button => { button.click(); button.click(); });
    await verify('Confirmación explícita y doble clic sin duplicado local', async () => {
      await screen('P09');
      assert.equal(await page.locator('.account-pill').count(), 1);
      assert.equal(await page.locator('#messages').getByText(/^Matrícula simulada completada\./).count(), 1);
    });
    await capture('p09-mi-horario-escritorio');
    await page.selectOption('#scenario', 'cupo');
    await stageAction('review');
    await stageAction('confirm');
    await verify('Cupo ocupado no muestra matrícula exitosa', async () => {
      await screen('P10');
      assert.ok(await page.getByText(/No se creó una matrícula\./).first().isVisible());
    });
    await capture('p10-cupo-agotado-escritorio');
    await page.selectOption('#scenario', 'incierto');
    await stageAction('review');
    await stageAction('confirm');
    await screen('P10');
    await capture('p10-resultado-incierto-escritorio');
    await stageAction('reconcile');
    await verify('Resultado incierto se reconcilia sin repetir envío', async () => { await screen('P09'); });
    await verify('Salir borra conversación y selección anteriores', async () => {
      await page.locator('#message').fill('MARCADOR de la conversación anterior');
      await page.locator('#chat-form button').click();
      await stageAction('logout');
      await screen('P04');
      assert.ok(!(await page.locator('#messages').textContent()).includes('MARCADOR'));
    });
    await page.selectOption('#scenario', 'sin-ia');
    await verify('Ayuda guiada disponible cuando la IA falla', async () => {
      assert.ok((await page.locator('#chat-status').textContent()).includes('Ayuda guiada'));
      assert.ok(await page.locator('#login-form').isVisible());
    });
    await capture('ayuda-guiada-escritorio');
    await page.setViewportSize({ width: 390, height: 844 });
    for (const [name, filename] of [['preregistro', 'p01-planes-movil'], ['acceso', 'p04-acceso-movil'], ['matricula', 'p07-horarios-movil']]) {
      await chooseCase(name);
      await verify(`Sin desbordamiento horizontal en móvil: ${name}`, async () => {
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      });
      await capture(filename);
    }
    await verify('Sin errores JavaScript ni peticiones de API/proveedores', async () => {
      assert.deepEqual(errors, []);
      assert.deepEqual(apiCalls, []);
      assert.deepEqual(unexpectedNetwork, []);
    });
    fs.writeFileSync(path.join(__dirname, 'resultados.json'), JSON.stringify({
      date: '2026-11-03', scope: 'Prototipo local; no integración productiva',
      desktop: '1440x1000', mobile: '390x844', checks, captures,
      errors, apiCalls, unexpectedNetwork,
    }, null, 2) + '\n');
    console.log(JSON.stringify({ passed: checks.length, captures: captures.length, errors: errors.length, apiCalls: apiCalls.length }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
