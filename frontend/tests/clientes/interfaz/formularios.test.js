import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

test('client editor and membership actions preserve the actual view flow after extraction', async () => {
  const { setup, gym } = await setupView('ClientsView', '/admin/clients');
  const client = { id: 'SGCLI001', id_cliente: 1, name: 'Ana', email: 'ana@gmail.com', dni: '12345678', status: 'EN_TRAMITE', paymentStatus: 'PAGADO' };
  gym.members = [client];
  await setup.editClient(client);
  setup.form.nombre = 'Ana editada';
  let submitted;
  gym.upsertClient = async payload => { submitted = payload; return { ...client, name: payload.nombre }; };
  await setup.handleSubmit();
  assert.equal(submitted.nombre, 'Ana editada');
  assert.equal(submitted.id_usuario, 'SGCLI001');
  assert.equal(setup.isEditorOpen, false);
  assert.equal(setup.feedbackTone, 'success');
  setup.requestActivation(client);
  gym.activateClientMembership = async () => { throw new Error('No hay conexión'); };
  await setup.activateMembership(client);
  assert.equal(setup.pendingActivation.id, client.id);
  assert.equal(setup.activationError, 'No hay conexión');
  assert.equal(setup.activatingClientId, '');
  gym.activateClientMembership = async () => ({ ...client, notification: { status: 'queued' } });
  await setup.activateMembership(client);
  assert.equal(setup.pendingActivation, null);
  assert.match(setup.feedbackMessage, /pendiente de envío/);
});

test('extracted client dialogs render their real form and membership details', async () => {
  const { dialogs } = await setupView('ClientsView', '/admin/clients', (setup, gym) => {
    const client = { id: 'SGCLI001', id_cliente: 1, name: 'Ana editada', email: 'ana@example.com', plan: 'MENSUAL', status: 'EN_TRAMITE', paymentStatus: 'PAGADO' };
    gym.members = [client];
    setup.editClient(client);
    setup.openDetails(client);
  });
  assert.match(dialogs, /Ana editada/);
  assert.match(dialogs, /ana@example.com/);
  assert.match(dialogs, /Guardar cambios/);
  assert.match(dialogs, /Activar Membresía/);
});

test('public registration rejects invalid email inline before sending a request', async () => {
  const { setup, gym, html } = await setupView('RegisterView', '/registro', setup => {
    Object.assign(setup.form, { nombre: 'Ana', correo: 'ana@gmail.com.otro.org', dni: '12345678', telefono: '987654321', password: 'secreto123' });
    setup.validateField('correo');
  });
  let calls = 0;
  gym.registerPublicClient = async () => { calls++; };
  await setup.submitRegistration();
  assert.equal(calls, 0);
  assert.equal(setup.feedbackTone, 'error');
  assert.match(setup.feedback, /Solo se permiten correos/);
  assert.equal(setup.form.correo, 'ana@gmail.com.otro.org');
  assert.equal(setup.isSubmitting, false);
  assert.match(html, /aria-invalid="true"/);
  assert.match(html, /id="register-correo-error" role="alert"/);
});
