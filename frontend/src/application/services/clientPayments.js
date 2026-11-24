import { createBackendGateway } from "./backendGateway.js";

export const useClientPayments = (gateway = createBackendGateway()) => ({
  getAdminRenewalDetails: (clientId, token) => gateway.apiGet(`/clientes/${clientId}/renovacion`, token),
  renewClientMembership: (clientId, payload, token) => gateway.apiPost(`/clientes/${clientId}/renovar-membresia`, payload, token),
  getRenewalDetails: (token) => gateway.apiGet(`/renovacion?token=${encodeURIComponent(token)}`),
  startRenewalPayment: (token, amount) => gateway.apiPost('/renovacion/checkout', { token, monto_pago: amount }),
  retryActivationEmail: (clientId, token) =>
    gateway.apiPost(`/clientes/${clientId}/notificar-activacion`, {}, token),
  startClientPayment: (clientId, token) =>
    gateway.apiPost(`/clientes/${clientId}/pago-stripe`, {}, token),
  loadExternalPayment: (clientId, token) => gateway.apiGet(`/clientes/${clientId}/instrucciones-pago`, token),
  loadExternalRequests: (token) => gateway.apiGet('/preregistros/pagos-pendientes', token),
  confirmExternalRequest: (requestToken, payload, token) =>
    gateway.apiPost(`/preregistros/${encodeURIComponent(requestToken)}/confirmar-pago-externo`, payload, token),
  confirmExternalPayment: (clientId, payload, token) =>
    gateway.apiPost(`/clientes/${clientId}/confirmar-pago-externo`, payload, token),
  confirmMembershipPayment: (sessionId, token) =>
    gateway.apiPost(
      `/pagos/stripe/confirmar-retorno?session_id=${encodeURIComponent(sessionId)}`,
      {},
      token,
    ),
});
