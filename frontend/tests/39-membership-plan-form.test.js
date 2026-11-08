import assert from 'node:assert/strict';
import { test } from 'node:test';
import { membershipPlanErrors, planDurationOptions } from '../src/domain/utils/membershipPlanForm.js';

test('las duraciones disponibles producen planes válidos sin texto libre', () => {
  const options = planDurationOptions();
  assert.deepEqual(options.map(option => option.value), [
    '1 día', '7 días', '15 días', '30 días', '60 días', '90 días', '180 días', '365 días',
  ]);
  for (const { value } of options) {
    assert.deepEqual(membershipPlanErrors({ name: 'Plan nuevo', duration: value, price: 80 }), {});
  }
});

test('las duraciones guardadas se conservan sin convertir meses, años o días', () => {
  for (const duration of ['45 dias', '1 mes', '1 año']) {
    const options = planDurationOptions(duration);
    assert.equal(options.filter(option => option.value === duration).length, 1);
    assert.deepEqual(membershipPlanErrors({ name: 'Plan existente', duration, price: 0 }), {});
  }
  assert.equal(planDurationOptions('30 días').filter(option => option.value === '30 días').length, 1);
  assert.equal(planDurationOptions().some(option => option.value === '45 dias'), false);
});

test('el formulario identifica los campos obligatorios y acepta un precio cero explícito', () => {
  assert.deepEqual(Object.keys(membershipPlanErrors({ name: '', duration: '30 días', price: '' })), ['name', 'price']);
  assert.deepEqual(membershipPlanErrors({ name: 'Acceso de prueba', duration: '1 día', price: 0 }), {});
  for (const price of [-1, '80.555', 'abc']) {
    assert.ok(membershipPlanErrors({ name: 'Plan', duration: '30 días', price }).price);
  }
});

test('el formulario rechaza una duración inválida y conserva el límite de nombre de 50', () => {
  const plan = { name: 'Á'.repeat(50), duration: '90 días', price: '79.90' };
  assert.deepEqual(membershipPlanErrors(plan), {});
  assert.ok(membershipPlanErrors({ ...plan, name: 'Á'.repeat(51) }).name);
  for (const duration of ['', 'mensual', '0 días', '-1 mes']) {
    assert.ok(membershipPlanErrors({ ...plan, duration }).duration);
  }
});
