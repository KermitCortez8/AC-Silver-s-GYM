<template>
  <div class="min-h-screen bg-[#f5f5f5] text-slate-950">
    <header class="border-b border-orange-200 bg-white/85 backdrop-blur">
      <div class="mx-auto flex max-w-[1400px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-lg font-black italic text-[#dc2626]">Silver Gym Surco</router-link>
        <router-link to="/login" class="rounded-sm border border-[#dc2626]/25 px-4 py-2 text-sm font-bold text-[#dc2626]">Acceso</router-link>
      </div>
    </header>

    <main class="mx-auto grid max-w-[1400px] gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
      <section class="rounded-2xl border border-orange-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <p class="text-xs font-bold uppercase tracking-[0.35em] text-[#dc2626]">Pasarela</p>
        <h1 class="mt-3 text-3xl font-black">Confirma tu pago</h1>

        <div class="mt-6 space-y-3 rounded-2xl bg-[#fee2e2] p-5 text-sm text-slate-700">
          <p><span class="font-bold">Cliente:</span> {{ client?.name || 'Cliente nuevo' }}</p>
          <p><span class="font-bold">Plan:</span> {{ client?.plan || 'MENSUAL' }}</p>
          <p><span class="font-bold">Estado actual:</span> {{ client?.membershipStatus || 'PENDIENTE_PAGO' }}</p>
        </div>

        <form class="mt-6 space-y-4" @submit.prevent="confirmPayment">
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Metodo de pago</span>
            <select v-model="form.metodo_pago" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]">
              <option value="tarjeta">Tarjeta</option>
              <option value="yape">Yape</option>
              <option value="plin">Plin</option>
              <option value="transferencia">Transferencia</option>
            </select>
          </label>

          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Referencia</span>
            <input v-model="form.referencia_pago" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="Operacion o voucher" />
          </label>

          <button
            type="submit"
            class="w-full rounded-xl bg-[#dc2626] px-5 py-4 text-sm font-black uppercase tracking-[0.14em] text-white transition hover:bg-[#b91c1c] disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Confirmando...' : 'Confirmar pago' }}
          </button>
        </form>

        <p v-if="feedback" class="mt-5 rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-300 bg-rose-50 text-rose-900' : 'border-emerald-300 bg-emerald-50 text-emerald-900'">
          {{ feedback }}
        </p>
      </section>

      <section class="rounded-2xl bg-[#dc2626] p-6 text-white">
        <p class="text-xs font-bold uppercase tracking-[0.35em] text-white/70">Resumen</p>
        <h2 class="mt-3 text-3xl font-black">Solicitud pendiente de pago</h2>
        <p class="mt-3 leading-7 text-white/85">
          Al confirmar el pago, tu cuenta quedara registrada en el sistema con membresia en tramite. Luego el administrador la activara desde Clientes.
        </p>
        <div class="mt-6 rounded-2xl bg-white/10 p-5">
          <p class="text-sm text-white/70">Codigo de cliente</p>
          <p class="mt-1 text-2xl font-black">{{ client?.id || `SGCLI${String(idCliente).padStart(3, '0')}` }}</p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGymStore } from '../stores/gymStore';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();

const idCliente = computed(() => Number(route.params.idCliente || 0));
const storedClient = (() => {
  try {
    return JSON.parse(window.sessionStorage.getItem('pending_public_registration') || 'null');
  } catch (error) {
    return null;
  }
})();
const client = ref(storedClient);
const isSubmitting = ref(false);
const feedback = ref('');
const feedbackTone = ref('success');

const form = reactive({
  metodo_pago: 'tarjeta',
  referencia_pago: String(route.query.ref || `WEB-${Date.now()}`),
});

const confirmPayment = async () => {
  if (!idCliente.value) {
    feedbackTone.value = 'error';
    feedback.value = 'No se encontro la solicitud de registro.';
    return;
  }

  isSubmitting.value = true;
  feedback.value = '';
  try {
    const saved = await gymStore.confirmPublicPayment(idCliente.value, form);
    client.value = saved;
    window.sessionStorage.removeItem('pending_public_registration');
    feedbackTone.value = 'success';
    feedback.value = 'Pago confirmado. Tu membresia quedo en tramite para activacion administrativa.';
    window.setTimeout(() => router.push('/login'), 1400);
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo confirmar el pago.';
  } finally {
    isSubmitting.value = false;
  }
};
</script>
