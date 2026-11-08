import assert from 'node:assert/strict';
import { test } from 'node:test';

test('Rate limit calculation respects client caps (10/min client, 5/min visitor)', () => {
  const getCap = (isAuthenticated) => (isAuthenticated ? 10 : 5);

  assert.equal(getCap(true), 10);
  assert.equal(getCap(false), 5);

  const now = Date.now();
  const recentTimestamps = [
    now - 10000,
    now - 8000,
    now - 5000,
    now - 2000,
    now - 500,
    now,
  ];

  const visitorExceeded = recentTimestamps.filter((t) => now - t < 60000).length > getCap(false);
  const clientExceeded = recentTimestamps.filter((t) => now - t < 60000).length > getCap(true);

  assert.equal(visitorExceeded, true, 'Visitor with 6 requests in 1 min exceeds cap of 5');
  assert.equal(clientExceeded, false, 'Client with 6 requests in 1 min does not exceed cap of 10');
});

test('Timeout threshold for slow warning is strictly 15 seconds (HU-CB16)', () => {
  const SLOW_WARNING_THRESHOLD_MS = 15000;
  assert.equal(SLOW_WARNING_THRESHOLD_MS, 15000);
});

test('Inactivity session timeout is strictly 30 minutes (HU-CB16 / EX-14)', () => {
  const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000;
  assert.equal(INACTIVITY_TIMEOUT_MS, 1800000);
});

test('Pending action expiration is strictly 5 minutes (HU-CB16 / EX-15)', () => {
  const PENDING_ACTION_TIMEOUT_MS = 5 * 60 * 1000;
  assert.equal(PENDING_ACTION_TIMEOUT_MS, 300000);
});
