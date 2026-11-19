import assert from 'node:assert/strict';
import { test } from 'node:test';
import { movementSortKey, movementTime, signedQuantity } from '../../../src/domain/utils/inventoryMovements.js';

test('el traslado no altera el stock y se muestra con cantidad 0', () => {
  assert.equal(signedQuantity({ tipo_movimiento: 'entrada', cantidad: 3 }), '+3');
  assert.equal(signedQuantity({ tipo_movimiento: 'salida', cantidad: 2 }), '-2');
  assert.equal(signedQuantity({ tipo_movimiento: 'ajuste', cantidad: 8 }), '= 8');
  assert.equal(signedQuantity({ tipo_movimiento: 'traslado', cantidad: 1 }), '0');
});

test('la hora del movimiento se muestra en HH:MM y falta en filas antiguas', () => {
  assert.equal(movementTime({ hora_movimiento: '15:05:09' }), '15:05');
  assert.equal(movementTime({ hora_movimiento: null }), '');
  assert.equal(movementTime({}), '');
});

test('los movimientos del mismo día se ordenan por hora y luego por registro', () => {
  const rows = [
    { id_mov: 3, fecha_movimiento: '2026-11-17', hora_movimiento: '09:00:00' },
    { id_mov: 1, fecha_movimiento: '2026-11-17', hora_movimiento: '18:30:00' },
    { id_mov: 2, fecha_movimiento: '2026-11-16', hora_movimiento: '23:59:59' },
  ];
  const ordered = [...rows].sort((a, b) => movementSortKey(b).localeCompare(movementSortKey(a))).map((row) => row.id_mov);
  assert.deepEqual(ordered, [1, 3, 2]);
});
