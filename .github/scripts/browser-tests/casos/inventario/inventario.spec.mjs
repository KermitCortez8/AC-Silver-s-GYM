import { test, expect, login, capture } from '../../fixtures.mjs';

async function createArticle(page, testInfo) {
  await login(page);
  await page.goto('/admin/inventory');
  await page.getByRole('button', { name: /Ingresar Nuevo Artículo/ }).click();
  await page.locator('#inv-name').fill('Escoba QA');
  await page.locator('#inv-category').selectOption({ label: 'Limpieza' });
  await page.locator('#inv-quantity').fill('10');
  await page.locator('#inv-min').fill('3');
  await capture(page, testInfo, 'Formulario de artículo con stock inicial 10');
  await page.getByRole('button', { name: 'Agregar artículo', exact: true }).click();
  await expect(page.getByRole('row').filter({ hasText: 'Escoba QA' })).toContainText('10');
}

test('El alta de artículo conserva stock 10 al recargar', {
  annotation: [
    { type: 'descripcion', description: 'Crear un artículo de limpieza desde la interfaz y volver a consultar el listado.' },
    { type: 'esperado', description: 'El artículo aparece con stock 10 antes y después de recargar; los datos se conservan en el repositorio QA.' },
  ],
}, async ({ page }, testInfo) => {
  await test.step('Completar y guardar un artículo con stock inicial 10', () => createArticle(page, testInfo));
  await test.step('Recargar y verificar el stock persistido', async () => {
    await page.reload();
    await expect(page.getByRole('row').filter({ hasText: 'Escoba QA' })).toContainText('10');
  });
});

test('Registrar salida de 3 deja stock 7 y conserva el movimiento', {
  annotation: [
    { type: 'descripcion', description: 'Crear stock 10, registrar una salida de 3 por el formulario y consultar nuevamente el inventario.' },
    { type: 'esperado', description: 'La salida queda registrada y el listado recargado muestra stock 7.' },
  ],
}, async ({ page }, testInfo) => {
  await test.step('Preparar el artículo desde la aplicación', () => createArticle(page, testInfo));
  await test.step('Registrar salida de tres unidades', async () => {
    await page.getByRole('button', { name: 'Movimientos', exact: true }).click();
    await page.getByRole('button', { name: /Registrar movimiento/i }).first().click();
    const dialog = page.getByRole('dialog');
    const article = dialog.getByRole('combobox', { name: /^Articulo/ });
    const value = await article.locator('option').filter({ hasText: 'Escoba QA' }).getAttribute('value');
    await article.selectOption(value);
    await dialog.getByText('Salida', { exact: true }).click();
    await expect(dialog.getByRole('radio', { name: 'Salida', exact: true })).toBeChecked();
    await dialog.getByRole('textbox', { name: /^Cantidad/ }).fill('3');
    await capture(page, testInfo, 'Salida de 3 con previsualización del saldo');
    await dialog.getByRole('button', { name: 'Registrar movimiento', exact: true }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.getByRole('row').filter({ hasText: 'Escoba QA' }).filter({ hasText: /salida/i })).toContainText('3');
  });
  await test.step('Consultar el saldo después de la salida', async () => {
    await page.goto('/admin/inventory');
    await expect(page.getByRole('row').filter({ hasText: 'Escoba QA' })).toContainText('7');
  });
});
