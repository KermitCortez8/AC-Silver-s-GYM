import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../application/stores/authStore.js';
import { createChatbotService } from '../../application/services/chatbotService.js';

export function useChatbot(customChatService = null) {
  const router = useRouter();
  const authStore = useAuthStore();
  let chatServiceInstance = customChatService;

  const getChatService = () => {
    if (!chatServiceInstance) {
      chatServiceInstance = createChatbotService();
    }
    return chatServiceInstance;
  };

  const isOpen = ref(false);
  const conversationId = ref(null);
  const messages = ref([]);
  const quickReplies = ref([]);
  const isTyping = ref(false);
  const isSlow = ref(false);
  const currentState = ref('ok');

  // Rate Limiting
  const isRateLimited = ref(false);
  const rateLimitSeconds = ref(0);
  const messageTimestamps = ref([]);
  let rateLimitInterval = null;
  let slowTimer = null;
  let inactivityTimer = null;
  const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutos

  const lastUserMessage = ref('');

  const initialQuickReplies = [
    { label: 'Ver planes y membresías', action: 'planes' },
    { label: 'Consultar horarios de clases', action: 'horarios' },
    { label: 'Suplementos y productos', action: 'tienda' },
    { label: 'Hablar con recepción', action: 'contact_human' },
  ];

  const resetInactivityTimer = () => {
    if (inactivityTimer) clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
      // Inactividad de 30 minutos cumplida: resetear ID de conversación
      conversationId.value = null;
    }, INACTIVITY_TIMEOUT_MS);
  };

  const getInitialMessage = () => {
    const greeting =
      authStore.isAuthenticated && authStore.user?.name
        ? `¡Hola ${authStore.user.name.split(' ')[0]}! Bienvenido de vuelta a Silver Gym Surco.`
        : '¡Hola! Bienvenido a Silver Gym Surco. Soy Silver, tu asistente virtual con inteligencia artificial.';

    return {
      id: `bot-init-${Date.now()}`,
      sender: 'bot',
      blocks: [
        {
          type: 'text',
          text: `${greeting}\n\nPuedo ayudarte con horarios, planes, productos y resolver tus dudas al instante. ¿Qué te gustaría consultar?`,
        },
      ],
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };
  };

  const initChat = () => {
    if (messages.value.length === 0) {
      messages.value = [getInitialMessage()];
      quickReplies.value = [...initialQuickReplies];
    }
  };

  const startRateLimitCountdown = (seconds = 40) => {
    isRateLimited.value = true;
    rateLimitSeconds.value = Math.max(1, seconds);

    if (rateLimitInterval) clearInterval(rateLimitInterval);
    rateLimitInterval = setInterval(() => {
      rateLimitSeconds.value -= 1;
      if (rateLimitSeconds.value <= 0) {
        clearInterval(rateLimitInterval);
        rateLimitInterval = null;
        isRateLimited.value = false;
        rateLimitSeconds.value = 0;
      }
    }, 1000);
  };

  const openChat = () => {
    isOpen.value = true;
    initChat();
    resetInactivityTimer();
  };

  const closeChat = () => {
    isOpen.value = false;
  };

  const toggleChat = () => {
    if (isOpen.value) {
      closeChat();
    } else {
      openChat();
    }
  };

  const goToLogin = () => {
    closeChat();
    if (router) {
      router.push('/login');
    } else {
      window.location.href = '/login';
    }
  };

  const openWhatsAppReception = () => {
    const phone = '51912794583';
    const text = encodeURIComponent(
      'Hola recepción de Silver Gym Surco, quisiera realizar una consulta.'
    );
    window.open(`https://wa.me/${phone}?text=${text}`, '_blank', 'noopener,noreferrer');
  };

  const sendMessage = async (text, action = null) => {
    resetInactivityTimer();

    if (isRateLimited.value) {
      return;
    }

    // Regla de ráfaga en cliente: máximo 10 msg/min cliente, 5 msg/min visitante
    const now = Date.now();
    messageTimestamps.value = messageTimestamps.value.filter(
      (t) => now - t < 60000
    );
    messageTimestamps.value.push(now);

    const clientMaxPerMin = authStore.isAuthenticated ? 10 : 5;
    if (messageTimestamps.value.length > clientMaxPerMin) {
      startRateLimitCountdown(40);
      messages.value.push({
        id: `rate-limit-${now}`,
        sender: 'bot',
        blocks: [
          {
            type: 'notice',
            kind: 'rate_limit',
            text: 'Has enviado demasiados mensajes muy rápido.',
            retryInSeconds: 40,
          },
        ],
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });
      return;
    }

    const messageContent = action ? `[Acción: ${action}]` : text || '';
    if (action === 'contact_human') {
      openWhatsAppReception();
      messages.value.push({
        id: `user-${now}`,
        sender: 'user',
        text: 'Hablar con recepción',
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });
      messages.value.push({
        id: `bot-contact-${now}`,
        sender: 'bot',
        blocks: [
          {
            type: 'contact',
            phone: '+51 912 794 583',
            attentionHours:
              'Lun a Sáb de 6:00 am a 10:00 pm · Dom de 8:00 am a 2:00 pm',
          },
        ],
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });
      return;
    }

    if (!messageContent.trim()) return;

    lastUserMessage.value = messageContent;

    messages.value.push({
      id: `user-${now}`,
      sender: 'user',
      text: text || action,
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    });

    isTyping.value = true;
    isSlow.value = false;

    if (slowTimer) clearTimeout(slowTimer);
    slowTimer = setTimeout(() => {
      isSlow.value = true;
    }, 15000);

    try {
      const token = authStore.token || '';
      const service = getChatService();
      const response = await service.sendMessage({
        message: messageContent,
        conversationId: conversationId.value,
        token,
      });

      if (slowTimer) clearTimeout(slowTimer);
      isTyping.value = false;
      isSlow.value = false;

      if (response && response.conversation_id) {
        conversationId.value = response.conversation_id;
      }

      currentState.value = (response && response.state) || 'ok';

      if (response && response.state === 'rate_limited') {
        startRateLimitCountdown(60);
      }

      messages.value.push({
        id: `bot-${Date.now()}`,
        sender: 'bot',
        blocks: (response && response.blocks) || [],
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });

      if (response && response.quick_replies && response.quick_replies.length > 0) {
        quickReplies.value = response.quick_replies.map((qr) => ({
          label: qr.label || qr.titulo,
          action: qr.action || qr.payload || qr.label,
        }));
      } else if (response && response.state === 'basic_mode') {
        quickReplies.value = [...initialQuickReplies];
      } else {
        quickReplies.value = [];
      }
    } catch (err) {
      if (slowTimer) clearTimeout(slowTimer);
      isTyping.value = false;

      const status = err?.status || (err?.message?.includes('429') ? 429 : 0);
      const code = err?.code || '';

      if (status === 429 || code === 'rate_limit_exceeded') {
        const seconds = err?.retryAfterSeconds || 60;
        startRateLimitCountdown(seconds);
        messages.value.push({
          id: `bot-err-${Date.now()}`,
          sender: 'bot',
          blocks: [
            {
              type: 'notice',
              kind: 'rate_limit',
              text: err.message || 'Has alcanzado el límite temporal de mensajes.',
              retryInSeconds: seconds,
            },
          ],
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        });
        return;
      }

      if (status === 401 || code === 'session_expired') {
        messages.value.push({
          id: `bot-err-${Date.now()}`,
          sender: 'bot',
          blocks: [
            {
              type: 'notice',
              kind: 'session_expired',
              text: 'Tu sesión ha vencido o requiere validación. Inicia sesión nuevamente para continuar.',
            },
          ],
          timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        });
        return;
      }

      messages.value.push({
        id: `bot-err-${Date.now()}`,
        sender: 'bot',
        blocks: [
          {
            type: 'text',
            text:
              err?.message ||
              'Ocurrió un inconveniente al conectar con el asistente. Intenta de nuevo en unos momentos o contáctanos por WhatsApp.',
          },
          {
            type: 'contact',
            phone: '+51 912 794 583',
            attentionHours: 'Lun a Sáb de 6:00 am a 10:00 pm',
          },
        ],
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      });
    }
  };

  const retryLastMessage = () => {
    isSlow.value = false;
    if (lastUserMessage.value) {
      sendMessage(lastUserMessage.value);
    } else {
      sendMessage('Hola, información de planes');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && isOpen.value) {
      closeChat();
    }
  };

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyDown);
    }
  });

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', handleKeyDown);
    }
    if (rateLimitInterval) clearInterval(rateLimitInterval);
    if (slowTimer) clearTimeout(slowTimer);
    if (inactivityTimer) clearTimeout(inactivityTimer);
  });

  return {
    isOpen,
    conversationId,
    messages,
    quickReplies,
    isTyping,
    isSlow,
    currentState,
    isRateLimited,
    rateLimitSeconds,
    isAuthenticated: computed(() => authStore.isAuthenticated),
    openChat,
    closeChat,
    toggleChat,
    sendMessage,
    retryLastMessage,
    goToLogin,
    openWhatsAppReception,
  };
}
