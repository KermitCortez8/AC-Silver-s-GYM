import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

const plan = { id: '1', id_pm: 1, name: 'Pase semanal QA', duration: '7 días', price: 72,
  description: 'Entrenamiento QA', active: true };
const inactive = { ...plan, id: '2', id_pm: 2, name: 'Pase pausado QA', active: false };
const plansView = prepare => setupView('MembershipPlansView', '/admin/membership-plans', prepare);

test('TC-036: filtros muestran datos del plan elegido y el catálogo vacío es explícito', async () => {
  const { setup, html } = await plansView((setup, gym) => {
    gym.planCatalog = [plan, inactive];
    setup.status = 'active';
  });
  assert.match(html, /Pase semanal QA/);
  assert.match(html, /Entrenamiento QA/);
  assert.match(html, /7 días/);
  assert.match(html, /72/);
  assert.doesNotMatch(html, /Pase pausado QA/);
  setup.status = 'inactive';
  assert.deepEqual(setup.filteredPlans, [inactive]);
  setup.status = 'all';
  assert.deepEqual(setup.filteredPlans, [inactive, plan]);
  setup.editor = { showModal() {} };
  setup.editPlan(inactive);
  assert.equal(setup.form.id_pm, inactive.id_pm);
  assert.equal(setup.form.name, inactive.name);
  const empty = await plansView();
  assert.match(empty.html, /Tu catálogo empieza aquí/);
});

test('TC-035 y TC-039: formulario rechaza variantes inválidas, admite cero y recupera un fallo al guardar', async () => {
  const { setup, gym, html, dialogs } = await plansView();
  assert.match(html, /Nuevo plan/);
  assert.match(dialogs, /Descripción/);
  const saved = [];
  setup.editor = { showModal() {}, close() {} };
  gym.upsertPlan = async changes => {
    if (saved.length === 1) throw new Error('Guardado indisponible');
    saved.push(changes);
  };
  setup.newPlan();
  for (const changes of [{ name: '' }, { duration: '0 días' }, { price: -1 }, { price: '' }]) {
    Object.assign(setup.form, { ...plan, ...changes });
    await setup.savePlan();
    assert.ok(Object.keys(setup.fieldErrors).length);
  }
  assert.deepEqual(saved, []);
  Object.assign(setup.form, { ...plan, price: 0, duration: '1 año' });
  await setup.savePlan();
  assert.equal(saved[0].price, 0);
  setup.editPlan(plan);
  setup.form.price = 80;
  await setup.savePlan();
  assert.equal(setup.editorError, 'Guardado indisponible');
  assert.equal(setup.form.price, 80);
  assert.equal(saved[0].price, 0);
  gym.upsertPlan = async changes => { saved.push(changes); };
  await setup.savePlan();
  assert.equal(saved[1].price, 80);
});

test('TC-037 y TC-038: cancelar edición o borrado conserva los planes', async () => {
  const { setup, gym } = await plansView((_, gym) => { gym.planCatalog = [plan, inactive]; });
  let closed = false;
  setup.editor = { showModal() {}, close() { closed = true; } };
  setup.editPlan(plan);
  setup.form.name = 'Borrador';
  setup.closeEditor();
  assert.equal(closed, true);
  assert.equal(setup.plans[0].name, plan.name);
  let writes = 0;
  gym.deletePlan = async () => { writes++; };
  const previous = globalThis.window;
  globalThis.window = { confirm: message => {
    assert.match(message, /Pase semanal QA/);
    return false;
  }};
  try { await setup.removePlan(plan); }
  finally {
    if (previous === undefined) delete globalThis.window;
    else globalThis.window = previous;
  }
  assert.equal(writes, 0);
  assert.deepEqual(setup.plans, [plan, inactive]);
});
