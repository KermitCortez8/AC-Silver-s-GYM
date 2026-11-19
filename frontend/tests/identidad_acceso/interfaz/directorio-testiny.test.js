import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

const employee = {
  id_usuario: 'SGSTA001', nombre: 'Personal QA', correo: 'personal@gmail.com',
  dni: '23456789', telefono: '987654321', rol: 'staff', estado: 'ACTIVO', hasPassword: true,
};

test('TC-006: alta interna valida sus campos y confirma un único usuario con un solo rol', async () => {
  const { setup, gym, dialogs } = await setupView('UsersView', '/admin/users', setup => setup.openNewUser());
  assert.match(dialogs, /Nuevo usuario/);
  assert.match(dialogs, /Entrenador/);
  const submissions = [];
  gym.upsertUser = async data => {
    submissions.push(data);
    gym.users = [employee];
    return employee;
  };
  await setup.handleSubmit();
  assert.equal(submissions.length, 0);
  assert.ok(setup.fieldErrors.nombre);
  Object.assign(setup.form, {
    nombre: employee.nombre, correo: employee.correo, dni: employee.dni, telefono: employee.telefono,
    rol: 'staff', password: 'qa-synthetic-password',
  });
  await Promise.all([setup.handleSubmit(), setup.handleSubmit()]);
  assert.deepEqual(submissions.map(item => item.rol), ['staff']);
  assert.equal(setup.feedbackTone, 'success');
  assert.equal(setup.isEditorOpen, false);
  assert.equal(gym.members.length, 0);
});

test('TC-007: consulta filtros y ficha de la identidad seleccionada sin revelar clave', async () => {
  const trainer = { ...employee, id_usuario: 'SGTRA001', nombre: 'Entrenador QA', rol: 'trainer' };
  const { setup, gym, html, dialogs } = await setupView('UsersView', '/admin/users', (setup, gym) => {
    gym.users = [trainer, employee];
    setup.roleFilter = 'staff';
    setup.search = 'Personal';
    setup.openDetails(employee);
  });
  assert.deepEqual(setup.filteredUsers.map(item => item.id_usuario), [employee.id_usuario]);
  assert.match(html, /Personal QA/);
  assert.match(dialogs, /personal@gmail.com/);
  assert.doesNotMatch(dialogs, /type="password"/);
  setup.closeDetails();
  assert.equal(setup.viewingUser, null);
  assert.deepEqual(gym.users.map(item => item.id_usuario), [trainer.id_usuario, employee.id_usuario]);
});

test('TC-008 y TC-009: cancelar descarta el borrador y la confirmación sin escribir', async () => {
  const { setup, gym } = await setupView('UsersView', '/admin/users', (_, gym) => {
    gym.users = [employee];
  });
  let writes = 0;
  gym.upsertUser = gym.deleteUser = async () => { writes++; };
  setup.editUser(employee);
  setup.form.nombre = 'Descartado';
  setup.form.rol = 'trainer';
  setup.closeEditor();
  setup.editUser(employee);
  assert.equal(setup.form.nombre, employee.nombre);
  assert.equal(setup.form.rol, 'staff');
  assert.equal(setup.form.password, '');
  const previous = globalThis.window;
  globalThis.window = { confirm: message => {
    assert.match(message, /SGSTA001/);
    return false;
  }};
  try { await setup.confirmDelete(employee); }
  finally {
    if (previous === undefined) delete globalThis.window;
    else globalThis.window = previous;
  }
  assert.equal(writes, 0);
  assert.deepEqual(gym.users, [employee]);
});
