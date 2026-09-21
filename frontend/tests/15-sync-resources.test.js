import assert from 'node:assert/strict';
import { test } from 'node:test';
import { syncResources } from '../src/services/syncResources.js';

test('loads at most three resources concurrently and starts another when one completes', async () => {
  const started = [];
  const finish = [];
  const tasks = Array.from({ length: 5 }, (_, index) => [String(index), () => {
    started.push(index);
    return new Promise((resolve) => { finish[index] = resolve; });
  }]);
  const sync = syncResources(tasks);
  assert.deepEqual(started, [0, 1, 2]);
  finish[1]();
  await Promise.resolve();
  assert.deepEqual(started, [0, 1, 2, 3]);
  finish[0]();
  await Promise.resolve();
  assert.deepEqual(started, [0, 1, 2, 3, 4]);
  finish[2]();
  finish[3]();
  finish[4]();
  await sync;
});

test('continues loading after errors and reports failed sections in catalogue order', async () => {
  let finishFirst;
  const loaded = [];
  const errors = [];
  const sync = syncResources([
    ['Clientes', () => new Promise((_, reject) => { finishFirst = reject; })],
    ['Planes', async () => { throw new Error('No disponible'); }],
    ['Productos', async () => { loaded.push('Productos'); }],
    ['Horarios', async () => { loaded.push('Horarios'); }],
  ], (message) => errors.push(message));
  const failure = assert.rejects(sync, /Clientes: Sin conexión Planes: No disponible/);
  await Promise.resolve();
  finishFirst(new Error('Sin conexión'));
  await failure;
  assert.deepEqual(loaded, ['Productos', 'Horarios']);
  assert.equal(errors.at(-1), 'Clientes: Sin conexión Planes: No disponible');
});
