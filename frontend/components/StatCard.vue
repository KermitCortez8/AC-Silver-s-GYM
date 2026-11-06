<template>
  <div class="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/10 backdrop-blur">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-sm uppercase tracking-[0.3em] text-slate-400">{{ label }}</p>
        <p class="mt-3 text-4xl font-black text-white">{{ value }}</p>
        <p class="mt-2 text-sm text-slate-300">{{ description }}</p>
      </div>
      <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/15 text-2xl">
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
