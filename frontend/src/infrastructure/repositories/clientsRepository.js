/** Operaciones de clients: devuelve datos y mantiene HTTP en infraestructura. */
import { dataRequest } from './dataRequest.js';
export const createClientsRepository = (http, apiBase) => ({
  registerAdmin: (payload, token) => dataRequest(http, `${apiBase}/clientes/registro-admin`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  upsertMember: (body, token) => dataRequest(http, `${apiBase}/clientes`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  deleteMember: (id_cliente, token) => dataRequest(http, `${apiBase}/clientes/${id_cliente}`, {
    method: 'DELETE'
  }, token),
  upsertClienteToServer: (clientePayload, token) => dataRequest(http, `${apiBase}/clientes`, {
    method: 'POST',
    body: JSON.stringify(clientePayload)
  }, token),
  registerClienteMembresiaToServer: (payload, token) => dataRequest(http, `${apiBase}/registro-cliente-membresia`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  registerPublicClient: (payload, token) => dataRequest(http, `${apiBase}/registro-publico`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  confirmarPagoEfectivo: (idCliente, token) => dataRequest(http, `${apiBase}/clientes/${idCliente}/confirmar-pago-manual`, {
    method: 'POST'
  }, token)
});
