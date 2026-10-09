<template>
  <nav v-if="pageCount > 1" class="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400" aria-label="Paginación de la tabla">
    <span>{{ total }} registros · Página {{ page }} de {{ pageCount }}</span>
    <div class="flex gap-2">
      <button type="button" class="rounded-xl border border-white/10 px-4 py-2 font-bold text-white hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40" :disabled="page <= 1" @click="$emit('update:page', page - 1)">Anterior</button>
      <button type="button" class="rounded-xl border border-white/10 px-4 py-2 font-bold text-white hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40" :disabled="page >= pageCount" @click="$emit('update:page', page + 1)">Siguiente</button>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  page: { type: Number, required: true },
  pageCount: { type: Number, required: true },
  total: { type: Number, required: true },
});
defineEmits(['update:page']);
</script>
