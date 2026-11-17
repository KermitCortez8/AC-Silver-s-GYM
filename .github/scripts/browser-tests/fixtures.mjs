import { test as base, expect } from '@playwright/test';

export const test = base.extend({
  page: async ({ page, request }, use, testInfo) => {
    const reset = await request.post('http://127.0.0.1:8011/__qa/reset', {
      headers: { 'X-QA-Key': process.env.GYM_QA_KEY },
    });
    expect(reset.ok()).toBeTruthy();
    // Google es un proveedor doble explícito; esta suite valida acceso con correo.
    await page.addInitScript(() => {
      window.google = { accounts: { id: {
        initialize() {}, renderButton() {}, prompt() {}, disableAutoSelect() {},
      } } };
    });
    // Ningún recorrido de esta suite debe llamar a proveedores o producción.
    await page.route('**/*', route => {
      const url = new URL(route.request().url());
      return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort();
    });
    try {
      await use(page);
    } finally {
      if (!page.isClosed()) {
        const capture = testInfo.outputPath('resultado.png');
        await page.screenshot({ path: capture, fullPage: true, animations: 'disabled' });
        await testInfo.attach('Pantalla al terminar la prueba', { path: capture, contentType: 'image/png' });
      }
    }
  },
});
export { expect };

export async function login(page) {
  await page.goto('/login');
  await page.getByLabel('Correo', { exact: true }).fill('admin@example.test');
  await page.getByLabel('Contraseña', { exact: true }).fill('Prueba-Navegador-2026!');
  await page.getByRole('button', { name: 'Entrar con correo', exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/dashboard/);
}

export async function capture(page, testInfo, title) {
  const file = testInfo.outputPath(`paso-${testInfo.attachments.length}.png`);
  await page.screenshot({ path: file, fullPage: true, animations: 'disabled' });
  await testInfo.attach(title, { path: file, contentType: 'image/png' });
}
