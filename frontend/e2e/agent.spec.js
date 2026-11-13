import { test, expect } from '@playwright/test';

async function setup(page, response) {
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.hostname !== '127.0.0.1') return route.abort();
    return route.continue();
  });
  await page.route('**/api/**', route => {
    if (route.request().url().endsWith('/agente/mensajes')) {
      return route.fulfill({
        status: response.status || 200,
        contentType: 'application/json',
        body: JSON.stringify(response.body),
      });
    }
    return route.fulfill({ status: 503, contentType: 'application/json', body: '{}' });
  });

  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir asistente del gimnasio' }).click();
}

async function ask(page, text) {
  await page.getByLabel('Tu pregunta para Silver').fill(text);
  await page.getByRole('button', { name: 'Enviar' }).click();
}

test('visitante pregunta por un plan y ve una respuesta del agente', async ({ page }) => {
  await setup(page, { body: {
    id_conversacion: 'synthetic-conversation', estado: 'respondida',
    texto: 'Planes disponibles: Mensual: S/ 80 · 30 días',
    enlaces: [{ texto: 'Ver registro', ruta: '/registro' }],
  } });
  await ask(page, '¿Cuánto cuesta el plan mensual?');
  await expect(page.getByRole('log')).toContainText('Mensual: S/ 80');
  await expect(page.getByRole('link', { name: 'Ver registro' })).toHaveAttribute('href', '/registro');
});

test('visitante pregunta por clases publicadas', async ({ page }) => {
  await setup(page, { body: {
    id_conversacion: 'synthetic-conversation', estado: 'respondida',
    texto: 'Clases publicadas: Spinning: Lunes 08:00–09:00',
    enlaces: [{ texto: 'Ver inicio', ruta: '/' }],
  } });
  await ask(page, '¿Cuándo hay spinning?');
  await expect(page.getByRole('log')).toContainText('Spinning: Lunes 08:00–09:00');
});

test('visitante pregunta por tipos de entrenamiento', async ({ page }) => {
  await setup(page, { body: {
    id_conversacion: 'synthetic-conversation', estado: 'respondida',
    texto: 'Tipos de entrenamiento:\n• Fitness: entrenamiento general.\n• Musculación: trabajo de fuerza.\n• Cardio: entrenamiento de resistencia.\n• Baile: clases grupales.',
    enlaces: [{ texto: 'Ver servicios', ruta: '/#servicios' }],
  } });
  await ask(page, '¿Qué tipo de ejercicios hay?');
  const reply = page.getByRole('log').locator('p').last();
  await expect(reply).toContainText('Tipos de entrenamiento:');
  await expect(reply).toHaveCSS('white-space', 'pre-wrap');
  expect(await reply.textContent()).toContain('\n• Musculación:');
  await expect(page.getByRole('link', { name: 'Ver servicios' })).toHaveAttribute('href', '/#servicios');
});

test('una lista larga desplaza el chat hasta el final', async ({ page }) => {
  await setup(page, { body: {
    id_conversacion: 'synthetic-conversation', estado: 'respondida',
    texto: `Clases publicadas:\n${Array.from({ length: 18 }, (_, index) => `• Clase ${index + 1}: Lunes 08:00–09:00`).join('\n')}`,
    enlaces: [],
  } });
  await ask(page, 'Dime los horarios de las clases');
  await expect(page.getByRole('log')).toContainText('Clase 18');
  await expect.poll(() => page.getByRole('log').evaluate(element => element.scrollTop)).toBeGreaterThan(0);
});

test('caída del proveedor muestra orientación y conserva la página', async ({ page }) => {
  await setup(page, { status: 503, body: { detail: 'No disponible' } });
  await ask(page, '¿Cuánto cuesta el plan?');
  await expect(page.getByRole('log')).toContainText('No pude consultar el servidor ahora');
  await expect(page.getByRole('button', { name: 'Cerrar asistente' })).toBeVisible();
  await page.getByRole('button', { name: 'Cerrar asistente' }).click();
  await expect(page.getByRole('button', { name: 'Abrir asistente del gimnasio' })).toBeVisible();
});

test('límite temporal muestra la causa sin afirmar que el tema es ajeno', async ({ page }) => {
  await setup(page, { status: 429, body: { detail: 'Límite temporal' } });
  await ask(page, 'Dime los horarios de las clases');
  await expect(page.getByRole('log')).toContainText('límite temporal de consultas');
  await expect(page.getByRole('log')).not.toContainText('No tengo datos confirmados');
});

test('operación privada se orienta a controles de la plataforma', async ({ page }) => {
  await setup(page, { body: {
    id_conversacion: 'synthetic-conversation', estado: 'fuera_de_alcance',
    texto: 'Esa gestión requiere usar los formularios y controles de la plataforma.',
    enlaces: [{ texto: 'Ir al acceso', ruta: '/login' }],
  } });
  await ask(page, 'Inscríbeme a spinning');
  await expect(page.getByRole('log')).toContainText('Esa gestión requiere');
  await expect(page.getByRole('link', { name: 'Ir al acceso' })).toHaveAttribute('href', '/login');
});
