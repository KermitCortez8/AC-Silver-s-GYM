<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full pt-1" data-purpose="product-basic-list">
    <article
      v-for="product in items"
      :key="product.id"
      class="bg-white border border-gray-200 rounded-2xl p-3 shadow-sm flex items-center gap-3 hover:border-gray-300 transition-all"
      data-purpose="product-card-basic"
    >
      <!-- Miniatura con fallback seguro -->
      <div class="w-14 h-14 rounded-xl bg-stone-100 flex-shrink-0 overflow-hidden flex items-center justify-center border border-gray-100 relative">
        <img
          v-if="product.imageUrl && !imageErrors[product.id]"
          :src="product.imageUrl"
          :alt="product.name"
          class="w-full h-full object-cover"
          @error="handleImageError(product.id)"
          referrerpolicy="no-referrer"
        />
        <div v-else class="w-full h-full bg-red-50 text-[#DC2626] flex items-center justify-center">
          <svg
            class="w-6 h-6 text-[#DC2626]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.75"
              d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
            />
          </svg>
        </div>
      </div>

      <!-- Datos básicos -->
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-bold text-gray-900 leading-snug truncate">
          {{ product.name }}
        </h4>
        <p class="text-[11px] text-gray-500 font-medium truncate mt-0.5">
          {{ product.category }}
        </p>

        <!-- Badge de Disponibilidad -->
        <div class="mt-1.5">
          <span
            v-if="product.available"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
          >
            Disponible
          </span>
          <span
            v-else
            class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-gray-100 text-gray-500 border border-gray-200"
          >
            Agotado
          </span>
        </div>
      </div>
    </article>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
});

const imageErrors = ref({});

const handleImageError = (id) => {
  imageErrors.value[id] = true;
};
</script>
