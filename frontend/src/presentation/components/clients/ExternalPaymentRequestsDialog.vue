<template>
  <WorkspaceDialog open title="Solicitudes de pago" :busy="busy" @close="$emit('close')">
    <p v-if="loading" role="status">Cargando solicitudes…</p>
    <div v-else-if="loadError" class="space-y-2">
      <p class="ws-danger" role="alert">{{ loadError }}</p>
      <button type="button" class="ws-btn" @click="loadRequests">Reintentar</button>
    </div>
    <template v-else>
      <p v-if="feedback" class="ws-success mb-3" role="status">{{ feedback }}</p>
      <p v-if="!requests.length" class="ws-muted">No hay solicitudes de pago pendientes.</p>
      <ul v-else class="space-y-3">
        <li v-for="request in requests" :key="request.token" class="space-y-3 rounded-xl border ws-border p-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p class="font-bold">{{ request.nombre }}</p>
              <p class="ws-muted text-sm">DNI {{ request.dni }} · {{ etiquetaPagoExterno(request.medio_pago) }} · S/ {{ Number(request.monto_pago).toFixed(2) }}</p>
            </div>
            <button v-if="selected !== request.token" type="button" class="ws-btn" :disabled="busy" @click="select(request.token)">Verificar pago</button>
          </div>
          <ExternalPaymentReceipt v-if="selected === request.token" :busy="busy" :error="error" @confirmar="confirmPayment" />
        </li>
      </ul>
    </template>
  </WorkspaceDialog>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useClientPayments } from '../../../application/services/clientPayments.js';
import { etiquetaPagoExterno } from '../../../domain/utils/membershipPaymentMethods.js';
import WorkspaceDialog from '../WorkspaceDialog.vue';
import ExternalPaymentReceipt from './ExternalPaymentReceipt.vue';

const props = defineProps({ token: String });
const emit = defineEmits(['close', 'confirmado']);
const { loadExternalRequests, confirmExternalRequest } = useClientPayments();
const requests = ref([]);
const selected = ref('');
const feedback = ref('');
const loadError = ref('');
const error = ref('');
const loading = ref(true);
const busy = ref(false);

async function loadRequests() {
  loading.value = true;
  loadError.value = '';
  try {
    requests.value = await loadExternalRequests(props.token);
  } catch (e) {
    loadError.value = e.message;
  } finally {
    loading.value = false;
  }
}

function select(token) {
  selected.value = token;
  error.value = '';
}

async function confirmPayment(receipt) {
  if (busy.value) return;
  const requestToken = selected.value;
  busy.value = true;
  error.value = '';
  try {
    const result = await confirmExternalRequest(requestToken, receipt, props.token);
    requests.value = requests.value.filter((request) => request.token !== requestToken);
    selected.value = '';
    feedback.value = 'Pago confirmado. La membresía queda pendiente de activación.';
    emit('confirmado', result);
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

onMounted(loadRequests);
</script>
