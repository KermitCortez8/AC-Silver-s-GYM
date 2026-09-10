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
        <GoogleSignInButton class="mt-5" text="signup_with" :disabled="isSubmitting || googleProcessing" @credential="selectGoogleAccount" />
        <p v-if="googleProcessing" role="status" class="mt-3 text-sm text-slate-600">Verificando tu cuenta de Google...</p>
        <div v-if="googleCredential" class="mt-4 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900">
          <p>Cuenta de Google verificada: {{ form.correo }}. Completa tus datos y elige un plan. Podrás ingresar con Google cuando el administrador active tu cuenta.</p>
          <button type="button" class="mt-2 font-bold underline" :disabled="isSubmitting" @click="clearGoogleAccount">Usar correo y contraseña</button>
        </div>

        <form class="mt-6 space-y-4" @submit.prevent="submitRegistration">
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Nombre completo</span>
            <input v-model.trim="form.nombre" required autocomplete="name" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="Jose Perez" />
          </label>

          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Correo</span>
            <input v-model.trim="form.correo" :readonly="Boolean(googleCredential)" required type="email" autocomplete="email" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626] read-only:bg-slate-100" placeholder="cliente@correo.com" />
          </label>

          <label v-if="!googleCredential" class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Contrasena</span>
            <input v-model="form.password" required minlength="6" type="password" autocomplete="new-password" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="Minimo 6 caracteres" />
          </label>

          <div class="grid gap-4 sm:grid-cols-2">
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700">DNI</span>
              <input v-model.trim="form.dni" required inputmode="numeric" pattern="[0-9]{8}" maxlength="8" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="12345678" />
            </label>
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700">Telefono</span>
              <input v-model.trim="form.telefono" required type="tel" inputmode="tel" pattern="[0-9+ ]{7,15}" maxlength="15" autocomplete="tel" class="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-[#dc2626]" placeholder="999111222" />
            </label>
          </div>

          <button
            type="submit"
            class="w-full rounded-xl bg-[#dc2626] px-5 py-4 text-sm font-black uppercase tracking-[0.14em] text-white transition hover:bg-[#b91c1c] disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isSubmitting || googleProcessing || !planOptions.length"
          >
            {{ isSubmitting ? 'Preparando pago seguro...' : 'Pagar con Stripe' }}
          </button>
          <p class="text-center text-xs leading-5 text-slate-500">
            Serás redirigido a Stripe Checkout. Silver Gym no recibe ni almacena los datos de tu tarjeta.
          </p>
          <p class="text-center text-sm leading-5 text-slate-600">
            Después del pago, tu cuenta quedará pendiente de activación por el administrador.
          </p>
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
import { useRoute } from 'vue-router';
import GoogleSignInButton from '../components/GoogleSignInButton.vue';
import { getVerifiedGoogleProfile } from '../services/authService';
import { apiGet } from '../services/apiClient';
import { useGymStore } from '../stores/gymStore';

const route = useRoute();
const gymStore = useGymStore();
const googleCredential = ref('');
const googleProcessing = ref(false);
const googleError = ref('');
const feedback = ref('');
const feedbackTone = ref('success');
const isSubmitting = ref(false);
const registeredClient = ref(null);
const backendPlans = ref([]);
const defaultPlans = [
  { id_pm: 1, nombre_plan: 'MENSUAL', duracion: '30 dias', precio: 79, descripcion: 'Acceso completo por 30 dias.', activo: true },
  { id_pm: 2, nombre_plan: '3 MESES', duracion: '90 dias', precio: 199, descripcion: 'Plan trimestral para progreso sostenido.', activo: true },
  { id_pm: 3, nombre_plan: 'ANUAL', duracion: '365 dias', precio: 699, descripcion: 'Membresia anual con mejor precio acumulado.', activo: true },
];

/**
 * Normaliza el valor recibido.
 */
const normalizePlanName = (value) => String(value || '').trim().toUpperCase();
/**
 * Formatea el valor para mostrarlo.
 */
const formatPlanLabel = (value) =>
  normalizePlanName(value)
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const planOptions = computed(() =>
  (backendPlans.value.length ? backendPlans.value : defaultPlans)
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

/**
 * Sincroniza los datos disponibles.
 */
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
});

/**
 * Consulta los datos del servidor.
 */
const loadPlans = async () => {
  try {
    const list = await apiGet('/planes-membresia');
    backendPlans.value = Array.isArray(list) ? list : [];
  } catch {
    backendPlans.value = defaultPlans;
  } finally {
    syncSelectedPlan();
  }
};

const clearGoogleAccount = () => {
  googleCredential.value = '';
  googleError.value = '';
  form.correo = '';
  form.password = '';
};

const selectGoogleAccount = async (credential) => {
  if (isSubmitting.value || googleProcessing.value) return;
  googleProcessing.value = true;
  clearGoogleAccount();
  try {
    const profile = await getVerifiedGoogleProfile(credential);
    form.nombre = profile.name || form.nombre;
    form.correo = profile.email;
    googleCredential.value = credential;
  } catch (error) {
    googleError.value = error.message || 'No se pudo verificar tu cuenta de Google';
  } finally {
    googleProcessing.value = false;
  }
};

/**
 * Envía los datos del formulario.
 */
const submitRegistration = async () => {
  if (isSubmitting.value || googleProcessing.value) return;
  isSubmitting.value = true;
  feedback.value = '';
  registeredClient.value = null;

  try {
    if (!form.plan) {
      throw new Error('No hay planes configurados para registrar clientes.');
    }

    const result = await gymStore.registerPublicClient({ ...form, google_credential: googleCredential.value });
    const { client, payment } = result;
    registeredClient.value = client;
    if (!payment?.checkout_url) {
      throw new Error(payment?.message || 'Stripe no está configurado. Contacta al administrador.');
    }
    feedbackTone.value = 'success';
    feedback.value = 'Preregistro creado. Abriendo el checkout seguro de Stripe. Tu cuenta requerirá activación por el administrador.';
    window.location.assign(payment.checkout_url);
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo completar el registro.';
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  loadPlans();
});
</script>
