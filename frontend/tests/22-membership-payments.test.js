import assert from 'node:assert/strict';
import { test } from 'node:test';
import { filterMembershipPayments, summarizeMembershipPayments } from '../src/utils/membershipPayments.js';
import { sectionForPath } from '../src/services/moduleNavigation.js';

const payments = [
  { id_membresia: 3, nombre: 'José Pérez', dni: '12345678', plan: 'MENSUAL', monto_pago: 69, estado_pago: 'PAGADO', metodo_pago: 'stripe', referencia_pago: 'cs_paid', fecha_pago: '2026-10-09' },
  { id_membresia: 2, nombre: 'José Pérez', monto_pago: 199, estado_pago: 'PENDIENTE', metodo_pago: 'stripe', fecha_pago: '' },
  { id_membresia: 1, nombre: 'Ana', monto_pago: 79, estado_pago: 'PAGADO', metodo_pago: 'efectivo', fecha_pago: '2026-09-30' },
  { id_membresia: 4, monto_pago: 999, estado_pago: 'SIN_REGISTRO' },
];

test('payment totals include only confirmed amounts and keep pending amounts separate', () => {
  assert.deepEqual(summarizeMembershipPayments(payments), {
    total: 4, paid: 2, collected: 148, pending: 1, outstanding: 199,
  });
});

test('payment search finds names without accents, DNI and Stripe references', () => {
  assert.equal(filterMembershipPayments(payments, { search: 'jose' }).length, 2);
  assert.equal(filterMembershipPayments(payments, { search: '12345678' })[0].id_membresia, 3);
  assert.equal(filterMembershipPayments(payments, { search: 'cs_paid' })[0].id_membresia, 3);
});

test('combined payment filters apply to the summary and keep dates inclusive', () => {
  const filtered = filterMembershipPayments(payments, {
    method: 'stripe', status: 'PAGADO', from: '2026-10-09', to: '2026-10-09',
  });
  assert.equal(filtered.length, 1);
  assert.equal(summarizeMembershipPayments(filtered).collected, 69);
  assert.equal(filterMembershipPayments(payments, { from: '2026-09-01' }).length, 2);
  assert.equal(filterMembershipPayments(payments, { status: 'PENDIENTE', to: '2026-10-09' }).length, 0);
});

test('payments and the previous configuration path select payment resources', () => {
  assert.equal(sectionForPath('/admin/payments'), 'payments');
  assert.equal(sectionForPath('/admin/settings'), 'payments');
});
