<template>
  <Teleport to="body">
    <div
      v-if="open && item"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md"
    >
      <div
        class="w-full max-w-md rounded-3xl border border-white/15 bg-slate-950 p-6 shadow-2xl space-y-4 text-white"
      >
        <h3 class="text-xl font-black text-white">¿Desvincular rutina?</h3>
        <p class="text-xs text-slate-300">
          Se quitará la rutina asignada para el servicio
          <strong>{{ serviceLabel(item.servicio) }}</strong
          >.
        </p>
        <div class="flex justify-end gap-3 pt-3">
          <button
            class="rounded-xl bg-slate-900 border border-white/10 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
            @click="open = false"
          >
            Cancelar
          </button>
          <button
            class="rounded-xl bg-red-600 px-4 py-2 text-xs font-black text-white hover:bg-red-500 transition disabled:opacity-50"
            :disabled="busy"
            @click="$emit('confirm')"
          >
            {{ busy ? 'Desvinculando…' : 'Desvincular' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
import { serviceLabel } from '../../utils/trainerRoutines.js';
const open = defineModel('open', { type: Boolean, default: false });
defineProps({ item: Object, busy: Boolean });
defineEmits(['confirm']);
</script>
