/**
 * Cliente HTTP para el Chatbot de Silver Gym Surco (SWGACSGYM).
 * Conecta con el endpoint POST /api/chatbot/message según contracts/control.md.
 */

export class ChatbotApiError extends Error {
  constructor(message, status = 500, detail = null) {
    super(message);
    this.name = 'ChatbotApiError';
    this.status = status;
    this.detail = detail;
    this.code = detail?.code || `HTTP_${status}`;
    this.retryAfterSeconds = detail?.retry_after_seconds || (status === 429 ? 40 : 0);
  }
}

export const createHttpChatService = (customConfig = null) => {
  const getBaseUrl = () => {
    if (customConfig && customConfig.authApiBaseUrl !== undefined) {
      return customConfig.authApiBaseUrl;
    }
    try {
      if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_AUTH_API_BASE_URL) {
        return import.meta.env.VITE_AUTH_API_BASE_URL.trim().replace(/\/$/, '');
      }
    } catch {
      // Entorno sin import.meta.env
    }
    return '';
  };

  /**
   * Envía un mensaje o acción al chatbot.
   * @param {Object} params
   * @param {string} [params.message]
   * @param {string} [params.conversationId]
   * @param {Object} [params.clientContext]
   * @param {string} [params.token]
   * @param {AbortSignal} [params.signal]
   * @returns {Promise<Object>}
   */
  const sendMessage = async ({
    message,
    conversationId,
    clientContext = {},
    token = '',
    signal = null,
  }) => {
    const baseUrl = getBaseUrl();
    const endpoint = `${baseUrl}/api/chatbot/message`;

    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const payload = {
      message: message || '',
      conversation_id: conversationId || null,
      client_context: {
        current_path: clientContext.current_path || (typeof window !== 'undefined' ? window.location?.pathname : '/'),
        device: clientContext.device || (typeof window !== 'undefined' && window.innerWidth < 768 ? 'mobile' : 'desktop'),
      },
    };

    let response;
    try {
      response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal,
      });
    } catch (networkError) {
      if (networkError.name === 'AbortError') {
        throw networkError;
      }
      throw new ChatbotApiError(
        'No se pudo conectar con el servidor. Revisa tu conexión a internet.',
        0,
        { code: 'NETWORK_ERROR' }
      );
    }

    if (!response.ok) {
      let detail = null;
      try {
        const errorJson = await response.json();
        detail = errorJson.detail || errorJson;
      } catch {
        detail = { message: `Error HTTP ${response.status}` };
      }

      const errorMessage =
        typeof detail === 'object' && detail?.message
          ? detail.message
          : typeof detail === 'string'
          ? detail
          : `Error del servidor (${response.status})`;

      throw new ChatbotApiError(errorMessage, response.status, detail);
    }

    return await response.json();
  };

  return {
    sendMessage,
  };
};

export const defaultHttpChatService = createHttpChatService();
