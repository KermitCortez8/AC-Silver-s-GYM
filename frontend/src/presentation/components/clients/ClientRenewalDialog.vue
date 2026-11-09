<template>
  <WorkspaceDialog :open="Boolean(client)" :busy="busy" title="Renovar membresía" @close="$emit('close')">
    <p class="ws-text text-lg font-bold">{{ client?.name || client?.id }}</p>
    <p class="ws-muted mt-1 text-sm">Revisa la compra y el método de pago antes de renovar.</p>
    <p v-if="loading" role="status" class="mt-5 ws-muted">Cargando plan e importe…</p>
    <p v-if="error" role="alert" class="mt-5 ws-notice ws-danger ws-tint-danger">{{ error }}</p>
    <template v-if="details">
      <dl class="mt-5 space-y-3 rounded-xl ws-inset p-4 text-sm">
        <div class="flex justify-between gap-4"><dt class="ws-muted">Plan</dt><dd class="ws-text font-bold">{{ details.plan }}</dd></div>
        <div class="flex justify-between gap-4"><dt class="ws-muted">Duración</dt><dd class="ws-text">{{ details.duracion }}</dd></div>
        <div class="flex justify-between gap-4"><dt class="ws-muted">Fin del período anterior</dt><dd class="ws-text">{{ details.fecha_fin }}</dd></div>
        <div class="flex justify-between gap-4 border-t ws-border pt-3"><dt class="ws-text font-bold">Total de renovación</dt><dd class="ws-text font-black">{{ money(details.monto_pago) }}</dd></div>
      </dl>
      <p class="mt-4 text-sm leading-6 ws-muted">Solo se renuevan membresías vencidas o en sus últimos 7 días. La renovación se activa al confirmar el pago. Si aún hay días vigentes, el nuevo período empieza al día siguiente de su vencimiento.</p>
      <p v-if="details.renovada" role="status" class="mt-4 rounded-xl ws-tint-success ws-success p-4 text-sm">Ya hay una renovación pagada. Actualiza los detalles antes de realizar otra compra.</p>
      <p v-if="details.renovacion_pendiente" role="status" class="mt-4 rounded-xl ws-tint-warning ws-warning p-4 text-sm">Ya hay una renovación pendiente. Continúa con Stripe para retomar esa compra sin crear otra.</p>
      <fieldset class="mt-5 space-y-3" :disabled="busy || loading">
        <legend class="mb-3 font-bold ws-text">Método de pago</legend>
        <label class="flex items-center gap-3 ws-text"><input type="radio" name="renewal-method" value="efectivo" :checked="method === 'efectivo'" :disabled="details.renovacion_pendiente" @change="$emit('update:method', 'efectivo')"> Efectivo / caja</label>
        <label class="flex items-center gap-3 ws-text"><input type="radio" name="renewal-method" value="stripe" :checked="method === 'stripe'" @change="$emit('update:method', 'stripe')"> Stripe</label>
        <label v-if="method === 'efectivo'" class="mt-4 flex items-start gap-3 rounded-xl ws-tint-warning p-4 text-sm ws-text">
          <input type="checkbox" class="mt-1 h-4 w-4 shrink-0" :checked="cashReceived" @change="$emit('update:cash-received', $event.target.checked)">
          Confirmo que recibí {{ money(details.monto_pago) }} en efectivo para esta renovación.
        </label>
      </fieldset>
    </template>
    <div class="mt-6 flex flex-wrap justify-end gap-3">
      <button type="button" class="ws-btn" :disabled="busy" @click="$emit('close')">Cancelar</button>
      <button v-if="error" type="button" class="ws-btn" :disabled="busy || loading" @click="$emit('reload')">Actualizar detalles</button>
      <button type="button" class="ws-btn ws-primary" :disabled="busy || loading || !details || details.renovada || (method === 'efectivo' && (!cashReceived || details.renovacion_pendiente))" @click="$emit('confirm')">
        {{ busy ? 'Procesando…' : method === 'stripe' ? 'Continuar a Stripe' : 'Confirmar renovación' }}
      </button>
    </div>
  </WorkspaceDialog>
</template>

<script setup>
import WorkspaceDialog from '../WorkspaceDialog.vue';
defineProps({ client: Object, details: Object, loading: Boolean, busy: Boolean, error: String, method: String, cashReceived: Boolean });
defineEmits(['close', 'reload', 'confirm', 'update:method', 'update:cash-received']);
const money = value => new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(value);
</script>
