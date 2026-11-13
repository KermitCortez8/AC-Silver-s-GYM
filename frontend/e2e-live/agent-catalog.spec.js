import { test, expect } from '@playwright/test'

test('horarios del chat coinciden con el catálogo público actual de Supabase', async ({ page }) => {
  await page.route('**/*', route => {
    const url = new URL(route.request().url())
    return url.hostname === '127.0.0.1' ? route.continue() : route.abort()
  })

  const response = await page.request.get('/api/gym/horarios-publicos')
  expect(response.ok()).toBe(true)
  const schedules = await response.json()
  expect(schedules.length).toBeGreaterThan(0)
  const sample = schedules[0]

  await page.goto('/')
  await page.getByRole('button', { name: 'Abrir asistente del gimnasio' }).click()
  await page.getByLabel('Tu pregunta para Silver').fill('Dime los horarios de todas las clases')
  await page.getByRole('button', { name: 'Enviar' }).click()

  const transcript = page.getByRole('log')
  await expect(transcript).toContainText('Horarios publicados por actividad:')
  await expect(transcript).toContainText(`${sample.hora_inicio}–${sample.hora_fin}`)
  const plain = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  expect(plain(await transcript.innerText())).toContain(plain(sample.servicio))
})
