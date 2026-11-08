<template>
  <nav
    v-if="options && options.length > 0"
    aria-label="Opciones rápidas"
    class="flex flex-col items-start gap-2 pt-1 pb-1 w-full"
    data-purpose="quick-replies"
  >
    <!-- Botón desplegable interactivo para mostrar/ocultar opciones rápidas -->
    <button
      type="button"
      @click="toggleExpand"
      :aria-expanded="isExpanded"
      aria-controls="quick-replies-list"
      class="group inline-flex items-center gap-2 px-3.5 py-2 min-h-[38px] bg-white hover:bg-gray-50 active:bg-gray-100 text-gray-700 hover:text-gray-900 border border-gray-200/90 rounded-full shadow-xs text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-[#DC2626]/40"
    >
      <!-- Ícono vectorial de opciones rápidas (rayo deportivo / acciones) -->
      <svg
        class="w-3.5 h-3.5 text-[#DC2626] transition-transform duration-200 group-hover:scale-110"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>

      <span>Opciones rápidas</span>

      <!-- Badge con cantidad de opciones disponibles -->
      <span
        class="inline-flex items-center justify-center px-1.5 py-0.2 text-[10px] font-bold bg-gray-100 group-hover:bg-red-50 group-hover:text-[#DC2626] text-gray-500 rounded-full transition-colors"
      >
        {{ options.length }}
      </span>

      <!-- Chevron indicador con rotación suave -->
      <svg
        :class="[
          'w-3.5 h-3.5 text-gray-400 transition-transform duration-300 ease-out',
          isExpanded ? 'rotate-180 text-[#DC2626]' : 'rotate-0'
        ]"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Lista desplegable animada de opciones -->
    <Transition name="quick-accordion">
      <div
        v-if="isExpanded"
        id="quick-replies-list"
        class="flex flex-col items-start gap-2 w-full pt-1"
      >
        <button
          v-for="option in options"
          :key="option.action"
          type="button"
          :disabled="disabled"
          @click="selectOption(option)"
          :class="[
            'w-fit max-w-[95%] text-left px-4 py-2.5 min-h-[44px] bg-[#DC2626] hover:bg-[#B91C1C] active:scale-[0.98] text-white text-xs sm:text-sm font-semibold rounded-full shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626] flex items-center justify-between gap-2.5',
            disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
          ]"
        >
          <span class="flex items-center gap-2">
            <!-- Icono de planes / membresías -->
            <svg
              v-if="option.action === 'planes' || option.action === 'activities'"
              class="w-4 h-4 shrink-0 text-white"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>

            <!-- Icono de horarios -->
            <svg
              v-else-if="option.action === 'horarios' || option.action === 'gym_hours' || option.action === 'attention_hours'"
              class="w-4 h-4 shrink-0 text-white"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>

            <!-- Icono de tienda / productos -->
            <svg
              v-else-if="option.action === 'tienda' || option.action === 'products'"
              class="w-4 h-4 shrink-0 text-white"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>

            <!-- Icono de contacto / recepción -->
            <svg
              v-else-if="option.action === 'contact_human'"
              class="w-4 h-4 shrink-0 text-white"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>

            <span>{{ option.label }}</span>
          </span>

          <svg
            class="w-3.5 h-3.5 shrink-0 opacity-70 ml-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  options: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['select', 'toggle']);

const isExpanded = ref(false);

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
  emit('toggle', isExpanded.value);
};

const selectOption = (option) => {
  emit('select', option);
  isExpanded.value = false;
  emit('toggle', false);
};
</script>

<style scoped>
.quick-accordion-enter-active {
  transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}
.quick-accordion-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 1, 1);
}
.quick-accordion-enter-from,
.quick-accordion-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
