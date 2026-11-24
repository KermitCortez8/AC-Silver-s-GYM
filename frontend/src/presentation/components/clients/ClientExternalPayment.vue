<template>
  <section class="space-y-4" aria-label="Pago pendiente de verificación">
    <ExternalPaymentInstructions v-if="payment" :payment="payment" />
    <button v-else type="button" class="ws-btn" :disabled="loading" @click="loadInstructions">
      {{ loading ? 'Cargando…' : 'Ver QR o enlace de pago' }}
    </button>
    <p v-if="instructionsError" class="ws-danger text-sm" role="alert">{{ instructionsError }}</p>
    <ExternalPaymentReceipt :busy="busy" :error="error" @confirmar="confirmPayment" />
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useClientPayments } from '../../../application/services/clientPayments.js';
import ExternalPaymentInstructions from './ExternalPaymentInstructions.vue';
import ExternalPaymentReceipt from './ExternalPaymentReceipt.vue';

const props = defineProps({ client: { type: Object, required: true }, token: String });
const emit = defineEmits(['confirmado']);
const { loadExternalPayment, confirmExternalPayment } = useClientPayments();
const payment = ref(props.client.payment?.revision_pendiente ? props.client.payment : null);
const loading = ref(false);
const busy = ref(false);
const error = ref('');
const instructionsError = ref('');

async function loadInstructions() {
  loading.value = true;
  instructionsError.value = '';
  try {
    payment.value = await loadExternalPayment(props.client.id_cliente, props.token);
  } catch (e) {
    instructionsError.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function confirmPayment(receipt) {
  if (busy.value) return;
  busy.value = true;
  error.value = '';
  try {
    const result = await confirmExternalPayment(props.client.id_cliente, {
      ...receipt, id_membresia: props.client.id_membresia,
    }, props.token);
    emit('confirmado', result);
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>
