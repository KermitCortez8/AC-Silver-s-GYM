import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reactive } from 'vue';
import { usePlanDirectory } from '../src/presentation/composables/memberships/usePlanDirectory.js';

const plans = [
  { id: 'pm-1', name: 'Mensual', description: 'Entrenamiento', benefits: 'Evaluación inicial', duration: '30 días', price: 80, active: true },
  { id: 'pm-2', name: 'Anual', description: 'Acceso completo', benefits: '', duration: '365 días', price: 500, active: false },
  { id: 'pm-3', name: 'Prueba', description: '', benefits: '', duration: '1 día', price: 0, active: true },
];
const directory = fetchFromBackend => usePlanDirectory(reactive({ planCatalog: [...plans], fetchFromBackend }));

test('el catálogo combina búsqueda sin tildes con disponibilidad y cuenta planes activos', () => {
  const catalog = directory(async () => {});
  assert.equal(catalog.activeCount.value, 2);
  catalog.search.value = 'evaluacion';
  assert.deepEqual(catalog.filteredPlans.value.map(plan => plan.id), ['pm-1']);
  catalog.status.value = 'inactive';
  assert.equal(catalog.filteredPlans.value.length, 0);
  catalog.clearFilters();
  assert.equal(catalog.hasFilters.value, false);
  assert.equal(catalog.filteredPlans.value.length, 3);
  catalog.status.value = 'inactive';
  assert.deepEqual(catalog.filteredPlans.value.map(plan => plan.id), ['pm-2']);
});

test('el orden por precio conserva cero y no altera el catálogo original', () => {
  const catalog = directory(async () => {});
  catalog.sort.value = 'price-asc';
  assert.deepEqual(catalog.filteredPlans.value.map(plan => plan.price), [0, 80, 500]);
  catalog.sort.value = 'price-desc';
  assert.deepEqual(catalog.filteredPlans.value.map(plan => plan.price), [500, 80, 0]);
  assert.deepEqual(catalog.plans.value.map(plan => plan.id), ['pm-1', 'pm-2', 'pm-3']);
});

test('la carga evita consultas duplicadas y finaliza el estado de espera', async () => {
  let release, calls = 0;
  const pending = new Promise(resolve => { release = resolve; });
  const catalog = directory(async options => { assert.deepEqual(options, { section: 'plans' }); calls++; await pending; });
  const loading = catalog.loadPlans();
  await catalog.loadPlans();
  assert.equal(catalog.loading.value, true);
  assert.equal(calls, 1);
  release();
  await loading;
  assert.equal(catalog.loading.value, false);
});

test('un fallo de carga conserva los planes y un reintento limpia el error', async () => {
  let fail = true;
  const catalog = directory(async () => { if (fail) throw new Error('Servicio temporalmente indisponible'); });
  await catalog.loadPlans();
  assert.equal(catalog.loadError.value, 'Servicio temporalmente indisponible');
  assert.equal(catalog.loading.value, false);
  assert.equal(catalog.plans.value.length, 3);
  fail = false;
  await catalog.loadPlans();
  assert.equal(catalog.loadError.value, '');
});
