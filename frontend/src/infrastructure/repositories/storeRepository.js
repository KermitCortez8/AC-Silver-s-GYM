/** Operaciones de store: devuelve datos y mantiene HTTP en infraestructura. */
import { dataRequest } from './dataRequest.js';
export const createStoreRepository = (http, apiBase) => ({
  upsertProductoTienda: (body, token) => dataRequest(http, `${apiBase}/tienda`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  deleteProductoTienda: (id_producto, token) => dataRequest(http, `${apiBase}/tienda/${id_producto}`, {
    method: 'DELETE'
  }, token),
  refreshStoreProductsFromBackend: token => dataRequest(http, `${apiBase}/tienda`, {}, token),
  refreshStoreOrdersFromBackend: token => dataRequest(http, `${apiBase}/tienda/pedidos`, {}, token),
  updateStoreOrderStatus: (idPedido, body, token) => dataRequest(http, `${apiBase}/tienda/pedidos/${idPedido}`, {
    method: 'PUT',
    body: JSON.stringify(body)
  }, token),
  createStoreOrder: (body, token) => dataRequest(http, `${apiBase}/tienda/pedidos`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  createStoreCheckout: (body, token) => dataRequest(http, `${apiBase}/tienda/pedidos/checkout`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  confirmStoreCheckoutReturn: (sessionId, token) => dataRequest(http, `${apiBase}/pagos/stripe/confirmar-retorno?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST'
  }, token),
  cancelStoreCheckout: (idPedido, token) => dataRequest(http, `${apiBase}/tienda/pedidos/${Number(idPedido)}/cancelar-pago`, {
    method: 'POST'
  }, token)
});
