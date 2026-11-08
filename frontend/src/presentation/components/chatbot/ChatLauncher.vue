<template>
  <div
    v-if="!isOpen"
    class="fixed bottom-6 right-6 md:bottom-8 md:right-8 z-40 flex items-center justify-end pointer-events-auto"
    data-purpose="floating-chat-trigger"
  >
    <button
      type="button"
      @click="$emit('open')"
      aria-label="Abrir asistente de IA Pregúntale a Silver"
      class="group relative flex items-center h-14 bg-[#DC2626] hover:bg-[#B91C1C] text-white rounded-full shadow-[0_10px_30px_-5px_rgba(220,38,38,0.5)] hover:shadow-[0_15px_35px_-5px_rgba(220,38,38,0.7)] transition-all duration-300 ease-out focus:outline-none focus:ring-4 focus:ring-[#DC2626]/40 cursor-pointer overflow-hidden p-3.5 select-none"
    >
      <!-- Icono de chat que gira a la izquierda en hover -->
      <div
        class="flex items-center justify-center w-7 h-7 flex-shrink-0 transition-transform duration-300 ease-out group-hover:-rotate-12 group-hover:scale-110"
      >
        <svg
          aria-hidden="true"
          class="w-6 h-6 text-white drop-shadow-sm"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            fill-rule="evenodd"
            clip-rule="evenodd"
            d="M4.848 2.771A49.144 49.144 0 0112 2.25c2.43 0 4.817.177 7.152.521 1.944.287 3.348 1.954 3.348 3.924v6.554c0 1.97-1.404 3.637-3.348 3.924a50.944 50.944 0 01-3.655.437v3.09a.75.75 0 01-1.28.53l-3.353-3.352a48.74 48.74 0 01-3.864-.71C4.348 16.35 2.944 14.683 2.944 12.713V6.695c0-1.97 1.404-3.637 3.348-3.924z"
          />
        </svg>
      </div>

      <!-- Texto expandible que aparece y se retrae suavemente -->
      <span
        class="max-w-0 opacity-0 group-hover:max-w-[200px] group-hover:opacity-100 group-hover:pl-2.5 group-hover:pr-1.5 transition-all duration-300 ease-out text-sm font-bold tracking-wide whitespace-nowrap overflow-hidden font-inter leading-none"
      >
        Pregúntale a Silver
      </span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['open']);
</script>
