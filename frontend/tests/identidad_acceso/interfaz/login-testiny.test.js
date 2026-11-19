import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

test('TC-003: el acceso vacío se valida en el formulario y permite corregirlo', async () => {
  const { setup, html } = await setupView('LoginView', '/login');
  assert.match(html, /Entrar con correo/);
  assert.match(html, /Google/);
  await setup.handlePasswordLogin();
  assert.match(setup.googleError, /correo/i);
  assert.equal(setup.processing, false);
  setup.passwordForm.correo = 'personal@gmail.com';
  await setup.handlePasswordLogin();
  assert.match(setup.googleError, /contraseña es obligatoria/i);
  assert.equal(setup.processing, false);
});

test('TC-186: inicio y acceso muestran los puntos de entrada públicos', async () => {
  const landing = await setupView('LandingView', '/');
  assert.match(landing.html, /Silver Gym Surco/);
  assert.match(landing.html, /href="\/login"/);
  const login = await setupView('LoginView', '/login');
  assert.match(login.html, /Entrar con correo/);
  assert.match(login.html, /Google/);
  assert.equal(login.setup.processing, false);
});
