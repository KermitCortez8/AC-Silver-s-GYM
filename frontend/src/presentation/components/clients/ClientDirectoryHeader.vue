<template>
  <header class="ws-panel ws-hero ws-toolbar">
    <div>
      <p class="ws-eyebrow">Administración · Clientes</p>
      <h1 class="ws-title">Tu comunidad, en un solo lugar</h1>
      <p class="ws-description">Encuentra a cada cliente y gestiona sus pagos y membresías.</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <button type="button" class="ws-btn" @click="showPaymentRequests = true">Solicitudes de pago</button>
      <button type="button" class="ws-btn ws-primary" @click="$emit('nuevo')">
        <Plus :size="18" aria-hidden="true" /> Nuevo cliente
      </button>
    </div>
  </header>

  <ExternalPaymentRequestsDialog
    v-if="showPaymentRequests" :token="token"
    @close="showPaymentRequests = false" @confirmado="$emit('pago-confirmado', $event, true)"
  />
</template>

<script setup>
import { defineAsyncComponent, ref } from 'vue';
import { Plus } from 'lucide-vue-next';

defineProps({ token: String });
defineEmits(['nuevo', 'pago-confirmado']);
const ExternalPaymentRequestsDialog = defineAsyncComponent(() => import('./ExternalPaymentRequestsDialog.vue'));
const showPaymentRequests = ref(false);
</script>
