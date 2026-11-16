import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

const product = { id_producto: 1, nombre: 'Botella QA', categoria: 'Bebidas', descripcion: 'Botella de prueba',
  precio: 15, cantidad: 10, estado: 'Disponible', imagen_url: 'https://example.com/botella.png' };

test('TC-096: producto incompleto muestra campos requeridos y no llama al servidor', async () => {
  const { setup: s, gym } = await setupView('StoreView', '/admin/store');
  let saves = 0;
  gym.upsertProductoTienda = async () => { saves++; };
  s.openNewProducto();
  await s.handleSubmit();
  assert.match(s.feedbackMessage, /Nombre/);
  assert.match(s.feedbackMessage, /Precio/);
  Object.assign(s.form, { nombre: 'Botella QA', precio: 15, categoria: '' });
  await s.handleSubmit();
  assert.match(s.feedbackMessage, /Categor[ií]a/);
  assert.equal(saves, 0);
  assert.equal(s.isProductEditorOpen, true);
});

test('TC-097: precio negativo y stock fraccionario conservan el borrador sin guardarlo', async () => {
  const { setup: s, gym } = await setupView('StoreView', '/admin/store');
  let saves = 0;
  gym.upsertProductoTienda = async () => { saves++; };
  s.openNewProducto();
  Object.assign(s.form, { nombre: 'Botella QA', categoria: 'Bebidas', precio: '-5', cantidad: 10 });
  await s.handleSubmit();
  assert.equal(s.feedbackTone, 'error');
  assert.equal(s.form.precio, '-5');
  Object.assign(s.form, { precio: 15, cantidad: '1.5' });
  await s.handleSubmit();
  assert.equal(s.feedbackTone, 'error');
  assert.equal(saves, 0);
  assert.equal(s.isProductEditorOpen, true);
});

test('TC-099: catálogo muestra precio, disponibilidad y detalle del producto seleccionado', async () => {
  const { setup: s, gym, html } = await setupView('StoreView', '/user/store', (_s, store) => {
    store.productos_tienda = [product];
  });
  assert.match(html, /Botella QA/);
  assert.match(html, /15\.00/);
  assert.match(html, /Stock: 10/);
  assert.match(html, /Ver detalle de Botella QA/);
  const before = structuredClone(gym.productos_tienda.map(row => ({ ...row })));
  s.openClientDetail(product);
  assert.equal(s.clientDetail.id_producto, 1);
  assert.equal(s.clientDetail.descripcion, 'Botella de prueba');
  assert.deepEqual(gym.productos_tienda.map(row => ({ ...row })), before);
});

test('TC-100: catálogo vacío se presenta explícitamente y una recarga recupera los productos', async () => {
  const { setup: s, gym, html } = await setupView('StoreView', '/user/store');
  assert.match(html, /Pronto encontrarás nuevos productos aquí/);
  assert.equal(s.visibleProducts.length, 0);
  assert.equal(gym.cart.length, 0);
  gym.productos_tienda = [product];
  assert.equal(s.visibleProducts.length, 1);
  const reloaded = await setupView('StoreView', '/user/store', (_s, store) => { store.productos_tienda = [product]; });
  assert.match(reloaded.html, /Botella QA/);
  assert.doesNotMatch(reloaded.html, /Pronto encontrarás nuevos productos aquí/);
});

test('TC-103: cantidad superior al stock se ajusta y muestra un aviso sin crear pedidos', async () => {
  const { setup: s, gym } = await setupView('StoreView', '/user/store');
  gym.productos_tienda = [product];
  const event = { target: { value: '11' } };
  s.setQuantity(product, event);
  assert.equal(Number(s.cantidadInput[1]), 10);
  assert.match(s.stockWarning[1], /Solo hay 10 disponibles/);
  assert.equal(gym.cart.length, 0);
});

test('TC-104: carrito vacío no ofrece procesar compra y la pasarela no inventa productos', async () => {
  const store = await setupView('StoreView', '/user/store');
  assert.match(store.html, /Tu carrito está vacío/);
  assert.doesNotMatch(store.html, /Procesar compra/);
  const payment = await setupView('StorePaymentView', '/user/store/payment');
  assert.match(payment.html, /No hay productos para pagar/);
  assert.equal(payment.gym.cart.length, 0);
});

test('TC-105: cantidades inválidas no entran al carrito ni modifican existencias', async () => {
  const { setup: s, gym } = await setupView('StoreView', '/user/store');
  gym.productos_tienda = [product];
  for (const value of ['-1', '1.5', 'abc']) {
    s.cantidadInput[1] = value;
    s.agregarAlCarrito(product);
    assert.equal(gym.cart.length, 0);
    assert.equal(s.feedbackTone, 'error');
    assert.equal(gym.productos_tienda[0].cantidad, 10);
  }
});
