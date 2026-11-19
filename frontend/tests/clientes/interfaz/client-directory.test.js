import assert from 'node:assert/strict';
import { test } from 'node:test';
import { view } from '../../soporte/entorno-vistas.js';

const target = {
  id: 'SGCLI001', id_cliente: 1, name: 'Ana Tórres', dni: '12345678',
  email: 'ana.torres@example.com', status: 'ACTIVO',
};
const clients = [
  target,
  ...Array.from({ length: 22 }, (_, index) => ({
    id: `SGCLI${String(index + 2).padStart(3, '0')}`,
    id_cliente: index + 2,
    name: index === 0 ? 'Ana Rivera' : `Cliente ${index + 2}`,
    dni: String(20000000 + index),
    email: `cliente${index}@example.com`,
    status: 'ACTIVO',
  })),
];

const directory = search => view('ClientsView', {
  prepare: (setup, gym) => {
    gym.members = structuredClone(clients);
    setup.isLoading = false;
    setup.search = search;
  },
});

const verifyDetails = (setup, result) => {
  setup.openDetails(result);
  assert.equal(setup.isDetailsOpen, true);
  assert.equal(setup.viewingClient.id, target.id);
  assert.equal(setup.viewingClient.dni, target.dni);
  setup.closeDetails();
};

test('buscar por DNI abre la ficha correcta y limpiar recupera todo el directorio', async () => {
  const { setup, gym, dispose } = await directory('');
  try {
    assert.ok(setup.pagination.totalPages > 1);
    assert.ok(!setup.pagination.items.some(client => client.id === target.id));
    setup.search = target.dni;
    const [result] = setup.pagination.items;
    assert.equal(setup.pagination.total, 1);
    verifyDetails(setup, result);

    setup.resetFilters();
    assert.equal(setup.pagination.total, clients.length);
    setup.search = target.dni;
    setup.search = '';
    assert.equal(setup.pagination.total, clients.length);
    assert.deepEqual(gym.members, clients);
  } finally {
    dispose();
  }
});

test('buscar por nombre completo o fragmento mantiene la identidad de la ficha elegida', async () => {
  const { setup, gym, dispose } = await directory('Ana Torres');
  try {
    assert.deepEqual(setup.pagination.items.map(client => client.id), [target.id]);
    setup.search = 'Ana';
    assert.equal(setup.pagination.total, 2);
    verifyDetails(setup, setup.pagination.items.find(client => client.id === target.id));
    assert.deepEqual(gym.members, clients);
  } finally {
    dispose();
  }
});

test('buscar por correo o código interno encuentra la ficha y permite limpiar', async () => {
  const { setup, dispose } = await directory(target.email);
  try {
    for (const query of [target.email, 'ana.torres@', target.id]) {
      setup.search = query;
      assert.equal(setup.pagination.total, 1, query);
      verifyDetails(setup, setup.pagination.items[0]);
      setup.resetFilters();
      assert.equal(setup.pagination.total, clients.length);
    }
  } finally {
    dispose();
  }
});

test('la búsqueda sin coincidencias informa el vacío y se recupera sin perder clientes', async () => {
  const { setup, gym, html, dispose } = await directory('identidad inexistente');
  try {
    assert.match(html, /No encontramos coincidencias/);
    assert.equal(setup.pagination.total, 0);
    setup.search = target.dni;
    assert.equal(setup.pagination.total, 1);
    verifyDetails(setup, setup.pagination.items[0]);
    assert.deepEqual(gym.members, clients);
  } finally {
    dispose();
  }
});

test('el buscador acepta texto libre, lo recorta a 30 caracteres y reinicia la página al limpiar', async () => {
  const { setup, html, child, dispose } = await directory('');
  try {
    assert.match(html, /<input[^>]+type="search"[^>]+maxlength="30"/);
    setup.currentPage = 2;
    const component = child('SearchInput');
    const input = { value: 'Ana Torres'.padEnd(35, ' ') };
    component.update({ target: input });
    assert.equal(input.value.length, 30);
    assert.equal(setup.search.length, 30);
    assert.deepEqual(setup.pagination.items.map(client => client.id), [target.id]);

    setup.resetFilters();
    assert.equal(setup.search, '');
    assert.equal(setup.pagination.page, 1);
    assert.equal(setup.pagination.total, clients.length);
  } finally {
    dispose();
  }
});

test('el directorio permite reconocer y recuperar resultados sin recorrer páginas', async () => {
  const found = await directory('Ana Torres');
  const empty = await directory('identidad inexistente');
  try {
    assert.match(found.html, /Ana Tórres/);
    assert.match(found.html, /DNI 12345678/);
    assert.equal(found.setup.pagination.total, 1);
    found.setup.search = target.id;
    assert.equal(found.setup.pagination.total, 1);
    verifyDetails(found.setup, found.setup.pagination.items[0]);
    assert.match(empty.html, /No encontramos coincidencias/);
    assert.match(empty.html, /Limpiar filtros/);
    assert.equal(empty.setup.isDetailsOpen, false);
    assert.equal(empty.setup.viewingClient, null);
    empty.setup.resetFilters();
    assert.equal(empty.setup.pagination.page, 1);
    assert.equal(empty.setup.pagination.total, 23);
    assert.deepEqual(empty.gym.members, clients);
  } finally {
    found.dispose();
    empty.dispose();
  }
});
