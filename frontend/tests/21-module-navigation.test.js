import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createModuleLoader, prepareNavigationSession } from '../src/services/moduleNavigation.js';

const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};

test('slow data stops blocking the view after three seconds without restarting the loader', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let visible = false;
  const loader = createModuleLoader({ onChange: value => { visible = value; } });
  loader.setSyncing(true);
  const navigation = loader.start();
  loader.complete(navigation);
  t.mock.timers.tick(2779);
  assert.equal(visible, true);
  t.mock.timers.tick(1);
  assert.equal(visible, false);
  t.mock.timers.tick(220);
  assert.equal(visible, false);
  loader.setSyncing(false);
  t.mock.timers.tick(7000);
  assert.equal(visible, false);
});

test('fast views have no artificial minimum wait', () => {
  let visible;
  const loader = createModuleLoader({ onChange: value => { visible = value; } });
  const navigation = loader.start();
  assert.equal(visible, true);
  loader.complete(navigation);
  assert.equal(visible, false);
});

test('old navigation completion cannot close a newer transition', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let visible;
  const loader = createModuleLoader({ onChange: value => { visible = value; } });
  const old = loader.start();
  t.mock.timers.tick(2000);
  const current = loader.start();
  loader.complete(old);
  t.mock.timers.tick(1000);
  assert.equal(visible, true);
  loader.complete(current);
  assert.equal(visible, false);
});

test('unmounting cancels loader timers and ignores pending completion', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const changes = [];
  const loader = createModuleLoader({ onChange: value => changes.push(value) });
  const navigation = loader.start();
  loader.dispose();
  loader.complete(navigation);
  t.mock.timers.tick(3000);
  assert.deepEqual(changes, [true, false]);
});

for (const role of ['admin', 'trainer']) {
  test(`${role} section changes proceed while server session revalidation is pending`, { timeout: 1000 }, async () => {
    const validation = deferred();
    let calls = 0;
    const auth = {
      isInitialized: true, isAuthenticated: true,
      isAdmin: role === 'admin', isTrainer: role === 'trainer',
      initializeAuth() { calls++; return validation.promise; },
    };
    const meta = { requiresAuth: true, requiresAdmin: role === 'admin', requiresTrainer: role === 'trainer' };
    await prepareNavigationSession(auth, { path: `/${role}/routines`, meta }, { meta });
    assert.equal(calls, 1);
    validation.resolve();
  });
}

test('entering a protected panel still waits for server validation', async () => {
  const validation = deferred();
  let ready = false;
  const auth = {
    isInitialized: true, isAuthenticated: true, isAdmin: true,
    initializeAuth: () => validation.promise,
  };
  const navigation = prepareNavigationSession(auth, {
    path: '/admin/users', meta: { requiresAuth: true, requiresAdmin: true },
  }, { path: '/', meta: {} }).then(() => { ready = true; });
  await Promise.resolve();
  assert.equal(ready, false);
  validation.resolve();
  await navigation;
  assert.equal(ready, true);
});

test('client sessions keep blocking validation before protected navigation', async () => {
  const validation = deferred();
  let ready = false;
  const auth = {
    isInitialized: true, isAuthenticated: true, isAdmin: false, isTrainer: false,
    initializeAuth: () => validation.promise,
  };
  const meta = { requiresAuth: true };
  const navigation = prepareNavigationSession(auth, { path: '/user/store', meta }, { meta }).then(() => { ready = true; });
  await Promise.resolve();
  assert.equal(ready, false);
  validation.resolve();
  await navigation;
  assert.equal(ready, true);
});
