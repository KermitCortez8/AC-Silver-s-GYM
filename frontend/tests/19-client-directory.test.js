import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  clientMembershipGroup,
  clientMembershipLabel,
  normalizeMembershipStatus,
  filterClientDirectory,
  paginateClients,
} from '../src/utils/clientDirectory.js';

const clients = Array.from({ length: 23 }, (_, index) => ({
  id_cliente: index + 1,
  id: `SGCLI${String(index + 1).padStart(3, '0')}`,
  name: index === 0 ? 'José Pérez' : `Cliente ${index + 1}`,
  email: `cliente${index + 1}@example.com`,
  dni: String(10000000 + index),
  plan: index % 2 ? 'ANUAL' : 'MENSUAL',
  membershipStatus: index % 2 ? 'Activa' : 'PENDIENTE_PAGO',
  paymentStatus: index % 2 ? 'PAGADO' : 'PENDIENTE',
}));

test('the first page shows only the seven newest clients without changing the source', () => {
  const page = paginateClients(filterClientDirectory(clients));
  assert.deepEqual(
    page.items.map((client) => client.id_cliente),
    [23, 22, 21, 20, 19, 18, 17],
  );
  assert.equal(page.totalPages, 4);
  assert.equal(page.start, 1);
  assert.equal(page.end, 7);
  assert.equal(clients[0].id_cliente, 1);
});

test('navigation includes every client exactly once and clamps after deletion', () => {
  const sorted = filterClientDirectory(clients);
  const pages = [1, 2, 3, 4].map((page) => paginateClients(sorted, page));
  assert.deepEqual(
    pages.flatMap((page) => page.items),
    sorted,
  );
  assert.equal(pages[3].items.length, 2);
  assert.equal(paginateClients(sorted.slice(0, 7), 4).page, 1);
  assert.equal(paginateClients([], 99).page, 1);
  assert.equal(paginateClients([]).start, 0);
  assert.equal(paginateClients([]).end, 0);
});

test('search covers the full directory before pagination and ignores accents', () => {
  assert.equal(
    filterClientDirectory(clients, { search: 'JOSE PEREZ' })[0].id_cliente,
    1,
  );
  assert.equal(
    paginateClients(filterClientDirectory(clients, { search: 'SGCLI001' }))
      .items[0].id_cliente,
    1,
  );
  assert.equal(
    filterClientDirectory(clients, { search: 'cliente23@' })[0].id_cliente,
    23,
  );
  assert.equal(
    filterClientDirectory(clients, { search: '10000000' })[0].id_cliente,
    1,
  );
});

test('membership, plan and payment filters work together', () => {
  const filtered = filterClientDirectory(clients, {
    status: 'active',
    plan: 'ANUAL',
    payment: 'PAGADO',
  });
  assert.equal(filtered.length, 11);
  assert.ok(
    filtered.every(
      (client) => client.paymentStatus === 'PAGADO' && client.plan === 'ANUAL',
    ),
  );
  assert.equal(
    filterClientDirectory(clients, { status: 'active', payment: 'PENDIENTE' })
      .length,
    0,
  );
  assert.equal(
    filterClientDirectory([{ id_cliente: 1, paymentStatus: '' }], {
      payment: 'UNKNOWN',
    }).length,
    1,
  );
  assert.equal(
    clientMembershipGroup({ membershipStatus: 'EN_TRAMITE' }),
    'pending',
  );
  assert.equal(
    clientMembershipGroup({ membershipStatus: 'Vencida' }),
    'expired',
  );
});

test('legacy inactive accounts are in progress and do not add a fourth state', () => {
  const directory = [
    { id_cliente: 1, membershipStatus: 'Vencida', status: 'VENCIDA' },
    { id_cliente: 2, membershipStatus: 'Inactiva', status: 'INACTIVO' },
    { id_cliente: 3, membershipStatus: 'Activa', status: 'ACTIVO' },
  ];
  assert.deepEqual(
    filterClientDirectory(directory, { status: 'expired' }).map(
      (c) => c.id_cliente,
    ),
    [1],
  );
  assert.deepEqual(
    filterClientDirectory(directory, { status: 'pending' }).map(
      (c) => c.id_cliente,
    ),
    [2],
  );
});

test('sorting supports oldest first, names and IDs before registration dates are refreshed', () => {
  assert.equal(
    filterClientDirectory(clients, { sort: 'oldest' })[0].id_cliente,
    1,
  );
  assert.deepEqual(
    filterClientDirectory(
      [
        { id: 'SGCLI001', name: 'Zoe' },
        { id: 'SGCLI002', name: 'Ana' },
      ],
      { sort: 'name' },
    ).map((client) => client.name),
    ['Ana', 'Zoe'],
  );
  assert.equal(
    filterClientDirectory([
      { id_cliente: 2, joinedAt: '' },
      { id_cliente: 1, joinedAt: '2026-01-01' },
    ])[0].id_cliente,
    2,
  );
});

test('page navigation stays short even with thousands of clients', () => {
  const page = paginateClients(Array.from({ length: 7000 }), 500);
  assert.deepEqual(page.pages, [1, 'gap-499', 499, 500, 501, 'gap-1000', 1000]);
  assert.equal(page.pages.length, 7);
});

test('only three membership labels are exposed, including legacy and missing values', () => {
  for (const [raw, state, label] of [
    ['ACTIVO', 'ACTIVO', 'Activo'],
    ['Activa', 'ACTIVO', 'Activo'],
    ['VENCIDA', 'VENCIDA', 'Vencida'],
    ['Vencido', 'VENCIDA', 'Vencida'],
    ['EN_TRAMITE', 'EN_TRAMITE', 'En trámite'],
    ['PENDIENTE_PAGO', 'EN_TRAMITE', 'En trámite'],
    ['Inactiva', 'EN_TRAMITE', 'En trámite'],
    ['', 'EN_TRAMITE', 'En trámite'],
  ]) {
    assert.equal(normalizeMembershipStatus(raw), state);
    assert.equal(clientMembershipLabel({ membershipStatus: raw }), label);
  }
  assert.equal(
    filterClientDirectory([{ membershipStatus: 'EN_TRAMITE' }], {
      search: 'en tramite',
    }).length,
    1,
  );
});
