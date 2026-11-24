<template>
  <form class="space-y-3" @submit.prevent="$emit('confirmar', { operacion, monto_recibido: monto })">
    <p class="ws-muted text-sm">Verifica el abono en el proveedor antes de registrar el pago.</p>
    <div class="grid gap-3 sm:grid-cols-2">
      <label class="space-y-1">
        <span class="block text-sm">Número de operación</span>
        <input v-model.trim="operacion" class="ws-input" required minlength="5" maxlength="80" :disabled="busy" />
      </label>
      <label class="space-y-1">
        <span class="block text-sm">Monto recibido (S/)</span>
        <input v-model="monto" class="ws-input" required type="number" min="0.01" step="0.01" :disabled="busy" />
      </label>
    </div>
    <p v-if="error" class="ws-danger text-sm" role="alert">{{ error }}</p>
    <button type="submit" class="ws-btn ws-primary" :disabled="busy">{{ busy ? 'Confirmando…' : 'Confirmar pago' }}</button>
  </form>
</template>

<script setup>
import { ref } from 'vue';

defineProps({ busy: Boolean, error: { type: String, default: '' } });
defineEmits(['confirmar']);
const operacion = ref('');
const monto = ref('');
</script>
