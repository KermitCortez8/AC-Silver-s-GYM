import test from 'node:test';
import assert from 'node:assert/strict';
import { createAgentService } from '../../src/application/services/agentService.js';

test('envía el mensaje al endpoint público con el identificador de conversación', async () => {
  const calls = [];
  const service = createAgentService({
    apiPost: async (...args) => {
      calls.push(args);
      return { id_conversacion: 'c1', texto: 'Mensual: S/ 80', enlaces: [] };
    },
  });
  const response = await service.send('¿Cuánto cuesta el plan?', 'c1');
  assert.equal(response.texto, 'Mensual: S/ 80');
  assert.deepEqual(calls, [['/agente/mensajes', { mensaje: '¿Cuánto cuesta el plan?', id_conversacion: 'c1' }]]);
});
