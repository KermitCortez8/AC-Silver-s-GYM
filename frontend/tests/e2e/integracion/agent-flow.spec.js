import { test, expect } from '@playwright/test'

async function openChat(page) {
  await page.route('**/*', route => {
    const url = new URL(route.request().url())
    return url.hostname === '127.0.0.1' ? route.continue() : route.abort()
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Abrir asistente del gimnasio' }).click()
}

async function ask(page, message) {
  await page.getByLabel('Tu pregunta para Silver').fill(message)
  await page.getByRole('button', { name: 'Enviar' }).click()
}

test('flujo público: visitante consulta plan y horario a través del backend', async ({ page }) => {
  const calls = []
  page.on('response', response => {
    if (response.url().endsWith('/api/agente/mensajes')) calls.push(response.status())
  })
  await openChat(page)

  await ask(page, '¿Cuánto cuesta el plan?')
  await expect(page.getByRole('log')).toContainText('Plan QA: S/ 91 · 31 días')
  await expect(page.getByRole('link', { name: 'Ver registro' })).toHaveAttribute('href', '/registro')

  await ask(page, '¿Qué horarios tiene baile?')
  await expect(page.getByRole('log')).toContainText('Baile:')
  await expect(page.getByRole('log')).toContainText('Lunes 07:00–08:00')
  expect(calls).toEqual([200, 200])
})

test('el diálogo del agente solicita el enlace a la ruta de autenticación', async ({ page }) => {
  const messages = []
  page.on('request', request => {
    if (request.url().endsWith('/api/agente/mensajes')) messages.push(request.postDataJSON())
  })
  await openChat(page)

  await ask(page, 'quiero recuperar mi cuenta')
  const dialog = page.getByRole('dialog', { name: 'Recuperar contraseña' })
  await dialog.getByRole('textbox', { name: 'Correo' }).fill('qa@example.com')
  const [response] = await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/api/auth/recuperar-contrasena')),
    dialog.getByRole('button', { name: 'Enviar enlace de recuperación' }).click(),
  ])
  expect(response.status()).toBe(202)
  expect(response.request().postDataJSON()).toEqual({ correo: 'qa@example.com' })
  await expect(dialog.getByRole('status')).toContainText('Si el correo está registrado, recibirás un enlace')
  await dialog.getByRole('button', { name: 'Entendido' }).click()
  await expect(page.getByRole('log')).not.toContainText('qa@example.com')
  expect(messages).toEqual([{ mensaje: 'quiero recuperar mi cuenta', id_conversacion: null }])
})
