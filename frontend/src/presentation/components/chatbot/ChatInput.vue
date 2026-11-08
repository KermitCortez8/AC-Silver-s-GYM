<template>
  <footer
    class="flex-none bg-white border-t border-[#E5E7EB] p-3 pb-safe z-20 space-y-2 w-full"
    data-purpose="chat-input-bar"
  >
    <!-- Aviso de inicio de sesión si no está autenticado -->
    <div
      v-if="!isAuthenticated"
      class="bg-stone-50 border border-gray-100 rounded-lg px-3 py-1.5 text-center text-[11px] text-gray-600 leading-tight flex items-center justify-center gap-1 flex-wrap"
    >
      <span>Inicia sesión para consultar tu membresía e inscribirte</span>
      <span class="text-gray-400">•</span>
      <button
        type="button"
        @click="$emit('login-click')"
        class="text-[#DC2626] font-semibold underline hover:text-[#B91C1C] focus:outline-none focus:ring-1 focus:ring-[#DC2626] rounded cursor-pointer"
      >
        Iniciar sesión
      </button>
    </div>

    <!-- Formulario de entrada de texto -->
    <form @submit.prevent="handleSubmit" class="flex items-center gap-2">
      <label for="chat-message-input" class="sr-only">
        Escribe tu pregunta
      </label>
      <div class="relative flex-1">
        <input
          id="chat-message-input"
          ref="inputRef"
          type="text"
          v-model="inputText"
          :maxlength="MAX_CHAR_LENGTH"
          :disabled="disabled || isRateLimited"
          @keydown="handleKeyDown"
          :placeholder="computedPlaceholder"
          :class="[
            'w-full bg-white border border-[#E5E7EB] rounded-2xl px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#DC2626] focus:border-[#DC2626] transition-shadow',
            isRateLimited ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
          ]"
        />
        <!-- Contador de caracteres (hasta 500 chars) -->
        <span
          v-if="inputText.length > 0"
          :class="[
            'absolute right-3.5 top-2.5 text-[10px] tabular-nums font-medium',
            isNearLimit ? 'text-amber-600 font-bold' : 'text-gray-400'
          ]"
        >
          {{ inputText.length }}/{{ MAX_CHAR_LENGTH }}
        </span>
      </div>

      <!-- Botón de envío -->
      <button
        type="submit"
        :disabled="disabled || isRateLimited || !inputText.trim()"
        aria-label="Enviar mensaje"
        :class="[
          'w-11 h-11 flex-shrink-0 rounded-full flex items-center justify-center shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626]',
          disabled || isRateLimited || !inputText.trim()
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-[#DC2626] hover:bg-[#B91C1C] active:scale-95 text-white cursor-pointer'
        ]"
      >
        <svg
          class="w-5 h-5 translate-x-0.5"
          fill="none"
          stroke="currentColor"
          stroke-width="2.2"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
          />
        </svg>
      </button>
    </form>
  </footer>
</template>

<script setup>
import { ref, computed } from 'vue';

const MAX_CHAR_LENGTH = 500;

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  isRateLimited: {
    type: Boolean,
    default: false,
  },
  rateLimitSeconds: {
    type: Number,
    default: 0,
  },
  isAuthenticated: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['send-message', 'login-click']);

const inputText = ref('');
const inputRef = ref(null);

const isNearLimit = computed(() => inputText.value.length > MAX_CHAR_LENGTH * 0.8);

const computedPlaceholder = computed(() => {
  if (props.isRateLimited) {
    return `Bloqueado temporalmente (${props.rateLimitSeconds}s)...`;
  }
  return 'Escribe tu pregunta…';
});

const handleSubmit = () => {
  if (props.disabled || props.isRateLimited) return;
  const trimmed = inputText.value.trim();
  if (!trimmed) return;
  emit('send-message', trimmed);
  inputText.value = '';
};

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSubmit();
  }
};

defineExpose({
  focus: () => inputRef.value?.focus(),
});
</script>
