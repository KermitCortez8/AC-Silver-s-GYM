import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

test('promotion saves reject duplicate clicks and retain the draft with an inline error', async () => {
  const { setup, gym } = await setupView('PromotionsView', '/admin/promotions');
  setup.openNewModal();
  setup.form.name = 'Verano';
  setup.form.appliesTo = ['pm-1'];
  let calls = 0;
  let reject;
  gym.upsertPromotion = () => { calls++; return new Promise((resolve, fail) => { reject = fail; }); };
  const pending = setup.save();
  await setup.save();
  setup.closeModal();
  assert.equal(calls, 1);
  assert.equal(setup.isModalOpen, true);
  reject(new Error('Sin conexión'));
  await pending;
  assert.equal(setup.modalError, 'Sin conexión');
  assert.equal(setup.form.name, 'Verano');
  assert.equal(setup.isModalOpen, true);
  assert.equal(setup.saving, false);
});

test('promotion deletion preserves its confirmation and target after failure', async () => {
  const { setup, gym } = await setupView('PromotionsView', '/admin/promotions');
  setup.requestDelete({ id_promocion: 1, name: 'Verano' });
  gym.deletePromotion = async () => { throw new Error('No se pudo eliminar'); };
  await setup.confirmDelete();
  assert.equal(setup.promoToDelete.id_promocion, 1);
  assert.equal(setup.deleteError, 'No se pudo eliminar');
  assert.equal(setup.deleting, false);
});
