<template>
  <div class="rounded-smoother border-2 border-primary/20 bg-primary/5 p-5 shadow-lg shadow-primary/10">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-sm uppercase tracking-widest text-primary/70 font-semibold">{{ label }}</p>
        <p class="mt-3 text-4xl font-bold text-gray-800">{{ value }}</p>
        <p class="mt-2 text-sm text-gray-600">{{ description }}</p>
      </div>
      <div class="flex h-14 w-14 items-center justify-center rounded-smooth bg-primary/15 text-2xl">
        {{ icon }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    default: '★',
  },
});
</script>
