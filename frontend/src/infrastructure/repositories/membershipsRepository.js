/** Operaciones de memberships: devuelve datos y mantiene HTTP en infraestructura. */
import { dataRequest } from './dataRequest.js';
export const createMembershipsRepository = (http, apiBase) => ({
  upsertPlan: (idPm, body, token) => dataRequest(http, idPm ? `${apiBase}/planes-membresia/${idPm}` : `${apiBase}/planes-membresia`, {
    method: idPm ? 'PUT' : 'POST',
    body: JSON.stringify(body)
  }, token),
  deletePlan: (idPm, token) => dataRequest(http, `${apiBase}/planes-membresia/${idPm}`, {
    method: 'DELETE'
  }, token),
  upsertPromotion: (idPromocion, body, token) => dataRequest(http, idPromocion ? `${apiBase}/promociones/${idPromocion}` : `${apiBase}/promociones`, {
    method: idPromocion ? 'PUT' : 'POST',
    body: JSON.stringify(body)
  }, token),
  deletePromotion: (idPromocion, token) => dataRequest(http, `${apiBase}/promociones/${idPromocion}`, {
    method: 'DELETE'
  }, token),
  assignPlanToMember: (payload, token) => dataRequest(http, `${apiBase}/membresias`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  refreshPromotionsFromBackend: token => dataRequest(http, `${apiBase}/promociones`, {}, token),
  activateClientMembership: (idCliente, token) => dataRequest(http, `${apiBase}/clientes/${idCliente}/activar-membresia`, {
    method: 'POST'
  }, token)
});
