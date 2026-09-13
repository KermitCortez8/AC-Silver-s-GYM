<template>
  <div
    class="auth-page min-h-screen bg-[radial-gradient(circle_at_12%_8%,rgba(220,38,38,0.08),transparent_45%),radial-gradient(circle_at_88%_92%,rgba(15,23,42,0.05),transparent_45%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] text-slate-950"
  >
    <!-- HEADER -->
    <header class="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div
        class="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8"
      >
        <router-link
          to="/"
          class="text-xl font-black italic text-orange-600"
        >
          Silver Gym Surco
        </router-link>

        <router-link
          to="/registro"
          class="btn-cta rounded-full bg-orange-500 px-4 py-2 text-sm text-white transition hover:bg-orange-600"
        >
          Registrarse
        </router-link>
      </div>
    </header>

    <!-- CONTENIDO -->
    <main
      class="mx-auto grid max-w-[1100px] gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-stretch lg:gap-10 lg:py-16"
    >
      <!-- PANEL IZQUIERDO -->
      <div
        class="relative hidden overflow-hidden rounded-[1.75rem] p-10 text-white shadow-2xl shadow-slate-900/20 lg:flex lg:flex-col lg:justify-between"
      >
        <img
          :src="panelImage"
          alt=""
          class="absolute inset-0 h-full w-full object-cover"
          @error="handlePanelImageError"
        />

        <div
          class="absolute inset-0 bg-[linear-gradient(175deg,rgba(220,38,38,0.55)_0%,rgba(20,17,16,0.90)_100%)]"
        ></div>

        <span
          class="relative inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-white/80"
        >
          <span class="h-[2px] w-[18px] bg-white/80"></span>
          Plataforma digital
        </span>

        <div class="relative">
          <svg
            class="h-8 w-8 text-white/90"
            viewBox="0 0 48 48"
            fill="none"
            stroke="currentColor"
            stroke-width="2.4"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path
              d="M6 24h6M36 24h6M12 24h4M32 24h4M16 16v16M32 16v16"
            />
          </svg>

          <h2 class="mt-4 text-lg font-black leading-tight">
            Tu progreso,<br />
            siempre a la mano.
          </h2>

          <p class="mt-3 max-w-xs text-xs leading-5 text-white/80">
            Revisa tus horarios, controla tu membresía y registra asistencia
            desde un solo lugar.
          </p>
        </div>

        <p class="relative text-xs font-semibold text-white/50">
          Silver Gym Surco &middot; Acceso de clientes y staff
        </p>
      </div>

      <!-- LOGIN -->
      <section
        class="flex w-full flex-col justify-center rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-slate-900/10 sm:p-8 lg:p-10"
      >
        <div class="mb-6">
          <p
            class="text-xs font-black uppercase tracking-[0.08em] text-orange-500"
          >
            Acceso
          </p>

          <h1 class="mt-2 text-xl font-black text-slate-950">
            Ingreso Plataforma digital
          </h1>
        </div>

        <!-- ERRORES -->
        <div
          v-if="googleError"
          class="mb-4 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"
        >
          {{ googleError }}
        </div>

        <!-- LOGIN CORREO / PASSWORD -->
        <form class="space-y-4" @submit.prevent="handlePasswordLogin">
          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">
              Correo
            </span>

            <div class="relative">
              <svg
                class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M3 8l9 6 9-6M4 6h16a1 1 0 011 1v10a1 1 0 01-1 1H4a1 1 0 01-1-1V7a1 1 0 011-1z"
                />
              </svg>

              <input
                v-model="passwordForm.correo"
                type="email"
                required
                autocomplete="email"
                class="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-11 pr-4 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
                placeholder="cliente@correo.com"
              />
            </div>
          </label>

          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">
              Contraseña
            </span>

            <div class="relative">
              <svg
                class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 10-8 0v4h8z"
                />
              </svg>

              <input
                v-model="passwordForm.password"
                type="password"
                required
                autocomplete="current-password"
                class="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-11 pr-4 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
                placeholder="Tu contraseña"
              />
            </div>
          </label>

          <button
            type="submit"
            class="btn-cta w-full rounded-full bg-orange-500 px-4 py-3 text-sm text-white shadow-lg shadow-orange-500/25 transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
          >
            {{ processing ? 'Validando...' : 'Entrar con correo' }}
          </button>
        </form>

        <!-- SEPARADOR GOOGLE -->
        <div
          v-if="googleReady"
          class="my-6 flex items-center gap-3 text-xs uppercase tracking-[0.08em] text-slate-400"
        >
          <span class="h-px flex-1 bg-slate-200"></span>

          Google

          <span class="h-px flex-1 bg-slate-200"></span>
        </div>

        <!-- GOOGLE SIGN IN -->
        <div v-if="googleReady" class="space-y-4">
          <div
            ref="googleButtonRef"
            class="flex min-h-[48px] items-center justify-center"
          ></div>
        </div>

        <!--
          CONSERVAMOS LA FUNCIONALIDAD DE "resend":
          Vincular una cuenta existente del gimnasio con Google.
        -->
        <form
          v-if="linkCredential"
          class="mt-5 space-y-3"
          @submit.prevent="
            completeLogin(linkCredential, linkPassword)
          "
        >
          <div
            class="rounded-2xl border border-orange-200 bg-orange-50 p-4"
          >
            <p class="text-sm text-slate-700">
              Esta cuenta todavía no está vinculada con Google.
              Ingresa tu contraseña actual para completar la vinculación.
            </p>
          </div>

          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">
              Contraseña actual del gimnasio
            </span>

            <input
              v-model="linkPassword"
              required
              type="password"
              autocomplete="current-password"
              class="w-full rounded-2xl border border-orange-100 px-4 py-3 outline-none focus:border-orange-400"
            />
          </label>

          <button
            type="submit"
            :disabled="processing"
            class="w-full rounded-2xl bg-orange-500 px-4 py-3 font-bold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{ processing ? 'Vinculando...' : 'Vincular Google y entrar' }}
          </button>

          <button
            type="button"
            :disabled="processing"
            class="w-full text-sm text-slate-600 underline disabled:opacity-60"
            @click="cancelLink"
          >
            Cancelar vinculación
          </button>
        </form>

        <!-- REGISTRO -->
        <p class="mt-8 text-center text-sm text-slate-500">
          ¿Aún no tienes cuenta?

          <router-link
            to="/registro"
            class="font-black text-orange-600 hover:text-orange-700"
          >
            Regístrate aquí
          </router-link>
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import {
  nextTick,
  onMounted,
  reactive,
  ref,
} from 'vue';

import { useRouter } from 'vue-router';

import { useAuth } from '../composables/useAuth';

import { GOOGLE_CONFIG } from '../config/googleConfig';

import {
  authenticateWithGoogleCredential,
  authenticateWithPassword,
  loadGoogleIdentityScript,
} from '../services/authService';

import { landingImageUrl } from '../config/publicStorage';


const router = useRouter();

const {
  signIn,
  initializeAuth,
  isAuthenticated,
  dashboardPath,
} = useAuth();


/* -------------------------------------------------------------------------- */
/* ESTADOS                                                                    */
/* -------------------------------------------------------------------------- */

const googleError = ref('');

const linkCredential = ref('');

const linkPassword = ref('');

const processing = ref(false);

const googleReady = ref(false);

const googleButtonRef = ref(null);


const passwordForm = reactive({
  correo: '',
  password: '',
});


/* -------------------------------------------------------------------------- */
/* IMAGEN                                                                     */
/* -------------------------------------------------------------------------- */

const panelImage = landingImageUrl('fitness.jpg');


const handlePanelImageError = (event) => {
  event.currentTarget.style.display = 'none';
};


/* -------------------------------------------------------------------------- */
/* NAVEGACIÓN SEGÚN ROL                                                       */
/* -------------------------------------------------------------------------- */

const navigateByRole = (role) => {
  if (role === 'trainer') {
    router.replace('/trainer/dashboard');
    return;
  }

  if (['admin', 'staff'].includes(role)) {
    router.replace('/admin/dashboard');
    return;
  }

  router.replace('/user/dashboard');
};


/* -------------------------------------------------------------------------- */
/* CANCELAR VINCULACIÓN GOOGLE                                                */
/* -------------------------------------------------------------------------- */

const cancelLink = () => {
  linkCredential.value = '';
  linkPassword.value = '';
  googleError.value = '';
};


/* -------------------------------------------------------------------------- */
/* LOGIN / VINCULACIÓN CON GOOGLE                                             */
/* -------------------------------------------------------------------------- */

const completeLogin = async (credential, password = '') => {
  if (processing.value) {
    return;
  }

  if (!credential) {
    googleError.value =
      'No se recibió una credencial válida de Google.';
    return;
  }

  processing.value = true;
  googleError.value = '';

  try {
    const result = await authenticateWithGoogleCredential(
      credential,
      password
    );

    await signIn(result.token, {
      ...result.user,

      expiresIn: result.expiresIn,

      role: result.user.role,

      authSource: result.source,
    });

    cancelLink();

    navigateByRole(result.user.role);
  } catch (error) {
    /*
     * Si el backend indica que la cuenta Google tiene que
     * vincularse con la cuenta actual del gimnasio,
     * guardamos temporalmente la credential.
     */
    if (error?.code === 'google_link_required') {
      linkCredential.value = credential;
    } else {
      linkCredential.value = '';
    }

    linkPassword.value = '';

    googleError.value =
      error?.message ||
      'No se pudo completar el inicio de sesión con Google.';
  } finally {
    processing.value = false;
  }
};


/* -------------------------------------------------------------------------- */
/* LOGIN CORREO / PASSWORD                                                    */
/* -------------------------------------------------------------------------- */

const handlePasswordLogin = async () => {
  if (processing.value) {
    return;
  }

  processing.value = true;
  googleError.value = '';

  try {
    const result = await authenticateWithPassword({
      correo: passwordForm.correo.trim(),
      password: passwordForm.password,
    });

    await signIn(result.token, {
      ...result.user,

      expiresIn: result.expiresIn,

      role: result.user.role,

      authSource: result.source,
    });

    navigateByRole(result.user.role);
  } catch (error) {
    googleError.value =
      error?.message ||
      'Correo o contraseña incorrectos.';
  } finally {
    processing.value = false;
  }
};


/* -------------------------------------------------------------------------- */
/* INICIALIZAR GOOGLE IDENTITY SERVICES                                       */
/* -------------------------------------------------------------------------- */

const initializeGoogleSignIn = async () => {
  try {
    /*
     * Conservamos el sistema que estaba implementando
     * la rama develop.
     */
    await loadGoogleIdentityScript();

    const googleAccounts = window.google?.accounts?.id;

    if (!googleAccounts) {
      throw new Error(
        'Google Identity Services no pudo inicializarse.'
      );
    }

    const clientId = GOOGLE_CONFIG.webClientId;

    if (!clientId) {
      throw new Error(
        'No se encontró el Client ID de Google.'
      );
    }

    /*
     * Primero hacemos visible el contenedor.
     */
    googleReady.value = true;

    /*
     * Esperamos a que Vue lo coloque en el DOM.
     */
    await nextTick();

    if (!googleButtonRef.value) {
      throw new Error(
        'No se pudo crear el contenedor del botón de Google.'
      );
    }

    /*
     * Configurar Google Identity.
     */
    googleAccounts.initialize({
      client_id: clientId,

      callback: (response) => {
        if (!response?.credential) {
          googleError.value =
            'Google no devolvió una credencial válida.';
          return;
        }

        completeLogin(response.credential);
      },

      auto_select: false,

      cancel_on_tap_outside: true,
    });

    /*
     * Evitar que se duplique el botón si por alguna razón
     * la función vuelve a ejecutarse.
     */
    googleButtonRef.value.innerHTML = '';

    /*
     * Renderizar botón Google.
     */
    googleAccounts.renderButton(
      googleButtonRef.value,
      {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'pill',
        logo_alignment: 'left',
        width: 320,
      }
    );
  } catch (error) {
    console.error(
      'Error inicializando Google Sign-In:',
      error
    );

    googleReady.value = false;

    googleError.value =
      error?.message ||
      'No se pudo cargar el inicio de sesión con Google.';
  }
};


/* -------------------------------------------------------------------------- */
/* MOUNT                                                                      */
/* -------------------------------------------------------------------------- */

onMounted(async () => {
  /*
   * Primero verificar si ya existe una sesión.
   */
  await initializeAuth();

  if (isAuthenticated.value) {
    router.replace(dashboardPath.value);
    return;
  }

  /*
   * Solo cargar Google si realmente necesitamos mostrar
   * la pantalla de login.
   */
  await initializeGoogleSignIn();
});
</script>

<style scoped>
.auth-page {
  font-family: 'Manrope', 'Segoe UI', 'Trebuchet MS', sans-serif;
}

.auth-page h1,
.auth-page h2,
.auth-page h3 {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.01em;
}

.auth-page .btn-cta {
  font-family: 'Anton', 'Manrope', sans-serif;
  font-weight: 400;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
</style>
