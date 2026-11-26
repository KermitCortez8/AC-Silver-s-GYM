import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createPinia, setActivePinia } from 'pinia';
import { ref } from 'vue';
import { setupComponent, setupView } from '../../soporte/entorno-formularios.js';
import { createInventoryModule } from '../../../src/application/modules/inventory.js';
import { createStoreModule } from '../../../src/application/modules/store.js';
import { SYNC_SECTIONS } from '../../../src/application/modules/synchronization.js';

const ITEM = { id: 'item-1', inventoryCode: 'ACT-1001', name: 'Mancuerna hexagonal 5 kg par', category: 'Equipo de fuerza',
  location: 'Almacén', quantity: 21, minQuantity: 1, archived: false, byUnit: true };
const UNIT = { id_unidad: 19, id_item: 1, correlativo: 19, codigo: '1001-MH-019', estado: 'Operativo', ubicacion: 'Sala 1' };
const MOVEMENTS = [
  { id_mov: 7, id_item: 1, tipo_movimiento: 'traslado', cantidad: 1, fecha_movimiento: '2026-11-24', hora_movimiento: '19:12:00',
    descripcion: 'Traslado 1001-MH-019: Sala de fuerza → Sala 1', id_usuario: 'SGADM001', id_unidad: 19 },
  { id_mov: 6, id_item: 1, tipo_movimiento: 'entrada', cantidad: 2, fecha_movimiento: '2026-11-19', hora_movimiento: '21:45:00',
    descripcion: 'Alta de ítem · Unidades: 1001-MH-023 a 1001-MH-024', id_usuario: 'SGADM001' },
];
const DISABLED_BUTTON = /<button\b[^>]*?\sdisabled(?=[\s>=])/;

// ---- Movimientos: Excel y Detalles ------------------------------------------------------------

test('X-02: Movimientos ofrece Descargar Excel solo cuando hay filas filtradas', async () => {
  const empty = await setupComponent('inventory/InventoryMovementsPanel', {}, (_setup, gym) => { gym.inventory = [ITEM]; });
  assert.match(empty.html, /Descargar Excel/);
  assert.match(empty.html, DISABLED_BUTTON);
  const full = await setupComponent('inventory/InventoryMovementsPanel', {}, (_setup, gym) => {
    gym.inventory = [ITEM];
    gym.inventoryMovements = MOVEMENTS;
  });
  assert.equal(full.setup.sortedMovements.length, 2);
  assert.match(full.html, /Detalles/);
});

test('D-02: Detalles de un traslado muestra sus datos, el historial y el cambio a solo la unidad', async () => {
  const { setup, html } = await setupComponent('inventory/MovementDetailsModal', { movement: MOVEMENTS[0], item: ITEM, destination: '' }, (_setup, gym) => {
    gym.inventoryMovements = MOVEMENTS;
    gym.inventoryUnits = [UNIT];
    gym.users = [{ id_usuario: 'SGADM001', nombre: 'Administrador Silver' }];
  });
  assert.equal(setup.author, 'Administrador Silver');
  assert.deepEqual(setup.history.map((row) => row.id_mov), [7, 6]);
  assert.equal(setup.unit.codigo, '1001-MH-019');
  setup.unitOnly = true;
  assert.deepEqual(setup.history.map((row) => row.id_mov), [7]);
  void html;
});

test('D-03: Detalles de un movimiento sin unidad no ofrece filtrar por unidad', async () => {
  const { setup } = await setupComponent('inventory/MovementDetailsModal', { movement: MOVEMENTS[1], item: ITEM }, (_setup, gym) => {
    gym.inventoryMovements = MOVEMENTS;
    gym.inventoryUnits = [UNIT];
  });
  assert.equal(setup.unit, null);
  assert.deepEqual(setup.history.map((row) => row.id_mov), [7, 6]);
});

// ---- Íconos de dar de baja --------------------------------------------------------------------

test('I-01: Tienda muestra "Dar de baja" con la caja de archivo y no la basurita', async () => {
  const { html } = await setupComponent('store/StoreProductTable', {
    ...(() => {
      const productos = [{ id_producto: 1, id_item: 2, nombre: 'Agua', categoria: 'Bebidas', precio: 2, cantidad: 5, estado: 'Disponible' }];
      return { productos, productosFiltrados: productos, productosPaginados: productos, categoriasUnicas: ['Bebidas'] };
    })(),
    categoriaDotColor: () => '#c8102e', productCode: () => 'PROD-0001', isProductLowStock: () => false, productStatusClass: () => '',
  });
  assert.match(html, /Dar de baja/);
  assert.match(html, /lucide-archive/);
  assert.doesNotMatch(html, />\s*Eliminar\s*</);
  assert.doesNotMatch(html, /lucide-trash/);
});

test('I-01: el panel de unidades da de baja con la caja de archivo', async () => {
  const { html } = await setupComponent('inventory/InventoryUnitsPanel', { item: ITEM }, (_setup, gym) => {
    gym.inventory = [ITEM];
    gym.inventoryUnits = [UNIT];
  });
  assert.match(html, /aria-label="Dar de baja 1001-MH-019"/);
  assert.match(html, /lucide-archive/);
  assert.doesNotMatch(html, /lucide-trash/);
});

// ---- Yape con QR ------------------------------------------------------------------------------

test('Y-08: con Yape se ve el QR y el pedido se registra sin número de operación', async () => {
  const { setup, gym } = await setupView('StorePaymentView', '/tienda/pago');
  gym.cart = [{ id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 1 }];
  Object.assign(setup.payment, { customerName: 'Ana', customerEmail: 'ana@hotmail.com', dni: '12345678', method: 'yape', reference: '' });
  assert.equal(setup.isYape, true);
  assert.match(setup.submitLabel, /Registrar pedido/);
  assert.match(setup.infoMessage, /recepcionista/);
  const sent = [];
  gym.createStoreOrder = async (payload) => { sent.push(payload); return { id_pedido: 9, estado_pago: 'PENDIENTE', metodo_pago: 'yape' }; };
  await setup.submitPayment();
  assert.equal(sent.length, 1);
  assert.equal(sent[0].metodo_pago, 'yape');
  assert.match(setup.orderCreatedMessage, /Confirma tu pago con Yape con el recepcionista/);
});

test('Y-08: el QR de Yape aparece en la pantalla de pago', async () => {
  const { html } = await setupView('StorePaymentView', '/tienda/pago', (setup, gym) => {
    gym.cart = [{ id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 1 }];
    setup.payment.method = 'yape';
  });
  assert.match(html, /src="\/pagos\/yape-qr\.png"/);
  assert.match(html, /Confirma tu pago con el recepcionista/);
});

test('Y-09: Pedidos muestra el Yape por confirmar y Ventas no lo suma hasta confirmarse', async () => {
  const base = { id_cliente: 1, cliente_nombre: 'Ana', fecha_pedido: '2026-11-25T15:00:00Z', items: [{ nombre_producto: 'Agua', cantidad: 1 }] };
  const { setup, html } = await setupView('OrdersView', '/admin/orders', (_s, gym) => {
    gym.storeOrders = [
      { ...base, id_pedido: 1, metodo_pago: 'yape', estado_pago: 'PENDIENTE', estado_pedido: 'PENDIENTE', total: 10 },
      { ...base, id_pedido: 2, metodo_pago: 'plin', estado_pago: 'PAGADO', estado_pedido: 'CONFIRMADO', total: 20 },
      { ...base, id_pedido: 3, metodo_pago: 'tarjeta', estado_pago: 'PENDIENTE', estado_pedido: 'PENDIENTE', total: 40 },
    ];
  });
  assert.deepEqual(setup.orders.map((order) => order.id_pedido).sort(), [1, 2]);
  assert.equal(setup.totalSales, 20);
  assert.match(html, /YAPE POR CONFIRMAR/);
});

// ---- Recargas: solo lo afectado -----------------------------------------------------------------

const inventoryContext = () => {
  const sections = [];
  const ctx = {
    apiBase: '/api', authStore: { token: 'session' }, generation: 0, resourceErrors: new Map(), syncError: ref(''),
    inventory: ref([ITEM, { id: 'item-2', name: 'Agua', category: 'Tienda', byUnit: false }]),
    inventoryMovements: ref([{ id_mov: 50, id_item: 2, tipo_movimiento: 'salida', destino: 'TIENDA' }]),
    inventoryUnits: ref([UNIT]),
    fetchFromBackend: async ({ section }) => { sections.push(section); },
  };
  return { ctx, sections };
};

test('O-01: editar el estado de una unidad pide solo unidades y artículos; moverla también pide movimientos', async () => {
  setActivePinia(createPinia());
  const { ctx, sections } = inventoryContext();
  const module = createInventoryModule(ctx, { updateInventoryUnit: async (id, payload) => ({ id_unidad: id, ...payload }) });
  await module.updateInventoryUnit(19, { estado: 'En mantenimiento', ubicacion: 'Sala 1' });
  await module.updateInventoryUnit(19, { estado: 'Operativo', ubicacion: 'Sala de fuerza' });
  assert.deepEqual(sections, ['inventoryUnitState', 'inventory']);
  assert.deepEqual(SYNC_SECTIONS.inventoryUnitState, ['Inventario', 'Unidades de inventario']);
  assert.ok(!SYNC_SECTIONS.inventoryUnitState.includes('Productos'));
});

test('O-02 y O-04: un traslado no pide productos; una reposición a Tienda sí', async () => {
  setActivePinia(createPinia());
  const { ctx, sections } = inventoryContext();
  const module = createInventoryModule(ctx, {
    registrarMovimientoToServer: async (payload) => (payload.tipo_movimiento === 'traslado'
      ? { movimiento: { id_mov: 99, ...payload }, movimientos: [{ id_mov: 99 }, { id_mov: 100 }] }
      : { movimiento: { id_mov: 101, ...payload } }),
    updateInventoryMovement: async (id, payload) => ({ movimiento: { id_mov: id, id_item: 2, destino: null, ...payload } }),
  });
  await module.registrarMovimientoToServer({ id_item: 1, tipo_movimiento: 'traslado', cantidad: 2, unidades: [19, 20], ubicacion_destino: 'Sala 2' });
  await module.registrarMovimientoToServer({ id_item: 2, tipo_movimiento: 'salida', cantidad: 3, destino: 'TIENDA' });
  // Quitar el destino Tienda a una reposición también cambia el stock de la Tienda.
  await module.updateInventoryMovement(50, { descripcion: 'Corrección', destino: '' });
  assert.deepEqual(sections, ['inventoryUnitsHistory', 'inventoryStore', 'inventoryStore']);
  assert.deepEqual(SYNC_SECTIONS.inventoryUnitsHistory, ['Unidades de inventario', 'Movimientos']);
  assert.deepEqual(ctx.inventoryMovements.value.slice(0, 3).map((row) => row.id_mov), [101, 99, 100]);
});

test('O-03: cancelar un pedido recarga pedidos y productos, no todo el sistema', async () => {
  setActivePinia(createPinia());
  const sections = [];
  const ctx = {
    apiBase: '/api', authStore: { token: 'session' }, generation: 0, resourceErrors: new Map(), syncError: ref(''),
    productos_tienda: ref([]), papelera_tienda: ref([]), storeOrders: ref([{ id_pedido: 1, estado_pedido: 'CONFIRMADO' }]), cart: ref([]),
    inventory: ref([]), members: ref([]),
    fetchFromBackend: async (options = {}) => { sections.push(options.section ?? 'TODO'); },
  };
  const module = createStoreModule(ctx, { updateStoreOrderStatus: async (id, body) => ({ id_pedido: id, ...body, items: [] }) });
  await module.updateStoreOrderStatus(1, { estado_pedido: 'CANCELADO' });
  assert.deepEqual(sections, ['ordersStock']);
  assert.deepEqual(SYNC_SECTIONS.ordersStock, ['Pedidos', 'Productos']);
});
