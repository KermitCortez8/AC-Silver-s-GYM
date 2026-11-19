import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

const data = { nombre: 'Ana QA', correo: 'ana@gmail.com', telefono: '987654321', dni: '12345678', password: 'clave-qa-segura' };
const member = { id: 'SGCLI001', id_cliente: 1, name: data.nombre, dni: data.dni, phone: data.telefono,
  email: data.correo, plan: 'MENSUAL', status: 'EN_TRAMITE', paymentStatus: 'PAGADO', paymentAmount: 79 };

test('TC-013 y TC-014: el alta usa nombre completo y conserva el original ante DNI duplicado', async () => {
  const { setup, gym, dialogs } = await setupView('ClientsView', '/admin/clients', (setup, gym) => {
    gym.members = [member];
    setup.openNewClient();
  });
  assert.match(dialogs, />Nombre<\/span><input[^>]*placeholder="José Pérez"/);
  assert.doesNotMatch(dialogs, />Apellidos</);
  const submissions = [];
  gym.upsertClient = async payload => {
    submissions.push(payload);
    throw new Error('El DNI ya está registrado');
  };
  await setup.openNewClient();
  Object.assign(setup.form, data);
  await setup.handleSubmit();
  assert.match(setup.submitError, /DNI ya está registrado/);
  assert.equal(submissions[0].id_usuario, undefined);
  assert.equal(setup.editingId, '');
  setup.closeEditor();
  assert.equal(submissions.length, 1);
  assert.deepEqual(gym.members, [member]);
  await setup.openNewClient();
  Object.assign(setup.form, { ...data, dni: '87654321' });
  gym.upsertClient = async payload => {
    submissions.push(payload);
    return { ...member, id: 'SGCLI002', dni: payload.dni };
  };
  await setup.handleSubmit();
  assert.equal(submissions[1].dni, '87654321');
  assert.equal(setup.isEditorOpen, false);
});

test('TC-015: validación y fallo de guardado permiten reintentar con el borrador', async () => {
  const { setup, gym } = await setupView('ClientsView', '/admin/clients');
  let calls = 0;
  gym.upsertClient = async () => {
    calls++;
    if (calls === 1) throw new Error('No se pudo guardar');
    return member;
  };
  await setup.openNewClient();
  await setup.handleSubmit();
  assert.equal(calls, 0);
  assert.ok(setup.fieldErrors.nombre);
  Object.assign(setup.form, data);
  await setup.handleSubmit();
  assert.equal(setup.isEditorOpen, true);
  assert.match(setup.submitError, /No se pudo guardar/);
  assert.equal(gym.members.length, 0);
  await setup.handleSubmit();
  assert.equal(calls, 2);
  assert.equal(setup.isEditorOpen, false);
});

test('TC-016, TC-017 y TC-021: la ficha corresponde al cliente consultado y cancelar abandona solo el borrador', async () => {
  const { setup, gym, html, dialogs } = await setupView('ClientsView', '/admin/clients', (setup, gym) => {
    gym.members = [member];
    setup.openDetails(member);
  });
  for (const value of [member.name, member.dni, member.phone, member.email, member.plan]) {
    assert.ok((html + dialogs).includes(value), value);
  }
  assert.match(dialogs, /Pagado/i);
  setup.closeDetails();
  let writes = 0;
  gym.upsertClient = async () => { writes++; };
  await setup.editClient(member);
  setup.form.nombre = 'Borrador cancelado';
  setup.form.dni = '';
  await setup.handleSubmit();
  assert.equal(writes, 0);
  assert.ok(setup.fieldErrors.dni);
  setup.closeEditor();
  await setup.editClient(member);
  assert.equal(setup.form.nombre, member.name);
  assert.equal(setup.form.dni, member.dni);
  assert.deepEqual(gym.members, [member]);
});
