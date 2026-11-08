import { useState, useEffect, useRef, useCallback } from 'react';
import { ChatMessage, ChatResponse, ChatState, QuickReply } from '../types/chat';
import { MockChatService } from '../services/mockChatService';

const mockService = new MockChatService();

export function useChatbot(isOpen: boolean, onClose: () => void) {
  const [conversationId] = useState<string>(() => `conv-${Date.now()}`);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [isSlow, setIsSlow] = useState<boolean>(false);

  // Rate Limiting
  const [messageTimestamps, setMessageTimestamps] = useState<number[]>([]);
  const [isRateLimited, setIsRateLimited] = useState<boolean>(false);
  const [rateLimitSeconds, setRateLimitSeconds] = useState<number>(0);

  // Estado especial forzado (para DEMO_MODE)
  const [forcedState, setForcedState] = useState<ChatState>('ok');
  const lastUserTextRef = useRef<string>('');
  const slowTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Inicializar conversación al abrir
  useEffect(() => {
    if (messages.length === 0) {
      const initial: ChatResponse = mockService.getInitialMessage(conversationId);
      setMessages([
        {
          id: `msg-${Date.now()}`,
          sender: 'bot',
          blocks: initial.blocks,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setQuickReplies(initial.quickReplies);
    }
  }, [conversationId, messages.length]);

  // Manejo de temporizador de Rate Limiting
  useEffect(() => {
    if (rateLimitSeconds > 0) {
      const interval = setInterval(() => {
        setRateLimitSeconds((prev) => {
          if (prev <= 1) {
            setIsRateLimited(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [rateLimitSeconds]);

  // Atajo de teclado: Escape cierra el chat
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Manejo del botón atrás del navegador en móvil
  useEffect(() => {
    if (!isOpen) return;

    // Agregar estado de historial para que el botón atrás cierre el modal
    window.history.pushState({ chatOpen: true }, '');

    const handlePopState = () => {
      onClose();
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [isOpen, onClose]);

  // Enviar mensaje o ejecutar acción
  const sendMessage = useCallback(
    async (text?: string, action?: string, explicitForcedState?: ChatState) => {
      const stateToApply = explicitForcedState ?? forcedState;

      // Si está en rate limit no permitir envío
      if (isRateLimited) return;

      const now = Date.now();
      const recentTimestamps = messageTimestamps.filter((t) => now - t < 60000);
      recentTimestamps.push(now);
      setMessageTimestamps(recentTimestamps);

      // Regla de Rate Limit: > 10 mensajes en 1 minuto
      if (recentTimestamps.length > 10 || stateToApply === 'rate_limited') {
        setIsRateLimited(true);
        setRateLimitSeconds(40);
        const rateLimitResponse = await mockService.sendMessage({
          conversationId,
          forcedState: 'rate_limited',
        });
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${Date.now()}`,
            sender: 'bot',
            blocks: rateLimitResponse.blocks,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
        return;
      }

      // Si viene texto del usuario, agregarlo al historial
      if (text) {
        lastUserTextRef.current = text;
        const userMsg: ChatMessage = {
          id: `user-${Date.now()}`,
          sender: 'user',
          text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, userMsg]);
      }

      setIsTyping(true);
      setIsSlow(false);

      // Configurar temporizador de lentitud (> 15 segundos)
      if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
      slowTimerRef.current = setTimeout(() => {
        setIsSlow(true);
      }, 15000);

      try {
        const response: ChatResponse = await mockService.sendMessage({
          conversationId,
          text,
          action,
          forcedState: stateToApply !== 'ok' ? stateToApply : undefined,
        });

        if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
        setIsTyping(false);

        const botMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          blocks: response.blocks,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        setMessages((prev) => [...prev, botMsg]);
        setQuickReplies(response.quickReplies);

        // Si se forzó el estado lento
        if (stateToApply === 'slow') {
          setIsSlow(true);
        }
      } catch (err) {
        if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: 'bot',
            blocks: [
              {
                type: 'text',
                text: 'Ocurrió un inconveniente al procesar tu mensaje. Puedes intentar nuevamente o comunicarte con recepción.',
              },
            ],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    },
    [conversationId, forcedState, isRateLimited, messageTimestamps]
  );

  const retryLastMessage = useCallback(() => {
    setIsSlow(false);
    if (lastUserTextRef.current) {
      sendMessage(lastUserTextRef.current);
    } else {
      sendMessage(undefined, 'gym_hours');
    }
  }, [sendMessage]);

  const contactHuman = useCallback(() => {
    setIsSlow(false);
    sendMessage(undefined, 'contact_human');
  }, [sendMessage]);

  const applyForcedState = useCallback(
    (state: ChatState) => {
      setForcedState(state);
      if (state === 'ok') {
        setIsRateLimited(false);
        setRateLimitSeconds(0);
        setIsSlow(false);
      } else if (state === 'rate_limited') {
        setIsRateLimited(true);
        setRateLimitSeconds(40);
        sendMessage(undefined, undefined, 'rate_limited');
      } else if (state === 'slow') {
        setIsSlow(true);
      } else {
        sendMessage(undefined, undefined, state);
      }
    },
    [sendMessage]
  );

  return {
    messages,
    quickReplies,
    isTyping,
    isSlow,
    isRateLimited,
    rateLimitSeconds,
    forcedState,
    sendMessage,
    retryLastMessage,
    contactHuman,
    applyForcedState,
  };
}
