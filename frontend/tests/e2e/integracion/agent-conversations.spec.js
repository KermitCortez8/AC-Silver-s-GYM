import { test, expect } from '@playwright/test'

async function openChat(page) {
  await page.route('**/*', route => {
    const url = new URL(route.request().url())
    return url.hostname === '127.0.0.1' ? route.continue() : route.abort()
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Abrir asistente del gimnasio' }).click()
}

async function ask(page, message, expected) {
  await page.getByLabel('Tu pregunta para Silver').fill(message)
  await page.getByRole('button', { name: 'Enviar' }).click()
  const reply = page.getByRole('log').locator('p').last()
  await expect(reply).toContainText(expected)
  return reply
}

test('CONV-01: del saludo al registro sin ejecutar inscripción', async ({ page }) => {
  const payloads = []
  page.on('request', request => {
    if (request.url().endsWith('/api/agente/mensajes')) payloads.push(request.postDataJSON())
  })
  await openChat(page)

  await ask(page, 'Hola', 'Soy Silver')
  await ask(page, '¿Cuánto cuesta el plan?', 'Plan QA: S/ 91 · 31 días')
  await ask(page, '¿Qué horarios tiene Baile?', 'Lunes 07:00–08:00')
  await ask(page, '¿Cómo me registro?', 'Abre la página de Registro')
  await expect(page.getByRole('link', { name: 'Ir al registro' })).toHaveAttribute('href', '/registro')
  await ask(page, 'Inscríbeme a Baile', 'requiere usar los formularios')
  await ask(page, 'Gracias', 'De nada')

  expect(payloads).toHaveLength(6)
  expect(payloads[0].id_conversacion).toBeNull()
  const identifier = payloads[1].id_conversacion
  expect(identifier).toBeTruthy()
  for (const payload of payloads.slice(1)) expect(payload.id_conversacion).toBe(identifier)
})

test('CONV-02: actividad, seguimiento y pregunta de cupos sin inventar disponibilidad', async ({ page }) => {
  await openChat(page)
  await ask(page, '¿Qué tipos de ejercicios hay?', 'Tipos de entrenamiento')
  await ask(page, '¿Y los horarios?', 'Lunes 07:00–08:00')
  const reply = await ask(page, '¿Hay cupo en Baile el lunes?', 'cupos limitados')
  const text = (await reply.innerText()).toLowerCase()
  expect(text).not.toContain('hay espacio')
  expect(text).not.toContain('está lleno')
})

test('CONV-03: datos de recuperación permanecen en el navegador', async ({ page }) => {
  const payloads = []
  page.on('request', request => {
    if (request.url().endsWith('/api/agente/mensajes')) payloads.push(request.postData() || '')
  })
  await openChat(page)
  await ask(page, 'Quiero recuperar mi cuenta', 'Completa tu correo, DNI y número telefónico')
  await page.getByLabel('Correo', { exact: true }).fill('qa@example.com')
  await page.getByLabel('DNI', { exact: true }).fill('12345678')
  await page.getByLabel('Número telefónico').fill('900000001')
  await page.getByRole('button', { name: 'Dejar datos listos' }).click()
  await expect(page.getByRole('log')).toContainText('La solicitud aún no se ha enviado al gimnasio')

  await ask(page, 'qa@example.com', 'no escribas datos personales')
  expect(payloads).toHaveLength(1)
  expect(payloads[0]).toContain('Quiero recuperar mi cuenta')
  expect(payloads[0]).not.toMatch(/qa@example\.com|12345678|900000001/)
  await expect(page.getByRole('log')).not.toContainText('qa@example.com')
})

test('CONV-04: redirige tema ajeno y vuelve a consultar un plan', async ({ page }) => {
  await openChat(page)
  await ask(page, 'Quisiera saber algo', 'Cuéntame un poco más')
  await ask(page, '¿Dónde está One Piece?', 'se aleja un poco del gimnasio')
  await ask(page, '¿Dónde está One Piece?', 'centrémonos en Silver Gym')
  await ask(page, '¿Cuánto cuesta el plan?', 'Plan QA: S/ 91')
})
