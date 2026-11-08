import { ChatResponse, SendMessageParams } from '../types/chat';

/**
 * Interfaz que define el contrato del servicio de Chatbot para Silver Gym Surco.
 * Permite alternar limpiamente entre MockChatService y HttpChatService.
 */
export interface ChatService {
  sendMessage(params: SendMessageParams): Promise<ChatResponse>;
  getInitialMessage(conversationId: string): ChatResponse;
}
