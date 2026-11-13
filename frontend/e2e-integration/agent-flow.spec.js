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

test('flujo de privacidad: recuperar cuenta no envía datos personales', async ({ page }) => {
  const payloads = []
  page.on('request', request => {
    if (request.url().endsWith('/api/agente/mensajes')) payloads.push(request.postData() || '')
  })
  await openChat(page)

  await ask(page, 'quiero recuperar mi cuenta')
  await expect(page.getByLabel('Correo', { exact: true })).toBeVisible()
  await page.getByLabel('Correo', { exact: true }).fill('qa@example.com')
  await page.getByLabel('DNI', { exact: true }).fill('12345678')
  await page.getByLabel('Número telefónico').fill('900000001')
  await page.getByRole('button', { name: 'Dejar datos listos' }).click()
  await expect(page.getByRole('log')).toContainText('La solicitud aún no se ha enviado al gimnasio')
  expect(payloads).toHaveLength(1)
  expect(payloads[0]).toContain('quiero recuperar mi cuenta')
  expect(payloads[0]).not.toMatch(/qa@example\.com|12345678|900000001/)
})
