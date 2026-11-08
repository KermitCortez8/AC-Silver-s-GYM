<template>
  <Transition name="chat-window">
    <aside
      v-if="isOpen"
      aria-label="Asistente Virtual Silver Gym Surco"
      class="fixed inset-0 z-50 md:inset-auto md:bottom-6 md:right-8 bg-black/40 md:bg-transparent md:pointer-events-none flex flex-col justify-end md:block backdrop-blur-xs md:backdrop-blur-none"
      id="silver-chatbot"
    >
      <div
        class="w-full h-[100dvh] md:w-[410px] md:h-[670px] md:max-h-[calc(100vh-40px)] bg-white flex flex-col rounded-t-3xl md:rounded-3xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.3)] border border-gray-200/90 pointer-events-auto overflow-hidden relative"
        data-purpose="chat-viewport"
      >
        <!-- Cabecera estilizada -->
        <ChatHeader @close="handleClose" />

        <!-- Historial de mensajes -->
        <MessageList
          :messages="messages"
          :is-typing="isTyping"
          :is-slow="isSlow"
          :quick-replies="quickReplies"
          @select-quick-reply="handleQuickReply"
          @retry="handleRetry"
          @contact-human="handleContactHuman"
          @login-click="handleLogin"
        />

        <!-- Barra de entrada -->
        <ChatInput
          :disabled="isTyping"
          :is-rate-limited="isRateLimited"
          :rate-limit-seconds="rateLimitSeconds"
          :is-authenticated="isAuthenticated"
          @send-message="handleSendMessage"
          @login-click="handleLogin"
        />
      </div>
    </aside>
  </Transition>
</template>

<script setup>
import { computed, unref } from 'vue';
import ChatHeader from './ChatHeader.vue';
import MessageList from './MessageList.vue';
import ChatInput from './ChatInput.vue';

const props = defineProps({
  chatbot: {
    type: Object,
    required: true,
  },
});

const isOpen = computed(() => Boolean(unref(props.chatbot?.isOpen)));
const messages = computed(() => unref(props.chatbot?.messages) || []);
const isTyping = computed(() => Boolean(unref(props.chatbot?.isTyping)));
const isSlow = computed(() => Boolean(unref(props.chatbot?.isSlow)));
const quickReplies = computed(() => unref(props.chatbot?.quickReplies) || []);
const isRateLimited = computed(() => Boolean(unref(props.chatbot?.isRateLimited)));
const rateLimitSeconds = computed(() => Number(unref(props.chatbot?.rateLimitSeconds)) || 0);
const isAuthenticated = computed(() => Boolean(unref(props.chatbot?.isAuthenticated)));

const handleClose = () => {
  props.chatbot?.closeChat?.();
};

const handleQuickReply = (option) => {
  props.chatbot?.sendMessage?.(option.label, option.action);
};

const handleRetry = () => {
  props.chatbot?.retryLastMessage?.();
};

const handleContactHuman = () => {
  props.chatbot?.openWhatsAppReception?.();
};

const handleLogin = () => {
  props.chatbot?.goToLogin?.();
};

const handleSendMessage = (text) => {
  props.chatbot?.sendMessage?.(text);
};
</script>

<style scoped>
.chat-window-enter-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.chat-window-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 1, 1);
}

@media (min-width: 768px) {
  .chat-window-enter-from,
  .chat-window-leave-to {
    opacity: 0;
    transform: scale(0.92) translateY(24px);
    transform-origin: bottom right;
  }
}

@media (max-width: 767px) {
  .chat-window-enter-from,
  .chat-window-leave-to {
    opacity: 0;
    transform: translateY(100%);
  }
}
</style>
