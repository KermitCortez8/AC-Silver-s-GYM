<template>
  <div class="public-page payment-page min-h-screen bg-[radial-gradient(circle_at_12%_8%,rgba(220,38,38,0.06),transparent_45%),radial-gradient(circle_at_88%_92%,rgba(15,23,42,0.04),transparent_45%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] text-slate-950">
    <header class="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1100px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-lg font-black italic text-orange-600">Silver Gym Surco</router-link>
        <router-link to="/login" class="btn-cta rounded-full border border-slate-300 bg-transparent px-4 py-2 text-sm text-slate-700 transition hover:border-orange-300 hover:text-orange-600">Acceso</router-link>
      </div>
    </header>

    <main class="mx-auto flex max-w-[760px] items-center px-4 py-14 sm:px-6">
      <section class="w-full rounded-[1.75rem] border bg-white p-7 text-center shadow-2xl shadow-slate-900/10 sm:p-10" :class="resultStyle.border">
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full text-3xl" :class="resultStyle.iconBackground">
          {{ resultStyle.icon }}
        </div>
        <p class="mt-6 text-xs font-black uppercase tracking-[0.2em]" :class="resultStyle.labelColor">Stripe</p>
        <h1 class="mt-3 text-2xl font-black leading-tight text-slate-950 sm:text-3xl">{{ resultStyle.title }}</h1>
        <p class="mx-auto mt-4 max-w-xl leading-7 text-slate-600">{{ resultStyle.description }}</p>

        <p v-if="confirmationError" role="alert" class="mx-auto mt-4 max-w-xl rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {{ confirmationError }}
        </p>

        <div class="mt-7 rounded-2xl bg-slate-50 p-5 text-left text-sm">
          <div class="flex justify-between gap-4">
            <span class="text-slate-500">Solicitud</span>
            <span class="font-bold">SGCLI{{ String(idCliente).padStart(3, '0') }}</span>
          </div>
          <div class="mt-3 flex justify-between gap-4">
            <span class="text-slate-500">Estado</span>
            <span class="font-bold">{{ resultStyle.status }}</span>
          </div>
        </div>

        <div class="mt-7 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button
            v-if="canRetryConfirmation"
            type="button"
            class="btn-cta rounded-full bg-orange-500 px-6 py-3 text-sm text-white disabled:opacity-50"
            :disabled="confirmationState === 'verifying'"
            @click="confirmPaidCheckout"
          >{{ confirmationState === 'verifying' ? 'Verificando…' : 'Volver a verificar el pago' }}</button>
          <router-link to="/login" class="btn-cta rounded-full bg-orange-500 px-6 py-3 text-sm text-white shadow-lg shadow-orange-500/25 transition hover:bg-orange-600">Ir al acceso</router-link>
          <router-link :to="result === 'failure' ? '/registro' : '/'" class="btn-cta rounded-full border border-slate-300 px-6 py-3 text-sm text-slate-700 transition hover:border-orange-300 hover:text-orange-600">
            {{ result === 'failure' ? 'Intentar nuevamente' : 'Volver al inicio' }}
          </router-link>
        </div>

        <p class="mt-6 text-xs leading-5 text-slate-500">
          Para usar tu cuenta, el administrador debe activarla después de confirmar el pago.
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onScopeDispose, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useClientPayments } from '../../application/services/clientPayments.js';

const { confirmMembershipPayment } = useClientPayments();

const route = useRoute();
const idCliente = computed(() => Number(route.params.idCliente || 0));
const result = computed(() => String(route.query.result || 'pending').toLowerCase());
const confirmationState = ref('idle');
const confirmationError = ref('');
let confirmationNumber = 0;
const checkoutKey = () => `${route.params.idCliente}|${route.query.result}|${route.query.session_id}`;
const canRetryConfirmation = computed(() =>
  ['success', 'pending'].includes(result.value) &&
  Boolean(String(route.query.session_id || '').trim()) &&
  confirmationState.value !== 'confirmed',
);

const resultStyle = computed(() => {
  if (['success', 'pending'].includes(result.value)) {
    if (confirmationState.value === 'confirmed') {
      return {
        icon: '✓', title: 'Pago confirmado',
        description: 'Tu pago fue confirmado. Tu cuenta está pendiente de activación por el administrador. Podrás ingresar cuando sea activada.',
        status: 'Pago confirmado; activación pendiente', border: 'border-emerald-200',
        iconBackground: 'bg-emerald-100 text-emerald-700', labelColor: 'text-emerald-700',
      };
    }
    if (confirmationState.value === 'error') return {
      icon: '!', title: 'No se pudo verificar el pago',
      description: 'Puedes volver a consultar el estado de la misma operación. No necesitas realizar otro pago.',
      status: 'Confirmación sin verificar', border: 'border-rose-200',
      iconBackground: 'bg-rose-100 text-rose-700', labelColor: 'text-rose-700',
    };
    if (confirmationState.value === 'pending') return {
      icon: '…', title: 'Pago pendiente de confirmación',
      description: 'La operación todavía no está confirmada. Vuelve a verificar antes de intentar pagar otra vez.',
      status: 'Pendiente de confirmación', border: 'border-orange-200',
      iconBackground: 'bg-orange-100 text-orange-700', labelColor: 'text-orange-700',
    };
    return {
      icon: '…', title: 'Confirmando el pago',
      description: 'Estamos verificando la operación directamente con Stripe.',
      status: 'Verificando', border: 'border-orange-200',
      iconBackground: 'bg-orange-100 text-orange-700', labelColor: 'text-orange-700',
    };
  }
  if (result.value === 'failure') {
    return {
      icon: '!', title: 'El pago no se completó',
      description: 'No se realizó ningún cobro confirmado. Puedes volver al registro e intentarlo nuevamente.',
      status: 'Rechazado o cancelado', border: 'border-rose-200',
      iconBackground: 'bg-rose-100 text-rose-700', labelColor: 'text-rose-700',
    };
  }
  return {
    icon: '…', title: 'Pago pendiente',
    description: 'Stripe está procesando la operación. La membresía se actualizará automáticamente cuando exista una respuesta definitiva.',
    status: 'Pendiente', border: 'border-orange-200',
    iconBackground: 'bg-orange-100 text-orange-700', labelColor: 'text-orange-700',
  };
});

const confirmPaidCheckout = async () => {
  if (!['success', 'pending'].includes(result.value) || confirmationState.value === 'verifying') return;
  const request = ++confirmationNumber;
  const key = checkoutKey();
  const expectedClient = idCliente.value;
  const isCurrent = () => request === confirmationNumber && key === checkoutKey();
  confirmationError.value = '';

  const sessionId = String(route.query.session_id || '').trim();
  if (!sessionId || !Number.isInteger(expectedClient) || expectedClient <= 0) {
    confirmationState.value = 'error';
    confirmationError.value = 'El enlace de pago está incompleto. Revisa el enlace de retorno o consulta con administración.';
    return;
  }

  confirmationState.value = 'verifying';
  try {
    const response = await confirmMembershipPayment(sessionId);
    if (!isCurrent()) return;
    if (response?.confirmed === true) {
      if (Number(response.id_cliente) !== expectedClient)
        throw new Error('La confirmación no corresponde a esta solicitud. Revisa el enlace de pago.');
      confirmationState.value = 'confirmed';
      return;
    }
    confirmationState.value = 'pending';
  } catch (error) {
    if (!isCurrent()) return;
    confirmationState.value = 'error';
    confirmationError.value = error instanceof Error ? error.message : 'No se pudo confirmar el pago en este momento.';
  }
};

onMounted(confirmPaidCheckout);
watch(checkoutKey, () => {
  confirmationNumber++;
  confirmationState.value = 'idle';
  confirmationError.value = '';
  confirmPaidCheckout();
});
onScopeDispose(() => { confirmationNumber++; });
</script>

<style scoped>
.payment-page {
  font-family: 'Manrope', 'Segoe UI', 'Trebuchet MS', sans-serif;
}
.payment-page h1,
.payment-page h2,
.payment-page h3 {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.01em;
}
.payment-page .btn-cta {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
</style>
