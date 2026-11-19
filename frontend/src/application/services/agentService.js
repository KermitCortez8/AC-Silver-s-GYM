import { createBackendGateway } from './backendGateway.js';

export const createAgentService = (gateway = createBackendGateway()) => ({
  send(mensaje, id_conversacion = null) {
    return gateway.apiPost('/agente/mensajes', { mensaje, id_conversacion });
  },
});
