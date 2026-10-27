import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ref } from 'vue';
import { requireList, requireRecord } from '../src/application/services/responseValidation.js';
import { createSchedulesModule } from '../src/application/modules/schedules.js';

test('response identities accept positive safe integers and decimal digit strings', () => {
  for (const id of [1, 100, Number.MAX_SAFE_INTEGER, '1', '001', '100', String(Number.MAX_SAFE_INTEGER)]) {
    const row = { id };
    assert.equal(requireRecord(row, 'id'), row);
    assert.deepEqual(requireList([row], 'id'), [row]);
  }
});

test('response identities reject coercible containers and nondecimal formats', () => {
  for (const id of [[1], ['1'], { valueOf: () => 1 }, '1e2', '0x10', '0b10', '+1', ' 1 ', '1\n', '1.0']) {
    assert.throws(() => requireRecord({ id }, 'id'), /datos incompletos o inválidos/);
    assert.throws(() => requireList([{ id: 1 }, { id }], 'id'), /datos incompletos o inválidos/);
  }
});

test('response identities reject missing, fractional, nonpositive and unsafe values', () => {
  for (const id of [null, undefined, true, false, '', [], 0, '0', -1, '-1', 1.5,
    NaN, Infinity, Number.MAX_SAFE_INTEGER + 1, '9007199254740992']) {
    assert.throws(() => requireRecord({ id }, 'id'), /datos incompletos o inválidos/);
  }
});

test('malformed saved routine identities never replace the local catalog', async () => {
  const previous = [{ id_rutina: 1, nombre_rutina: 'Anterior' }];
  const ctx = { apiBase: '/api', authStore: { token: 'test' }, routines: ref([...previous]) };
  let id;
  const schedules = createSchedulesModule(ctx, {
    upsertRutina: async () => ({ id_rutina: id, nombre_rutina: 'Nueva' }),
  });
  for (id of [[1], ['1'], '1e2', '0x10']) {
    await assert.rejects(schedules.upsertRutina({ nombre_rutina: 'Nueva' }), /datos incompletos o inválidos/);
    assert.deepEqual(ctx.routines.value, previous);
  }
});
