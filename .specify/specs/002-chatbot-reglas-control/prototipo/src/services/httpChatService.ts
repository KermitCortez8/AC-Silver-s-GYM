import { ChatResponse, SendMessageParams } from '../types/chat';
import { ChatService } from './chatService';

/**
 * HttpChatService (Esqueleto para integración futura con FastAPI y Supabase Auth)
 * 
 * Reglas de integración con backend:
 * 1. Envía el token JWT en el encabezado `Authorization: Bearer <jwt_token>`.
 * 2. La identidad del cliente se valida SIEMPRE en el backend a partir del token,
 *    NUNCA a partir del texto que el usuario escribe.
 * 3. Si no hay token presente, la petición se procesa en modo anónimo (Vista Usuario/Pública).
 */
export class HttpChatService implements ChatService {
  private apiUrl: string;
  private getAuthToken?: () => string | null;

  constructor(apiUrl: string = '/api/chatbot/message', getAuthToken?: () => string | null) {
    this.apiUrl = apiUrl;
    this.getAuthToken = getAuthToken;
  }

  public getInitialMessage(conversationId: string): ChatResponse {
    return {
      conversationId,
      blocks: [
        {
          type: 'text',
          text: 'Hola, soy Silver, el asistente con IA de Silver Gym Surco. Puedo ayudarte con horarios, actividades, productos y cómo contactarnos. ¿En qué te ayudo hoy?',
        },
      ],
      quickReplies: [
        { label: 'Horario del gimnasio', action: 'gym_hours' },
        { label: 'Horario de atención', action: 'attention_hours' },
        { label: 'Actividades y cupos', action: 'activities' },
        { label: 'Productos de la tienda', action: 'products' },
        { label: 'Hablar con una persona', action: 'contact_human' },
      ],
      state: 'ok',
    };
  }

  public async sendMessage(params: SendMessageParams): Promise<ChatResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const token = this.getAuthToken ? this.getAuthToken() : null;
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    /*
    const response = await fetch(this.apiUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        conversation_id: params.conversationId,
        message: params.text,
        action: params.action,
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        return {
          conversationId: params.conversationId,
          blocks: [{ type: 'notice', kind: 'session_expired', text: 'Tu sesión ha expirado.' }],
          quickReplies: [],
          state: 'session_expired',
        };
      }
      if (response.status === 429) {
        return {
          conversationId: params.conversationId,
          blocks: [{ type: 'notice', kind: 'rate_limit', text: 'Demasiadas solicitudes.', retryInSeconds: 40 }],
          quickReplies: [],
          state: 'rate_limited',
        };
      }
      throw new Error(`Error en servidor: ${response.statusText}`);
    }

    return await response.json();
    */

    throw new Error('HttpChatService no está activo en modo prototipo. Usa MockChatService.');
  }
}
