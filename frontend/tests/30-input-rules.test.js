import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  cleanDecimal,
  cleanInteger,
  cleanText,
  isAllowedText,
  matchesSearch,
  missingFields,
  missingFieldsMessage,
  sortRows,
  uniqueOptions,
} from '../src/domain/utils/inputRules.js';

test('search text keeps letters with accents, numbers and spaces up to 40 characters', () => {
  assert.equal(isAllowedText('Proteína Ñandú 2'), true);
  assert.equal(isAllowedText('agua#1'), false);
  assert.deepEqual(cleanText('agua#1 <b>'), { value: 'agua1 b', rejected: true, truncated: false });
  const long = cleanText('a'.repeat(45));
  assert.equal(long.value.length, 40);
  assert.equal(long.truncated, true);
});

test('integer and price fields only keep their allowed characters', () => {
  assert.equal(cleanInteger('12a-3.5e'), '1235');
  assert.equal(cleanDecimal('S/ 12.5.9x9'), '12.59');
  assert.equal(cleanDecimal('7'), '7');
});

test('search matches only the declared fields, ignoring accents and code hyphens', () => {
  const item = { code: 'ACT-0001', name: 'Proteína Whey', location: 'Sala 1' };
  const fields = [item.code, item.name];
  assert.equal(matchesSearch('proteina', fields), true);
  assert.equal(matchesSearch('ACT 0001', fields), true);
  assert.equal(matchesSearch('0001', fields), true);
  assert.equal(matchesSearch('Sala', fields), false);
  assert.equal(matchesSearch('', fields), true);
});

test('rows sort alphabetically or numerically in both directions without mutating', () => {
  const rows = [{ name: 'banda', qty: 10 }, { name: 'Ábaco', qty: 2 }, { name: 'cuerda', qty: 33 }];
  assert.deepEqual(sortRows(rows, (row) => row.name).map((row) => row.name), ['Ábaco', 'banda', 'cuerda']);
  assert.deepEqual(sortRows(rows, (row) => row.name, 'desc').map((row) => row.name), ['cuerda', 'banda', 'Ábaco']);
  assert.deepEqual(sortRows(rows, (row) => row.qty, 'asc', 'number').map((row) => row.qty), [2, 10, 33]);
  assert.equal(rows[0].name, 'banda');
});

test('missing required fields are listed by name', () => {
  const required = [
    { key: 'name', label: 'Nombre' },
    { key: 'quantity', label: 'Stock inicial', isEmpty: (value) => value === '' },
  ];
  assert.deepEqual(missingFields({ name: ' ', quantity: '' }, required), ['Nombre', 'Stock inicial']);
  assert.deepEqual(missingFields({ name: 'Pesas', quantity: 0 }, required), []);
  assert.equal(missingFieldsMessage(['Nombre']), 'Falta completar el campo: Nombre.');
  assert.equal(missingFieldsMessage(['Nombre', 'Precio', 'Stock inicial']), 'Faltan completar los campos: Nombre, Precio y Stock inicial.');
});

test('extensible dropdown options are unique and sorted', () => {
  assert.deepEqual(uniqueOptions(['Caja', 'unidad'], ['Unidad', 'caja', '', null, 'Bolsa']), ['Bolsa', 'Caja', 'unidad']);
});

test('store favorites are kept per user through the preferences port', async () => {
  const { ref } = await import('vue');
  const { createPinia, setActivePinia } = await import('pinia');
  setActivePinia(createPinia());
  const { configureApplicationServices } = await import('../src/application/ports/services.js');
  const { useStoreFavorites } = await import('../src/presentation/composables/store/useStoreFavorites.js');
  const saved = new Map();
  configureApplicationServices({
    http: {}, auth: {}, session: {}, attendance: {}, images: {}, config: {}, storage: {}, repositories: {},
    preferences: {
      readFavoriteProducts: (owner) => saved.get(owner) || [],
      writeFavoriteProducts: (owner, ids) => saved.set(owner, [...ids]),
    },
  });
  const owner = ref('cliente-1');
  const favorites = useStoreFavorites(owner);
  favorites.toggleFavorite(3);
  favorites.toggleFavorite('7');
  assert.equal(favorites.isFavorite(7), true);
  assert.deepEqual(saved.get('cliente-1'), [3, 7]);
  favorites.toggleFavorite(3);
  assert.deepEqual(saved.get('cliente-1'), [7]);
  owner.value = 'cliente-2';
  await Promise.resolve();
  assert.deepEqual(favorites.favoriteIds.value, []);
});
