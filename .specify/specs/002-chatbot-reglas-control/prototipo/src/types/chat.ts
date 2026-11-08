/**
 * Contrato de datos y tipos para el chatbot de Silver Gym Surco (Vista Usuario / Móvil)
 * Conforme a las historias HU-CB01 a HU-CB17.
 */

export type ChatState =
  | 'ok'
  | 'rate_limited'
  | 'slow'
  | 'basic_mode'
  | 'session_expired'
  | 'forbidden';

export interface ScheduleItem {
  id: string;
  service: string;
  day: string;
  start: string;
  end: string;
  slotsLeft: number;
}

export interface ProductBasic {
  id: string;
  name: string;
  category: string;
  imageUrl?: string;
  available: boolean;
}

export type Block =
  | { type: 'text'; text: string }
  | { type: 'schedule_list'; items: ScheduleItem[] }
  | { type: 'product_basic_list'; items: ProductBasic[] }
  | { type: 'contact'; phone: string; whatsappUrl: string; attentionHours: string }
  | { type: 'notice'; kind: 'rate_limit' | 'basic_mode' | 'session_expired'; text: string; retryInSeconds?: number };

export interface QuickReply {
  label: string;
  action: string;
}

export interface ChatResponse {
  conversationId: string;
  blocks: Block[];
  quickReplies: QuickReply[];
  state: ChatState;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text?: string;
  blocks?: Block[];
  timestamp: string;
}

export interface SendMessageParams {
  conversationId: string;
  text?: string;
  action?: string;
  forcedState?: ChatState;
}
