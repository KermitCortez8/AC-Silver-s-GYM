import { createBackendGateway } from './backendGateway.js';

export const createChatbotService = (gateway = createBackendGateway()) => ({
  sendMessage: async ({
    message,
    conversationId,
    clientContext = {},
    token = '',
  }) => {
    const payload = {
      message: message || '',
      conversation_id: conversationId || null,
      client_context: {
        current_path:
          clientContext.current_path ||
          (typeof window !== 'undefined' ? window.location?.pathname : '/'),
        device:
          clientContext.device ||
          (typeof window !== 'undefined' && window.innerWidth < 768
            ? 'mobile'
            : 'desktop'),
      },
    };

    return await gateway.apiPost('/chatbot/message', payload, token);
  },
});
