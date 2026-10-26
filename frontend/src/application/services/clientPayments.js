import { createBackendGateway } from "./backendGateway.js";

export const useClientPayments = (gateway = createBackendGateway()) => ({
  retryActivationEmail: (clientId, token) =>
    gateway.apiPost(`/clientes/${clientId}/notificar-activacion`, {}, token),
  startClientPayment: (clientId, token) =>
    gateway.apiPost(`/clientes/${clientId}/pago-stripe`, {}, token),
  confirmMembershipPayment: (sessionId, token) =>
    gateway.apiPost(
      `/pagos/stripe/confirmar-retorno?session_id=${encodeURIComponent(sessionId)}`,
      {},
      token,
    ),
});
