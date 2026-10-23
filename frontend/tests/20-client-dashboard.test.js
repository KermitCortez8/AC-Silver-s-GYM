import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  lastSevenPeruDays,
  peruDateKey,
  summarizeDashboardClients,
} from '../src/utils/clientDashboard.js';

test('dashboard keeps expired memberships distinct and activation requires a confirmed payment', () => {
  const summary = summarizeDashboardClients([
    {
      membershipStatus: 'Activa',
      paymentStatus: 'PAGADO',
      registrationOrigin: 'ADMIN',
    },
    {
      membershipStatus: 'PENDIENTE_PAGO',
      paymentStatus: 'PENDIENTE',
      registrationOrigin: 'ADMIN',
    },
    {
      membershipStatus: 'EN_TRAMITE',
      paymentStatus: 'PAGADO',
      registrationOrigin: 'PUBLICO',
    },
    { membershipStatus: 'Vencida', paymentStatus: 'PAGADO' },
    { membershipStatus: 'Inactiva' },
  ]);
  assert.deepEqual(summary.memberships, {
    active: 1,
    pending: 3,
    expired: 1,
  });
  assert.equal(summary.readyToActivate, 1);
  assert.equal(summary.pendingPayment, 1);
  assert.equal(summary.total, 5);
  assert.deepEqual(
    summary.origins.map(({ paid, pending, unknown }) => [
      paid,
      pending,
      unknown,
    ]),
    [
      [1, 1, 0],
      [1, 0, 0],
      [1, 0, 1],
    ],
  );
  assert.equal(
    summary.origins.reduce((sum, o) => sum + o.paid + o.pending + o.unknown, 0),
    5,
  );
});

test('client updates immediately move counts from payment to activation to active to expired', () => {
  const client = {
    membershipStatus: 'PENDIENTE_PAGO',
    paymentStatus: 'PENDIENTE',
    registrationOrigin: 'ADMIN',
  };
  assert.equal(summarizeDashboardClients([client]).pendingPayment, 1);
  client.membershipStatus = 'EN_TRAMITE';
  client.paymentStatus = 'PAGADO';
  assert.equal(summarizeDashboardClients([client]).readyToActivate, 1);
  client.membershipStatus = 'Activa';
  assert.equal(summarizeDashboardClients([client]).memberships.active, 1);
  assert.equal(summarizeDashboardClients([client]).readyToActivate, 0);
  client.membershipStatus = 'Vencida';
  const result = summarizeDashboardClients([client]);
  assert.equal(result.memberships.expired, 1);
  assert.equal(result.origins[0].paid, 1);
});

test('dashboard handles missing origin and missing payment without inventing confirmation', () => {
  const empty = summarizeDashboardClients([]);
  assert.equal(empty.total, 0);
  assert.equal(empty.readyToActivate, 0);
  const result = summarizeDashboardClients([
    { membershipStatus: 'EN_TRAMITE', registrationOrigin: 'LEGACY' },
  ]);
  assert.equal(result.readyToActivate, 0);
  assert.equal(result.pendingPayment, 0);
  assert.equal(result.origins[2].unknown, 1);
});

test('daily dashboard and seven day chart use Peru time across UTC and month boundaries', () => {
  assert.equal(peruDateKey(new Date('2026-10-02T04:59:59Z')), '2026-10-01');
  assert.equal(peruDateKey(new Date('2026-10-02T05:00:00Z')), '2026-10-02');
  assert.deepEqual(lastSevenPeruDays(new Date('2026-03-02T04:00:00Z')), [
    '2026-02-23',
    '2026-02-24',
    '2026-02-25',
    '2026-02-26',
    '2026-02-27',
    '2026-02-28',
    '2026-03-01',
  ]);
});
