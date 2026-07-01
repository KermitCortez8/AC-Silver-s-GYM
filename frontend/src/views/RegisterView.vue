<template>
  <div class="min-h-screen bg-[#f5f5f5] text-slate-950">
    <header class="border-b border-orange-200 bg-white/85 backdrop-blur">
      <div class="mx-auto flex max-w-[1560px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-lg font-black italic text-[#dc2626]">Silver Gym Surco</router-link>
        <router-link to="/login" class="rounded-sm border border-[#dc2626]/25 px-4 py-2 text-sm font-bold text-[#dc2626]">Acceso</router-link>
      </div>
    </header>

    <main class="mx-auto grid max-w-[1560px] gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
      <section class="rounded-2xl border border-orange-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <p class="text-xs font-bold uppercase tracking-[0.35em] text-[#dc2626]">Registro</p>
        <h1 class="mt-3 text-3xl font-black">Crea tu preinscripcion</h1>

        <div v-if="googleError" class="mt-5 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          {{ googleError }}
        </div>
        <div ref="googleButtonRef" class="mt-5 flex min-h-[48px] items-center"></div>

        <form class="mt-6 space-y-4" @submit.prevent="submitRegistration">
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Nombre completo</span>
            <input v-model="form.nombre" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="Jose Perez" />
          </label>

          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Correo</span>
            <input v-model="form.correo" type="email" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="cliente@correo.com" />
          </label>

          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Contrasena</span>
            <input v-model="form.password" type="password" autocomplete="new-password" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="Minimo 6 caracteres" />
          </label>

          <div class="grid gap-4 sm:grid-cols-2">
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700">DNI</span>
              <input v-model="form.dni" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="12345678" />
            </label>
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700">Telefono</span>
              <input v-model="form.telefono" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="999111222" />
            </label>
          </div>

          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Referencia de pago</span>
            <input v-model="form.referencia_pago" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="Operacion, voucher o codigo" />
          </label>

          <button
            type="submit"
            class="w-full rounded-xl bg-[#dc2626] px-5 py-4 text-sm font-black uppercase tracking-[0.14em] text-white transition hover:bg-[#b91c1c] disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isSubmitting || !planOptions.length"
          >
            {{ isSubmitting ? 'Procesando...' : 'Continuar a pago' }}
          </button>
        </form>

        <p v-if="feedback" class="mt-5 rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-300 bg-rose-50 text-rose-900' : 'border-emerald-300 bg-emerald-50 text-emerald-900'">
          {{ feedback }}
        </p>
      </section>

      <section class="space-y-4">
        <div class="rounded-2xl bg-[#dc2626] p-6 text-white">
          <p class="text-xs font-bold uppercase tracking-[0.35em] text-white/70">Membresia</p>
          <h2 class="mt-2 text-3xl font-black">Elige tu plan</h2>
        </div>

        <p v-if="!planOptions.length" class="rounded-2xl border border-orange-100 bg-white p-5 text-sm font-bold text-slate-600">
          Planes pendientes de configuracion.
        </p>

        <article
          v-for="plan in planOptions"
          :key="plan.id"
          class="cursor-pointer rounded-2xl border bg-white p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)] transition"
          :class="form.plan === plan.id ? 'border-[#dc2626] ring-2 ring-[#dc2626]/20' : 'border-orange-100 hover:border-[#dc2626]/40'"
          @click="form.plan = plan.id"
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xl font-black">{{ plan.label }}</p>
              <p class="mt-1 text-sm leading-6 text-slate-600">{{ plan.detail }}</p>
            </div>
            <p class="text-3xl font-black text-[#dc2626]">S/ {{ plan.price }}</p>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <span v-for="tag in plan.tags" :key="tag" class="rounded-full bg-[#fee2e2] px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] text-slate-600">{{ tag }}</span>
          </div>
        </article>

        <div v-if="registeredClient" class="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-950">
          <p class="text-xs font-bold uppercase tracking-[0.25em] text-emerald-700">Solicitud enviada</p>
          <p class="mt-2 text-xl font-black">{{ registeredClient.name }}</p>
          <p class="mt-1 text-sm">Codigo: {{ registeredClient.id }}</p>
          <p class="text-sm">Estado de membresia: {{ registeredClient.membershipStatus }}</p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { GOOGLE_CONFIG } from '../config/googleConfig';
import { loadGoogleIdentityScript } from '../services/authService';
import { apiGet } from '../services/apiClient';
import { decodeJWT } from '../utils/authUtils';
import { useGymStore } from '../stores/gymStore';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();
const googleButtonRef = ref(null);
const googleError = ref('');
const feedback = ref('');
const feedbackTone = ref('success');
const isSubmitting = ref(false);
const registeredClient = ref(null);
const backendPlans = ref([]);

const normalizePlanName = (value) => String(value || '').trim().toUpperCase();
const formatPlanLabel = (value) =>
  normalizePlanName(value)
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const planOptions = computed(() =>
  backendPlans.value
    .filter((plan) => plan.activo ?? plan.active ?? true)
    .map((plan) => {
      const name = normalizePlanName(plan.nombre_plan || plan.name);
      const duration = String(plan.duracion || plan.description || '').trim();
      return {
        id: name,
        label: formatPlanLabel(name),
        price: Number(plan.precio ?? plan.price ?? 0),
        detail: duration ? `Acceso por ${duration}.` : 'Plan disponible para registro.',
        tags: duration ? [duration] : [],
      };
    })
    .filter((plan) => plan.id),
);

const syncSelectedPlan = () => {
  if (!planOptions.value.length) {
    form.plan = '';
    return;
  }

  if (!planOptions.value.some((plan) => plan.id === form.plan)) {
    form.plan = planOptions.value[0].id;
  }
};

const form = reactive({
  nombre: '',
  correo: '',
  telefono: '',
  dni: '',
  password: '',
  plan: normalizePlanName(route.query.plan),
  referencia_pago: '',
  google_email: '',
  google_name: '',
});

const loadPlans = async () => {
  try {
    const list = await apiGet('/planes-membresia');
    backendPlans.value = Array.isArray(list) ? list : [];
  } catch {
    backendPlans.value = [];
  } finally {
    syncSelectedPlan();
  }
};

const renderGoogleButton = async () => {
  if (!GOOGLE_CONFIG.webClientId || !googleButtonRef.value) return;

  try {
    await loadGoogleIdentityScript();
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CONFIG.webClientId,
      callback: (response) => {
        const profile = decodeJWT(response.credential);
        if (!profile) return;
        form.nombre = profile.name || form.nombre;
        form.correo = profile.email || form.correo;
        form.google_email = profile.email || '';
        form.google_name = profile.name || '';
      },
      auto_select: false,
      cancel_on_tap_outside: true,
    });
    googleButtonRef.value.innerHTML = '';
    window.google.accounts.id.renderButton(googleButtonRef.value, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      shape: 'pill',
      text: 'signup_with',
      width: 320,
    });
  } catch (error) {
    googleError.value = error?.message || 'No se pudo cargar Google';
  }
};

const submitRegistration = async () => {
  isSubmitting.value = true;
  feedback.value = '';
  registeredClient.value = null;

  try {
    if (!form.plan) {
      throw new Error('No hay planes configurados para registrar clientes.');
    }

    const client = await gymStore.registerPublicClient({
      ...form,
      metodo_pago: 'pasarela',
      referencia_pago: form.referencia_pago || `WEB-${Date.now()}`,
    });
    registeredClient.value = client;
    feedbackTone.value = 'success';
    feedback.value = 'Cuenta creada. Te llevamos a la pasarela de pago.';
    router.push({ name: 'Payment', params: { idCliente: client.id_cliente }, query: { ref: client.paymentReference || `WEB-${Date.now()}` } });
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo completar el registro.';
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  loadPlans();
  renderGoogleButton();
});
</script>
