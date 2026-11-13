import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

test('editing a store product preserves a zero threshold through the actual view and save payload', async () => {
  const { setup, gym } = await setupView('StoreView', '/admin/store');
  const product = { id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 1, minimo: 0, estado: 'Disponible' };
  setup.editProducto(product);
  assert.equal(setup.form.minimo, 0);
  assert.equal(setup.stockBarColor(product), 'bg-emerald-400');
  setup.editProducto({ ...product, minimo: undefined });
  assert.equal(setup.form.minimo, 5);
  setup.editProducto(product);
  let payload;
  gym.upsertProductoTienda = async (value) => { payload = { ...value }; };
  await setup.handleSubmit();
  assert.equal(payload.minimo, 0);
  assert.equal(setup.feedbackTone, 'success');
});

test('la papelera conserva su pestaña y las acciones de restaurar y eliminar', async () => {
  const { setup, html } = await setupView('StoreView', '/admin/store', (_setup, gym) => {
    gym.papelera_tienda = [{ id_producto: 8, nombre: 'Agua archivada', precio: 3, cantidad: 4 }];
  }, { tab: 'papelera' });
  assert.equal(setup.activeTab, 'papelera');
  assert.ok(setup.tabs.some(tab => tab.value === 'papelera'));
  assert.match(html, /Agua archivada/);
  assert.match(html, /Restaurar/);
  assert.match(html, /Eliminar/);
});

test('a failed product save preserves the editor and its entered values', async () => {
  const { setup, gym } = await setupView('StoreView', '/admin/store');
  setup.openNewProducto();
  setup.form.nombre = 'Agua';
  setup.form.precio = 3;
  gym.upsertProductoTienda = async () => { throw new Error('No se pudo guardar'); };
  await setup.handleSubmit();
  assert.equal(setup.isProductEditorOpen, true);
  assert.equal(setup.form.nombre, 'Agua');
  assert.equal(setup.isSaving, false);
  assert.equal(setup.feedbackTone, 'error');
});

test('extracted product dialog hides the inventory link and renders the image picker', async () => {
  const { dialogs } = await setupView('StoreView', '/admin/store', (setup, gym) => {
    gym.inventory = [{ id: 'item-1', name: 'Almacén Agua', inventoryCode: 'ACT-0001', category: 'Tienda' }];
    const product = { id_producto: 1, id_item: 1, nombre: 'Agua editada', precio: 3, cantidad: 4, minimo: 0, estado: 'Disponible' };
    gym.productos_tienda = [product];
    setup.editProducto(product);
    setup.isBucketPickerOpen = true;
    setup.bucketImages = [{ name: 'agua.png', url: '/agua.png' }];
  });
  assert.match(dialogs, /Agua editada/);
  // El vinculo con Inventario se conserva por detras: el modal ya no lo muestra ni lo cambia.
  assert.doesNotMatch(dialogs, /Item de inventario|Almacén Agua/);
  assert.match(dialogs, /agua.png/);
  assert.match(dialogs, /Guardar cambios/);
});

test('product editor validates quantities before sending them', async () => {
  const { setup, gym } = await setupView('StoreView', '/admin/store');
  setup.openNewProducto();
  setup.form.nombre = 'Agua';
  setup.form.cantidad = '2e2';
  let saves = 0;
  gym.upsertProductoTienda = async () => { saves++; };
  await setup.handleSubmit();
  assert.equal(saves, 0);
  assert.equal(setup.feedbackTone, 'error');
  assert.equal(setup.isProductEditorOpen, true);
});

test('order status saves cannot overlap and retain their draft after failure', async () => {
  const { setup, gym } = await setupView('OrdersView', '/admin/orders');
  const order = { id_pedido: 1, estado_pedido: 'PENDIENTE', items: [] };
  setup.ensureDraft(order).estado_pedido = 'CONFIRMADO';
  setup.ensureDraft(order).observacion_admin = 'Recoger mañana';
  let reject;
  let calls = 0;
  gym.updateStoreOrderStatus = () => { calls++; return new Promise((resolve, fail) => { reject = fail; }); };
  const pending = setup.updateOrder(order);
  await setup.updateOrder(order);
  assert.equal(calls, 1);
  reject(new Error('Sin conexión'));
  await pending;
  assert.equal(setup.ensureDraft(order).estado_pedido, 'CONFIRMADO');
  assert.equal(setup.ensureDraft(order).observacion_admin, 'Recoger mañana');
  assert.equal(setup.savingOrders.size, 0);
  assert.equal(setup.feedback, 'Sin conexión');
});

test('store quantity errors are visible and do not change the cart', async () => {
  const { setup, gym } = await setupView('StoreView', '/user/store');
  const product = { id_producto: 1, nombre: 'Agua', precio: 2, cantidad: 3, estado: 'Disponible' };
  gym.productos_tienda = [product];
  setup.cantidadInput[1] = '1e2';
  setup.agregarAlCarrito(product);
  assert.equal(gym.cart.length, 0);
  assert.equal(setup.feedbackTone, 'error');
  setup.cantidadInput[1] = '2';
  setup.agregarAlCarrito(product);
  assert.equal(gym.cart[0].cantidad, 2);
  setup.agregarAlCarrito(product);
  assert.equal(gym.cart[0].cantidad, 3);
  setup.agregarAlCarrito(product);
  assert.equal(gym.cart[0].cantidad, 3);
  assert.equal(setup.feedbackTone, 'error');
  setup.updateCart(1, '1.5');
  assert.equal(gym.cart[0].cantidad, 3);
});

test('failed gallery refresh preserves previously loaded images', async (t) => {
  const { setup } = await setupView('StoreView', '/admin/store');
  setup.bucketImages = [{ name: 'agua.png', url: '/agua.png' }];
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('Failed to fetch'); });
  await setup.loadBucketImages();
  assert.equal(setup.bucketImages.length, 1);
  assert.equal(setup.bucketImages[0].name, 'agua.png');
  assert.equal(setup.imageFeedbackTone, 'error');
  assert.equal(setup.isLoadingBucketImages, false);
});

test('checkout validates customer data and prevents duplicate payments while preserving failed drafts', async () => {
  const { setup, gym } = await setupView('StorePaymentView', '/tienda/pago');
  gym.cart = [{ id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 1 }];
  Object.assign(setup.payment, { customerName: 'Ana', customerEmail: 'ana@', dni: '12345678', method: 'yape', reference: 'PAY-1' });
  let calls = 0;
  let rejectSave;
  gym.createStoreOrder = () => { calls++; return new Promise((_resolve, reject) => { rejectSave = reject; }); };
  await setup.submitPayment();
  assert.equal(calls, 0);
  assert.match(setup.feedback, /correo válido/);
  setup.payment.customerEmail = 'ana@hotmail.com';
  setup.payment.dni = 'abc';
  await setup.submitPayment();
  assert.equal(calls, 0);
  assert.match(setup.feedback, /8 dígitos/);
  setup.payment.dni = '12345678';
  setup.payment.reference = ' ';
  await setup.submitPayment();
  assert.equal(calls, 0);
  assert.match(setup.feedback, /referencia de pago es obligatorio/);
  setup.payment.reference = 'PAY-1';
  const pending = setup.submitPayment();
  await setup.submitPayment();
  assert.equal(calls, 1);
  rejectSave(new Error('Servicio no disponible'));
  await pending;
  assert.equal(setup.feedback, 'Servicio no disponible');
  assert.equal(setup.isSubmitting, false);
  assert.equal(setup.payment.reference, 'PAY-1');
  assert.equal(gym.cart.length, 1);
});

test('checkout accepts the contact email of a client account outside the sign-up domains', async () => {
  const { setup, gym } = await setupView('StorePaymentView', '/tienda/pago');
  gym.cart = [{ id_producto: 1, nombre: 'Agua', precio: 3, cantidad: 1 }];
  Object.assign(setup.payment, { customerName: 'Ana', customerEmail: 'socio@outlook.com', dni: '12345678', method: 'yape', reference: 'PAY-1' });
  const sent = [];
  gym.createStoreOrder = async (order) => { sent.push(order); throw new Error('Servicio no disponible'); };
  await setup.submitPayment();
  assert.equal(sent.length, 1);
  assert.equal(sent[0].cliente_correo, 'socio@outlook.com');
  assert.equal(setup.feedback, 'Servicio no disponible');
});

test('client quantities never exceed the available stock and out-of-stock products are shown as unavailable', async () => {
  const { setup, gym } = await setupView('StoreView', '/user/store');
  const product = { id_producto: 1, nombre: 'Toalla', precio: 10, cantidad: 3, estado: 'Disponible' };
  const soldOut = { id_producto: 2, nombre: 'Guantes', precio: 5, cantidad: 0, estado: 'Agotado' };
  gym.productos_tienda = [
    soldOut,
    product,
    { id_producto: 3, nombre: 'Gorra', precio: 0, cantidad: 4, estado: 'Descatalogado' },
    { id_producto: 4, nombre: 'Mochila', precio: 20, cantidad: 2, estado: 'Disponible', archivado: true },
  ];
  assert.deepEqual(setup.catalogProducts.map((p) => p.id_producto), [2, 1]);
  assert.deepEqual(setup.visibleProducts.map((p) => p.id_producto), [1, 2]);
  assert.equal(setup.canBuy(soldOut), false);
  setup.agregarAlCarrito(soldOut);
  assert.equal(gym.cart.length, 0);
  assert.match(setup.feedbackMessage, /no está disponible/);
  const event = { target: { value: '9' } };
  setup.setQuantity(product, event);
  assert.equal(event.target.value, '3');
  assert.equal(setup.cantidadInput[1], 3);
  assert.match(setup.stockWarning[1], /Solo hay 3/);
  setup.agregarAlCarrito(product);
  assert.equal(gym.cart[0].cantidad, 3);
  assert.equal(setup.availableFor(product), 0);
  setup.updateCart(1, '9');
  assert.equal(gym.cart[0].cantidad, 3);
});
