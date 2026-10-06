import assert from 'node:assert/strict';
import { test } from 'node:test';
import { canPayClientWithStripe } from '../src/utils/adminClientPayment.js';

test('only admin-created clients with an unpaid membership can pay from the panel', () => {
  const client = { registrationOrigin: 'ADMIN', paymentStatus: 'PENDIENTE', id_membresia: 34 };
  assert.equal(canPayClientWithStripe(client), true);
  for (const registrationOrigin of ['PUBLICO', '', undefined]) {
    assert.equal(canPayClientWithStripe({ ...client, registrationOrigin }), false);
  }
  assert.equal(canPayClientWithStripe({ ...client, paymentStatus: 'PAGADO' }), false);
  assert.equal(canPayClientWithStripe({ ...client, id_membresia: null }), false);
  assert.equal(canPayClientWithStripe(null), false);
});
