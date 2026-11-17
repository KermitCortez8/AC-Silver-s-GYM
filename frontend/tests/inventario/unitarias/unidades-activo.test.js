import assert from 'node:assert/strict';
import { test } from 'node:test';
import { isActiveUnit, isUnitCategory, unitPrefix } from '../../../src/domain/utils/inventoryUnits.js';

test('el prefijo usa las iniciales de las palabras significativas, igual que el backend', () => {
  assert.equal(unitPrefix('Maquina para correr'), 'MC');
  assert.equal(unitPrefix('Máquina de remo'), 'MR');
  assert.equal(unitPrefix('Mancuerna hexagonal 5 kg par'), 'MH');
  assert.equal(unitPrefix('Colchoneta'), 'CO');
  assert.equal(unitPrefix('Ñandú'), 'NA');
  assert.equal(unitPrefix('123'), 'AC');
});

test('solo equipos y accesorios llevan N° de activo por unidad', () => {
  assert.equal(isUnitCategory('Equipo de fuerza'), true);
  assert.equal(isUnitCategory(' accesorio cardio '), true);
  assert.equal(isUnitCategory('Tienda'), false);
  assert.equal(isUnitCategory('Limpieza'), false);
  assert.equal(isUnitCategory('General'), false);
});

test('una unidad dada de baja deja de estar activa', () => {
  assert.equal(isActiveUnit({ estado: 'En mantenimiento' }), true);
  assert.equal(isActiveUnit({ estado: 'Dado de baja' }), false);
});
