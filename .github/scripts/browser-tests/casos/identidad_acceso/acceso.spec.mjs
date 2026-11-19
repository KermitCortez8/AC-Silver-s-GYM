import { test, expect, login } from '../../fixtures.mjs';

test('El administrador inicia sesión y accede a su panel', {
  annotation: [
    { type: 'descripcion', description: 'Ingresar con la cuenta sintética mediante el formulario y la API real de autenticación.' },
    { type: 'esperado', description: 'La sesión es aceptada y el navegador muestra el panel administrativo.' },
  ],
}, async ({ page }) => {
  await test.step('Enviar correo y contraseña de la cuenta QA', () => login(page));
  await test.step('Comprobar navegación administrativa', async () => {
    await expect(page.getByRole('link', { name: /Inventario/i }).first()).toBeVisible();
  });
});

test('Una contraseña incorrecta muestra el rechazo sin iniciar sesión', {
  annotation: [
    { type: 'descripcion', description: 'Intentar el acceso con una contraseña incorrecta contra la API local.' },
    { type: 'esperado', description: 'El formulario muestra el error y permanece en login, sin sesión autenticada.' },
  ],
}, async ({ page }) => {
  await page.goto('/login');
  await test.step('Enviar credenciales incorrectas', async () => {
    await page.getByLabel('Correo', { exact: true }).fill('admin@example.test');
    await page.getByLabel('Contraseña', { exact: true }).fill('Incorrecta-2026!');
    await page.getByRole('button', { name: 'Entrar con correo', exact: true }).click();
  });
  await test.step('Comprobar el rechazo visible', async () => {
    await expect(page.getByRole('alert')).toContainText(/incorrectos/i);
    await expect(page).toHaveURL(/\/login/);
  });
});
