import { apiPost } from './backendGateway.js';

export const retryActivationEmail = (clientId, token) =>
  apiPost(`/clientes/${clientId}/notificar-activacion`, {}, token);
export const startClientPayment = (clientId, token) =>
  apiPost(`/clientes/${clientId}/pago-stripe`, {}, token);
export const confirmMembershipPayment = (sessionId, token) =>
  apiPost(`/pagos/stripe/confirmar-retorno?session_id=${encodeURIComponent(sessionId)}`, {}, token);
