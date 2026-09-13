<template>
  <div
    class="register-page min-h-screen bg-[radial-gradient(circle_at_12%_8%,rgba(220,38,38,0.08),transparent_45%),radial-gradient(circle_at_88%_92%,rgba(15,23,42,0.05),transparent_45%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] text-slate-950"
  >
    <!-- HEADER -->
    <header class="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div
        class="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8"
      >
        <router-link
          to="/"
          class="text-xl font-black italic text-orange-600"
        >
          Silver Gym Surco
        </router-link>

        <router-link
          to="/login"
          class="btn-cta rounded-full border border-slate-300 bg-transparent px-4 py-2 text-sm text-slate-700 transition hover:border-orange-300 hover:text-orange-600"
        >
          Acceso a plataforma digital
        </router-link>
      </div>
    </header>

    <!-- CONTENIDO -->
    <main
      class="mx-auto grid max-w-[1400px] gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_0.85fr] lg:items-start lg:gap-10 lg:py-16"
    >
      <!-- FORMULARIO -->
      <section
        class="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-slate-900/10 sm:p-8 lg:p-10"
      >
        <p
          class="text-xs font-black uppercase tracking-[0.08em] text-orange-500"
        >
          Registro
        </p>

        <h1
          class="mt-3 text-2xl font-black leading-tight text-slate-950 sm:text-3xl"
        >
          Crea tu preinscripción.
        </h1>

        <!-- ERROR GOOGLE -->
        <div
          v-if="googleError"
          class="mt-5 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"
        >
          {{ googleError }}
        </div>

        <!-- REGISTRO CON GOOGLE -->
        <GoogleSignInButton
          class="mt-5"
          text="signup_with"
          :disabled="isSubmitting || googleProcessing"
          @credential="selectGoogleAccount"
        />

        <p
          v-if="googleProcessing"
          role="status"
          class="mt-3 text-sm text-slate-600"
        >
          Verificando tu cuenta de Google...
        </p>

        <!-- GOOGLE VERIFICADO -->
        <div
          v-if="googleCredential"
          class="mt-4 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900"
        >
          <p>
            Cuenta de Google verificada:
            <strong>{{ form.correo }}</strong>.
            Completa tus datos y elige un plan.
            Podrás ingresar con Google cuando el administrador active tu cuenta.
          </p>

          <button
            type="button"
            class="mt-2 font-bold underline"
            :disabled="isSubmitting || googleProcessing"
            @click="clearGoogleAccount"
          >
            Usar correo y contraseña
          </button>
        </div>

        <!-- FORMULARIO -->
        <form
          class="mt-6 space-y-4"
          @submit.prevent="submitRegistration"
        >
          <!-- NOMBRE -->
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">
              Nombre completo
            </span>

            <input
              v-model.trim="form.nombre"
              required
              autocomplete="name"
              class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
              placeholder="Jose Perez"
            />
          </label>

          <!-- CORREO -->
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">
              Correo
            </span>

            <!--
              MERGE DE RESEND + DEVELOP

              RESEND:
              - readonly cuando viene de Google.
              - read-only:bg-slate-100.

              DEVELOP:
              - rounded-2xl.
              - colores naranja.
              - estilos nuevos.
            -->
            <input
              v-model.trim="form.correo"
              :readonly="Boolean(googleCredential)"
              required
              type="email"
              autocomplete="email"
              class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 transition focus:border-orange-400 read-only:cursor-not-allowed read-only:bg-slate-100 read-only:text-slate-600"
              placeholder="cliente@correo.com"
            />
          </label>

          <!-- CONTRASEÑA -->
          <label
            v-if="!googleCredential"
            class="block space-y-2"
          >
            <span class="text-sm font-semibold text-slate-700">
              Contraseña
            </span>

            <input
              v-model="form.password"
              required
              minlength="6"
              type="password"
              autocomplete="new-password"
              class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
              placeholder="Mínimo 6 caracteres"
            />
          </label>

          <!-- DNI + TELEFONO -->
          <div class="grid gap-4 sm:grid-cols-2">
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700">
                DNI
              </span>

              <input
                v-model.trim="form.dni"
                required
                inputmode="numeric"
                pattern="[0-9]{8}"
                maxlength="8"
                class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
                placeholder="12345678"
              />
            </label>

            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-700">
                Teléfono
              </span>

              <input
                v-model.trim="form.telefono"
                required
                type="tel"
                inputmode="tel"
                pattern="[0-9+ ]{7,15}"
                maxlength="15"
                autocomplete="tel"
                class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
                placeholder="999111222"
              />
            </label>
          </div>

          <!-- BOTON STRIPE -->
          <button
            type="submit"
            class="btn-cta w-full rounded-full bg-orange-500 px-5 py-4 text-sm text-white shadow-lg shadow-orange-500/25 transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="
              isSubmitting ||
              googleProcessing ||
              !planOptions.length
            "
          >
            {{
              isSubmitting
                ? 'Preparando pago seguro...'
                : 'Pagar con Stripe'
            }}
          </button>

          <p
            class="text-center text-xs leading-5 text-slate-500"
          >
            Serás redirigido a Stripe Checkout.
            Silver Gym no recibe ni almacena los datos de tu tarjeta.
          </p>

          <p
            class="text-center text-sm leading-5 text-slate-600"
          >
            Después del pago, tu cuenta quedará pendiente de
            activación por el administrador.
          </p>
        </form>

        <!-- FEEDBACK -->
        <p
          v-if="feedback"
          class="mt-5 rounded-2xl border px-4 py-3 text-sm"
          :class="
            feedbackTone === 'error'
              ? 'border-rose-300 bg-rose-50 text-rose-900'
              : 'border-emerald-300 bg-emerald-50 text-emerald-900'
          "
        >
          {{ feedback }}
        </p>
      </section>

      <!-- PLANES -->
      <section class="space-y-4">
        <!-- CABECERA -->
        <div
          class="rounded-[1.75rem] border border-white/10 bg-[#141110] p-6 text-white shadow-2xl shadow-red-950/20"
        >
          <span
            class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-orange-300"
          >
            <span class="h-[2px] w-[18px] bg-orange-300"></span>
            Membresía
          </span>

          <h2
            class="mt-3 text-xl font-black uppercase leading-tight text-white sm:text-2xl"
          >
            Elige tu plan.
          </h2>
        </div>

        <!-- SIN PLANES -->
        <p
          v-if="!planOptions.length"
          class="rounded-2xl border border-slate-200 bg-white p-5 text-sm font-bold text-slate-600"
        >
          Planes pendientes de configuración.
        </p>

        <!-- LISTADO DE PLANES -->
        <article
          v-for="plan in planOptions"
          :key="plan.id"
          class="cursor-pointer rounded-2xl border bg-white p-5 shadow-[0_18px_40px_rgba(15,23,42,0.08)] transition hover:-translate-y-0.5"
          :class="
            form.plan === plan.id
              ? 'border-orange-500 ring-2 ring-orange-500/20'
              : 'border-slate-200 hover:border-orange-300'
          "
          @click="form.plan = plan.id"
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-lg font-black text-slate-950">
                {{ plan.label }}
              </p>

              <p class="mt-1 text-sm leading-6 text-slate-600">
                {{ plan.detail }}
              </p>
            </div>

            <p
              class="text-2xl font-black tabular-nums text-orange-600"
            >
              S/ {{ plan.price }}
            </p>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="tag in plan.tags"
              :key="tag"
              class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.06em] text-slate-600"
            >
              {{ tag }}
            </span>
          </div>
        </article>

        <!-- CLIENTE REGISTRADO -->
        <div
          v-if="registeredClient"
          class="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-950"
        >
          <p
            class="text-xs font-bold uppercase tracking-[0.06em] text-emerald-700"
          >
            Solicitud enviada
          </p>

          <p class="mt-2 text-xl font-black">
            {{ registeredClient.name }}
          </p>

          <p class="mt-1 text-sm">
            Código: {{ registeredClient.id }}
          </p>

          <p class="text-sm">
            Estado de membresía:
            {{ registeredClient.membershipStatus }}
          </p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import {
  computed,
  onMounted,
  reactive,
  ref,
} from 'vue';

import { useRoute } from 'vue-router';

import GoogleSignInButton from '../components/GoogleSignInButton.vue';

import {
  getVerifiedGoogleProfile,
} from '../services/authService';

import { apiGet } from '../services/apiClient';

import { useGymStore } from '../stores/gymStore';


/* -------------------------------------------------------------------------- */
/* INSTANCIAS                                                                 */
/* -------------------------------------------------------------------------- */

const route = useRoute();

const gymStore = useGymStore();


/* -------------------------------------------------------------------------- */
/* ESTADOS                                                                    */
/* -------------------------------------------------------------------------- */

const googleCredential = ref('');

const googleProcessing = ref(false);

const googleError = ref('');

const feedback = ref('');

const feedbackTone = ref('success');

const isSubmitting = ref(false);

const registeredClient = ref(null);

const backendPlans = ref([]);


/* -------------------------------------------------------------------------- */
/* PLANES POR DEFECTO                                                         */
/* -------------------------------------------------------------------------- */

const defaultPlans = [
  {
    id_pm: 1,
    nombre_plan: 'MENSUAL',
    duracion: '30 dias',
    precio: 79,
    descripcion: 'Acceso completo por 30 dias.',
    activo: true,
  },

  {
    id_pm: 2,
    nombre_plan: '3 MESES',
    duracion: '90 dias',
    precio: 199,
    descripcion: 'Plan trimestral para progreso sostenido.',
    activo: true,
  },

  {
    id_pm: 3,
    nombre_plan: 'ANUAL',
    duracion: '365 dias',
    precio: 699,
    descripcion: 'Membresia anual con mejor precio acumulado.',
    activo: true,
  },
];


/* -------------------------------------------------------------------------- */
/* UTILIDADES PLANES                                                          */
/* -------------------------------------------------------------------------- */

const normalizePlanName = (value) =>
  String(value || '')
    .trim()
    .toUpperCase();


const formatPlanLabel = (value) =>
  normalizePlanName(value)
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) => letter.toUpperCase()
    );


/* -------------------------------------------------------------------------- */
/* OPCIONES DE PLAN                                                           */
/* -------------------------------------------------------------------------- */

const planOptions = computed(() =>
  (
    backendPlans.value.length
      ? backendPlans.value
      : defaultPlans
  )
    .filter(
      (plan) =>
        plan.activo ??
        plan.active ??
        true
    )
    .map((plan) => {
      const name = normalizePlanName(
        plan.nombre_plan || plan.name
      );

      const duration = String(
        plan.duracion ||
        plan.description ||
        ''
      ).trim();

      return {
        id: name,

        label: formatPlanLabel(name),

        price: Number(
          plan.precio ??
          plan.price ??
          0
        ),

        detail: duration
          ? `Acceso por ${duration}.`
          : 'Plan disponible para registro.',

        tags: duration
          ? [duration]
          : [],
      };
    })
    .filter((plan) => plan.id)
);


/* -------------------------------------------------------------------------- */
/* FORMULARIO                                                                 */
/* -------------------------------------------------------------------------- */

const form = reactive({
  nombre: '',

  correo: '',

  telefono: '',

  dni: '',

  password: '',

  plan: normalizePlanName(
    route.query.plan
  ),
});


/* -------------------------------------------------------------------------- */
/* SINCRONIZAR PLAN SELECCIONADO                                              */
/* -------------------------------------------------------------------------- */

const syncSelectedPlan = () => {
  if (!planOptions.value.length) {
    form.plan = '';
    return;
  }

  const planExists =
    planOptions.value.some(
      (plan) =>
        plan.id === form.plan
    );

  if (!planExists) {
    form.plan =
      planOptions.value[0].id;
  }
};


/* -------------------------------------------------------------------------- */
/* CARGAR PLANES                                                              */
/* -------------------------------------------------------------------------- */

const loadPlans = async () => {
  try {
    const list = await apiGet(
      '/planes-membresia'
    );

    backendPlans.value =
      Array.isArray(list)
        ? list
        : [];
  } catch (error) {
    console.error(
      'No se pudieron cargar los planes:',
      error
    );

    /*
     * Mantiene la funcionalidad original:
     * si falla el backend, se utilizan los planes locales.
     */
    backendPlans.value =
      defaultPlans;
  } finally {
    syncSelectedPlan();
  }
};


/* -------------------------------------------------------------------------- */
/* LIMPIAR CUENTA GOOGLE                                                      */
/* -------------------------------------------------------------------------- */

const clearGoogleAccount = () => {
  googleCredential.value = '';

  googleError.value = '';

  /*
   * El correo deja de estar bloqueado y el usuario
   * puede introducir una cuenta manualmente.
   */
  form.correo = '';

  form.password = '';
};


/* -------------------------------------------------------------------------- */
/* SELECCIONAR CUENTA GOOGLE                                                  */
/* -------------------------------------------------------------------------- */

const selectGoogleAccount = async (
  credential
) => {
  if (
    isSubmitting.value ||
    googleProcessing.value
  ) {
    return;
  }

  if (!credential) {
    googleError.value =
      'Google no devolvió una credencial válida.';

    return;
  }

  googleProcessing.value = true;

  googleError.value = '';

  /*
   * Eliminamos cualquier Google Credential anterior
   * antes de verificar la nueva.
   */
  googleCredential.value = '';

  try {
    const profile =
      await getVerifiedGoogleProfile(
        credential
      );

    if (!profile?.email) {
      throw new Error(
        'Google no devolvió un correo válido.'
      );
    }

    form.nombre =
      profile.name ||
      form.nombre;

    form.correo =
      profile.email;

    /*
     * Cuando esto tiene valor:
     * - correo queda readonly
     * - contraseña desaparece
     * - credential se manda al backend.
     */
    googleCredential.value =
      credential;

    /*
     * No necesitamos contraseña local cuando
     * el registro utiliza Google.
     */
    form.password = '';
  } catch (error) {
    googleCredential.value = '';

    googleError.value =
      error?.message ||
      'No se pudo verificar tu cuenta de Google';
  } finally {
    googleProcessing.value = false;
  }
};


/* -------------------------------------------------------------------------- */
/* ENVIAR REGISTRO                                                           */
/* -------------------------------------------------------------------------- */

const submitRegistration = async () => {
  if (
    isSubmitting.value ||
    googleProcessing.value
  ) {
    return;
  }

  isSubmitting.value = true;

  feedback.value = '';

  registeredClient.value = null;


  try {
    if (!form.plan) {
      throw new Error(
        'No hay planes configurados para registrar clientes.'
      );
    }

    /*
     * Conservamos ambas formas de registro:
     *
     * Registro tradicional:
     * google_credential = ''
     *
     * Registro Google:
     * google_credential = credencial Google
     */
    const result =
      await gymStore.registerPublicClient({
        ...form,

        google_credential:
          googleCredential.value,
      });


    const {
      client,
      payment,
    } = result;


    registeredClient.value =
      client;


    /*
     * Verificar que Stripe haya generado
     * correctamente el Checkout.
     */
    if (!payment?.checkout_url) {
      throw new Error(
        payment?.message ||
        'Stripe no está configurado. Contacta al administrador.'
      );
    }


    feedbackTone.value =
      'success';


    feedback.value =
      'Preregistro creado. Abriendo el checkout seguro de Stripe. Tu cuenta requerirá activación por el administrador.';


    /*
     * Redirección a Stripe Checkout.
     */
    window.location.assign(
      payment.checkout_url
    );
  } catch (error) {
    feedbackTone.value =
      'error';

    feedback.value =
      error instanceof Error
        ? error.message
        : 'No se pudo completar el registro.';
  } finally {
    isSubmitting.value =
      false;
  }
};


/* -------------------------------------------------------------------------- */
/* INICIALIZACIÓN                                                             */
/* -------------------------------------------------------------------------- */

onMounted(() => {
  loadPlans();
});
</script>

<style scoped>
.register-page {
  font-family:
    'Manrope',
    'Segoe UI',
    'Trebuchet MS',
    sans-serif;
}

.register-page h1,
.register-page h2,
.register-page h3 {
  font-family:
    'Anton',
    'Manrope',
    sans-serif;

  font-weight: 400;

  letter-spacing: 0.01em;
}

.register-page .btn-cta {
  font-family:
    'Anton',
    'Manrope',
    sans-serif;

  font-weight: 400;

  letter-spacing: 0.02em;

  text-transform: uppercase;
}
</style>