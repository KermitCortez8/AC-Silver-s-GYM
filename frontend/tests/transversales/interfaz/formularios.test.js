import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

test('client and user editors keep invalid drafts open and do not call the server', async () => {
  for (const [view, path, open, save] of [
    ['ClientsView', '/admin/clients', 'openNewClient', 'upsertClient'],
    ['UsersView', '/admin/users', 'openNewUser', 'upsertUser'],
  ]) {
    const { setup, gym } = await setupView(view, path);
    setup[open]();
    Object.assign(setup.form, { nombre: 'Ana', correo: 'ana@company.org', dni: 'bad', telefono: 'bad', password: '123' });
    let calls = 0;
    gym[save] = async () => { calls++; };
    await setup.handleSubmit();
    assert.equal(calls, 0);
    assert.equal(setup.isEditorOpen, true);
    assert.equal(setup.form.nombre, 'Ana');
    assert.equal(setup.feedbackTone, 'error');
    for (const field of ['correo', 'dni', 'telefono', 'password']) assert.ok(setup.fieldErrors[field]);
  }
});
