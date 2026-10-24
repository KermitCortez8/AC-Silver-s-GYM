/** Operaciones de inventory: devuelve datos y mantiene HTTP en infraestructura. */
import { dataRequest } from './dataRequest.js';
export const createInventoryRepository = (http, apiBase) => ({
  deleteInventoryItem: (id_item, token) => dataRequest(http, `${apiBase}/inventario/${id_item}`, {
    method: 'DELETE'
  }, token),
  refreshInventoryMovementsFromBackend: token => dataRequest(http, `${apiBase}/inventario/movimientos`, {}, token),
  upsertInventoryToServer: (payload, token) => dataRequest(http, `${apiBase}/inventario`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  registrarMovimientoToServer: (payload, token) => dataRequest(http, `${apiBase}/inventario/movimientos`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  updateInventoryMovement: (idMov, payload, token) => dataRequest(http, `${apiBase}/inventario/movimientos/${idMov}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  }, token)
});
