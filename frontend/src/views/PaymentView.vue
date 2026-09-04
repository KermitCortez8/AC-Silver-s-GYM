<template>
  <div class="min-h-screen bg-[#f5f5f5] text-slate-950">
    <header class="border-b border-orange-200 bg-white/85 backdrop-blur">
      <div class="mx-auto flex max-w-[1100px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-lg font-black italic text-[#dc2626]">Silver Gym Surco</router-link>
        <router-link to="/login" class="rounded-xl border border-[#dc2626]/25 px-4 py-2 text-sm font-bold text-[#dc2626]">Acceso</router-link>
      </div>
    </header>

    <main class="mx-auto flex max-w-[760px] items-center px-4 py-14 sm:px-6">
      <section class="w-full rounded-3xl border bg-white p-7 text-center shadow-[0_20px_60px_rgba(15,23,42,0.08)] sm:p-10" :class="resultStyle.border">
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full text-3xl" :class="resultStyle.iconBackground">
          {{ resultStyle.icon }}
        </div>
        <p class="mt-6 text-xs font-bold uppercase tracking-[0.32em]" :class="resultStyle.labelColor">Stripe</p>
        <h1 class="mt-3 text-3xl font-black">{{ resultStyle.title }}</h1>
        <p class="mx-auto mt-4 max-w-xl leading-7 text-slate-600">{{ resultStyle.description }}</p>

        <p v-if="confirmationError" class="mx-auto mt-4 max-w-xl rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
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
          <router-link to="/login" class="rounded-xl bg-[#dc2626] px-6 py-3 font-black text-white transition hover:bg-[#b91c1c]">Ir al acceso</router-link>
          <router-link :to="result === 'failure' ? '/registro' : '/'" class="rounded-xl border border-slate-200 px-6 py-3 font-bold text-slate-700">
            {{ result === 'failure' ? 'Intentar nuevamente' : 'Volver al inicio' }}
          </router-link>
        </div>

        <p class="mt-6 text-xs leading-5 text-slate-500">
          La confirmación definitiva llega directamente desde Stripe; nunca validamos un pago solo por la URL de retorno.
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiPost } from '../services/apiClient';

const route = useRoute();
const router = useRouter();
const idCliente = computed(() => Number(route.params.idCliente || 0));
const result = computed(() => String(route.query.result || 'pending').toLowerCase());
const confirmationState = ref('idle');
const confirmationError = ref('');

const resultStyle = computed(() => {
  if (result.value === 'success') {
    if (confirmationState.value === 'confirmed') {
      return {
        icon: '✓', title: 'Pago confirmado',
        description: 'Su cuenta ha sido inicializada. A la espera de activación de membresía.',
        status: 'Pago confirmado; activación pendiente', border: 'border-emerald-200',
        iconBackground: 'bg-emerald-100 text-emerald-700', labelColor: 'text-emerald-700',
      };
    }
    return {
      icon: '…', title: 'Confirmando el pago',
      description: 'Estamos verificando la operación directamente con Stripe.',
      status: confirmationState.value === 'error' ? 'Confirmación pendiente' : 'Verificando', border: 'border-amber-200',
      iconBackground: 'bg-amber-100 text-amber-700', labelColor: 'text-amber-700',
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
    status: 'Pendiente', border: 'border-amber-200',
    iconBackground: 'bg-amber-100 text-amber-700', labelColor: 'text-amber-700',
  };
});

const confirmPaidCheckout = async () => {
  if (result.value !== 'success') return;

  const sessionId = String(route.query.session_id || '').trim();
  if (!sessionId) {
    confirmationState.value = 'error';
    confirmationError.value = 'Stripe no devolvió el identificador de la sesión. La confirmación continuará mediante el webhook.';
    return;
  }

  confirmationState.value = 'verifying';
  try {
    const response = await apiPost(`/pagos/stripe/confirmar-retorno?session_id=${encodeURIComponent(sessionId)}`);
    if (response?.confirmed) {
      confirmationState.value = 'confirmed';
      await router.replace({
        path: '/',
        query: {
          registro: 'inicializado',
          solicitud: String(response.id_cliente || idCliente.value),
        },
      });
      return;
    }
    confirmationState.value = 'error';
    confirmationError.value = 'El pago todavía no aparece aprobado. La cuenta permanecerá pendiente hasta recibir la confirmación.';
  } catch (error) {
    confirmationState.value = 'error';
    confirmationError.value = error instanceof Error ? error.message : 'No se pudo confirmar el pago en este momento.';
  }
};

onMounted(confirmPaidCheckout);
</script>
