import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createSessionValidator } from '../src/services/sessionValidation.js';

test('navigation shares pending validation and reuses a recent server response', async () => {
  let calls = 0;
  let finish;
  let now = 0;
  const validator = createSessionValidator(() => {
    calls++;
    return new Promise((resolve) => { finish = resolve; });
  }, { now: () => now });
  const first = validator.validate('session-a');
  const second = validator.validate('session-a');
  assert.equal(first, second);
  await Promise.resolve();
  assert.equal(calls, 1);
  finish({ role: 'admin' });
  await first;
  now = 29_999;
  for (let section = 0; section < 10; section++) {
    assert.deepEqual(await validator.validate('session-a'), { role: 'admin' });
  }
  assert.equal(calls, 1);
  now = 30_000;
  const expired = validator.validate('session-a');
  await Promise.resolve();
  assert.equal(calls, 2);
  finish({ role: 'user' });
  assert.deepEqual(await expired, { role: 'user' });
});

test('changed tokens and forced checks bypass successful cached validation', async () => {
  const calls = [];
  const validator = createSessionValidator(async (token) => {
    calls.push(token);
    return { token };
  });
  await validator.validate('a');
  assert.deepEqual(await validator.validate('b'), { token: 'b' });
  await validator.validate('b', { force: true });
  assert.deepEqual(calls, ['a', 'b', 'b']);
});

test('failed validation is retried instead of granting a cached session', async () => {
  let calls = 0;
  const validator = createSessionValidator(async () => {
    calls++;
    throw new Error('Cuenta desactivada');
  });
  await assert.rejects(validator.validate('a'), /desactivada/);
  await assert.rejects(validator.validate('a'), /desactivada/);
  assert.equal(calls, 2);
});

test('logout invalidates a pending check even when the same token is reused later', async () => {
  let finish;
  let calls = 0;
  const validator = createSessionValidator(() => {
    calls++;
    return new Promise((resolve) => { finish = resolve; });
  });
  const previous = validator.validate('a');
  await Promise.resolve();
  validator.clear();
  finish({ name: 'Sesión anterior' });
  await previous;
  const next = validator.validate('a');
  await Promise.resolve();
  assert.equal(calls, 2);
  finish({ name: 'Sesión actual' });
  assert.deepEqual(await next, { name: 'Sesión actual' });
});
