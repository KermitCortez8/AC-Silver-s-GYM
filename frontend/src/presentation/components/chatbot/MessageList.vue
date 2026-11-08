<template>
  <main
    ref="scrollContainerRef"
    class="flex-1 overflow-y-auto bg-[#FAF9F6] px-4 py-4 space-y-4 chat-scroll"
    aria-live="polite"
    aria-atomic="false"
    data-purpose="chat-history"
  >
    <!-- Encabezado de contexto -->
    <div class="text-center my-1">
      <span class="text-[11px] font-medium text-gray-400 bg-white/90 px-3 py-1 rounded-full border border-gray-100 shadow-xs">
        Hoy en Silver Gym Surco
      </span>
    </div>

    <!-- Lista de mensajes -->
    <template v-for="message in safeMessages" :key="message.id">
      <!-- Mensaje del usuario -->
      <UserMessage v-if="message.sender === 'user'" :text="message.text || ''" />

      <!-- Mensaje del bot con bloques polimórficos -->
      <div v-else class="space-y-3 w-full" data-purpose="bot-message-wrapper">
        <template v-for="(block, idx) in message.blocks" :key="idx">
          <!-- Bloque de texto plano -->
          <BotMessage v-if="block.type === 'text'" :text="block.text" />

          <!-- Bloque de horarios -->
          <ScheduleCard v-else-if="block.type === 'schedule_list'" :items="block.items" />

          <!-- Bloque de productos básicos -->
          <ProductCardBasic v-else-if="block.type === 'product_basic_list'" :items="block.items" />

          <!-- Bloque de contacto -->
          <ContactCard
            v-else-if="block.type === 'contact'"
            :phone="block.phone"
            :whatsapp-url="block.whatsappUrl"
            :attention-hours="block.attentionHours"
          />

          <!-- Bloque de aviso especial (rate_limit, basic_mode, session_expired) -->
          <NoticeBanner
            v-else-if="block.type === 'notice'"
            :kind="block.kind"
            :text="block.text"
            :retry-in-seconds="block.retryInSeconds"
            @login-click="$emit('login-click')"
            @contact-click="$emit('contact-human')"
          />
        </template>
      </div>
    </template>

    <!-- Indicador de escritura animado -->
    <TypingIndicator v-if="isTyping" />

    <!-- Demora prolongada (> 15 segundos) -->
    <article
      v-if="isSlow"
      class="bg-stone-100 border border-stone-200 rounded-2xl p-4 shadow-xs space-y-3 max-w-[95%] w-full"
      data-purpose="slow-response-alert"
    >
      <p class="text-sm text-gray-800 font-medium">
        Está tardando más de lo normal. ¿Quieres intentar de nuevo o hablar con una persona?
      </p>
      <div class="flex flex-wrap gap-2 pt-1">
        <button
          type="button"
          @click="$emit('retry')"
          class="inline-flex items-center min-h-[44px] bg-white hover:bg-gray-50 text-gray-800 border border-gray-300 font-semibold text-xs px-4 py-2 rounded-full shadow-xs active:scale-95 transition-all focus:outline-none focus:ring-2 focus:ring-[#DC2626] cursor-pointer"
        >
          <svg class="w-3.5 h-3.5 mr-1.5 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Reintentar
        </button>
        <button
          type="button"
          @click="$emit('contact-human')"
          class="inline-flex items-center min-h-[44px] bg-[#DC2626] hover:bg-[#B91C1C] text-white font-semibold text-xs px-4 py-2 rounded-full shadow-xs active:scale-95 transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626] cursor-pointer"
        >
          <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          Hablar con una persona
        </button>
      </div>
    </article>

    <!-- Opciones rápidas interactivas -->
    <QuickReplies
      v-if="!isTyping && quickReplies && quickReplies.length > 0"
      :options="quickReplies"
      :disabled="isTyping"
      @select="(opt) => $emit('select-quick-reply', opt)"
    />

    <!-- Elemento ancla para auto-scroll -->
    <div ref="messagesEndRef" class="h-1" />
  </main>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import BotMessage from './BotMessage.vue';
import UserMessage from './UserMessage.vue';
import TypingIndicator from './TypingIndicator.vue';
import QuickReplies from './QuickReplies.vue';
import ScheduleCard from './cards/ScheduleCard.vue';
import ProductCardBasic from './cards/ProductCardBasic.vue';
import ContactCard from './cards/ContactCard.vue';
import NoticeBanner from './cards/NoticeBanner.vue';

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  isTyping: {
    type: Boolean,
    default: false,
  },
  isSlow: {
    type: Boolean,
    default: false,
  },
  quickReplies: {
    type: Array,
    default: () => [],
  },
});

defineEmits(['select-quick-reply', 'retry', 'contact-human', 'login-click']);

const safeMessages = computed(() => (Array.isArray(props.messages) ? props.messages : []));

const scrollContainerRef = ref(null);
const messagesEndRef = ref(null);

const scrollToBottom = () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
};

watch(
  () => [safeMessages.value.length, props.isTyping, props.isSlow],
  () => {
    scrollToBottom();
  },
  { deep: true }
);
</script>

<style scoped>
.chat-scroll {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}
.chat-scroll::-webkit-scrollbar {
  width: 5px;
}
.chat-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.chat-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
.chat-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
