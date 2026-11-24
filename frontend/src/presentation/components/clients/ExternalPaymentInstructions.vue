<template>
  <div class="external-payment space-y-3 rounded-xl border p-4" aria-label="Instrucciones de pago">
    <p class="text-sm font-bold">{{ etiquetaPagoExterno(payment.medio_pago) }} · S/ {{ Number(payment.amount).toFixed(2) }}</p>
    <template v-if="payment.qr_url">
      <img :src="payment.qr_url" alt="Código QR de Yape del gimnasio" width="176" height="176" class="rounded-md bg-white object-contain" />
      <p class="text-sm">Escanea el QR desde Yape o Plin y envía el importe indicado.</p>
    </template>
    <a v-else-if="payment.enlace" :href="payment.enlace" target="_blank" rel="noopener noreferrer"
      class="inline-block rounded-lg bg-[var(--app-accent)] px-4 py-2 text-sm font-bold text-white"
    >Abrir enlace de Mercado Pago</a>
    <p class="text-sm">El pago queda pendiente hasta que recepción verifique el abono.</p>
  </div>
</template>

<script setup>
import { etiquetaPagoExterno } from '../../../domain/utils/membershipPaymentMethods.js';

defineProps({ payment: { type: Object, required: true } });
</script>

<style scoped>
.external-payment {
  color: var(--app-text);
  background: var(--app-input);
  border-color: var(--app-border);
}
</style>
