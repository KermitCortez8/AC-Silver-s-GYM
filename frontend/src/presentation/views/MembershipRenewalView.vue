<template>
  <div class="public-page min-h-screen bg-slate-50 text-slate-950">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
        <router-link to="/" class="text-lg font-black italic text-orange-600">Silver Gym Surco</router-link>
        <router-link to="/login" class="text-sm font-bold text-slate-600">Acceso</router-link>
      </div>
    </header>
    <main class="mx-auto max-w-2xl px-5 py-12 sm:py-20">
      <p class="text-xs font-black uppercase tracking-widest text-orange-600">Sigue entrenando con nosotros</p>
      <h1 class="mt-3 text-3xl font-black sm:text-4xl">Renueva tu membresía</h1>
      <p class="mt-4 leading-7 text-slate-600">Revisa los detalles de tu nueva compra. Cuando estés listo, continúa al pago con Stripe.</p>
      <section class="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 sm:p-8" :aria-busy="loading">
        <p v-if="loading" role="status" class="text-slate-600">Cargando los detalles de tu membresía…</p>
        <p v-if="error" role="alert" class="mb-5 rounded-xl bg-rose-50 p-4 text-rose-800">{{ error }}</p>
        <template v-if="details">
          <div class="flex items-start justify-between gap-4">
            <div><p class="text-sm text-slate-500">Plan de renovación</p><h2 class="mt-1 text-2xl font-bold">{{ details.plan }}</h2></div>
            <span class="rounded-full bg-orange-50 px-3 py-1 text-xs font-bold text-orange-700">Membresía</span>
          </div>
          <p v-if="details.descripcion" class="mt-4 leading-6 text-slate-600">{{ details.descripcion }}</p>
          <dl class="mt-6 space-y-4 text-sm">
            <div class="flex justify-between gap-4"><dt class="text-slate-500">Duración del nuevo plan</dt><dd class="font-semibold">{{ details.duracion }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-slate-500">Fin de tu membresía anterior</dt><dd class="font-semibold">{{ formatDate(details.fecha_fin) }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-slate-500">Promoción</dt><dd>{{ details.promocion }}</dd></div>
            <div class="flex justify-between gap-4 border-t border-slate-200 pt-5 text-lg"><dt class="font-bold">{{ details.renovada ? 'Importe de renovación' : 'Total a pagar' }}</dt><dd class="font-black">{{ money(details.monto_pago) }}</dd></div>
          </dl>
          <p class="mt-6 rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">{{ details.activacion }} La compra conserva tu historial y no cambia las fechas de tu membresía anterior.</p>
          <p v-if="details.renovada" role="status" class="mt-6 rounded-xl bg-emerald-50 p-4 text-emerald-800">Ya tienes una renovación pagada. No necesitas pagar nuevamente. Puedes ingresar a tu cuenta para revisar su vigencia.</p>
          <button v-else type="button" class="mt-6 w-full rounded-full bg-orange-600 px-6 py-4 font-bold text-white hover:bg-orange-700 disabled:opacity-50" :disabled="paying || loading || Number(details.monto_pago) <= 0" @click="pay">
            {{ paying ? 'Preparando el pago…' : 'Continuar a Stripe' }}
          </button>
          <p class="mt-4 text-center text-xs leading-5 text-slate-500">Revisa y confirma el pago en Stripe. La membresía se registra como pagada cuando Stripe confirma la operación.</p>
        </template>
        <button v-if="error" type="button" class="mt-4 font-bold text-orange-700 underline" :disabled="loading || paying" @click="load">Volver a cargar los detalles</button>
      </section>
      <p class="mt-6 text-center text-sm text-slate-500">¿Necesitas otro plan? Comunícate con administración.</p>
    </main>
  </div>
</template>

<script setup>
import { onScopeDispose, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useClientPayments } from '../../application/services/clientPayments.js';

const route = useRoute();
const payments = useClientPayments();
const details = ref(null);
const loading = ref(false);
const paying = ref(false);
const error = ref('');
let version = 0;
const token = () => new URLSearchParams(route.hash.slice(1)).get('token') || '';
const money = (value) => new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(value);
const formatDate = (value) => String(value || '').slice(0, 10).split('-').reverse().join('/');
const load = async () => {
  const current = ++version;
  const requestedToken = token();
  details.value = null;
  error.value = '';
  paying.value = false;
  loading.value = true;
  try {
    if (!token()) throw new Error('El enlace está incompleto. Abre el enlace personal del correo o contacta con administración.');
    const response = await payments.getRenewalDetails(token());
    if (current === version && requestedToken === token()) details.value = response;
  } catch (cause) {
    if (current === version) error.value = cause.message || 'No se pudieron cargar los detalles.';
  } finally {
    if (current === version) loading.value = false;
  }
};
const pay = async () => {
  if (paying.value || loading.value || !details.value || details.value.renovada) return;
  const current = version;
  paying.value = true;
  error.value = '';
  try {
    const payment = await payments.startRenewalPayment(token(), Number(details.value.monto_pago));
    if (current !== version) return;
    if (!payment?.checkout_url) throw new Error('No se pudo preparar el pago. Intenta nuevamente.');
    window.location.assign(payment.checkout_url);
  } catch (cause) {
    if (current === version) error.value = cause.message || 'No se pudo iniciar el pago.';
  } finally {
    if (current === version) paying.value = false;
  }
};
watch(() => route.hash, load, { immediate: true });
onScopeDispose(() => { version++; });
</script>
