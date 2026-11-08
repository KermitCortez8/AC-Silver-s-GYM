<template>
  <div class="space-y-2.5 w-full pt-1" data-purpose="schedule-cards-list">
    <article
      v-for="item in items"
      :key="item.id"
      :class="[
        'bg-white border rounded-2xl p-4 shadow-sm transition-all',
        item.slotsLeft > 0
          ? 'border-gray-200 hover:border-red-300'
          : 'border-gray-200 bg-white/70 opacity-80'
      ]"
      :data-purpose="item.slotsLeft > 0 ? 'class-card-available' : 'class-card-full'"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h3 class="text-base font-black tracking-wide text-gray-900 leading-tight uppercase font-oswald">
            {{ item.service }}
          </h3>
          <p class="text-xs text-gray-500 font-medium mt-1 flex items-center gap-1.5">
            <svg
              class="w-3.5 h-3.5 text-gray-400 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
              />
            </svg>
            <span class="truncate">{{ item.day }} · {{ item.start }} a {{ item.end }}</span>
          </p>
        </div>

        <!-- Badge de disponibilidad -->
        <span
          v-if="item.slotsLeft > 0"
          class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0"
        >
          {{ item.slotsLeft }} {{ item.slotsLeft === 1 ? 'cupo disponible' : 'cupos disponibles' }}
        </span>
        <span
          v-else
          class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-500 border border-gray-200 shrink-0"
        >
          Completo
        </span>
      </div>
    </article>
  </div>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
});
</script>
