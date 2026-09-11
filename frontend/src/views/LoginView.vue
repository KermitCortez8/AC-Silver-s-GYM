<template>
  <div class="auth-page min-h-screen bg-[radial-gradient(circle_at_12%_8%,rgba(220,38,38,0.08),transparent_45%),radial-gradient(circle_at_88%_92%,rgba(15,23,42,0.05),transparent_45%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] text-slate-950">
    <header class="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-xl font-black italic text-orange-600">Silver Gym Surco</router-link>
        <router-link to="/registro" class="btn-cta rounded-full bg-orange-500 px-4 py-2 text-sm text-white transition hover:bg-orange-600">
          Registrarse
        </router-link>
      </div>
    </header>

    <main class="mx-auto grid max-w-[1100px] gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-stretch lg:gap-10 lg:py-16">
      <div class="relative hidden overflow-hidden rounded-[1.75rem] p-10 text-white shadow-2xl shadow-slate-900/20 lg:flex lg:flex-col lg:justify-between">
        <img
          :src="panelImage"
          alt=""
          class="absolute inset-0 h-full w-full object-cover"
          @error="handlePanelImageError"
        />
        <div class="absolute inset-0 bg-[linear-gradient(175deg,rgba(220,38,38,0.55)_0%,rgba(20,17,16,0.90)_100%)]"></div>
        <span class="relative inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.08em] text-white/80">
          <span class="h-[2px] w-[18px] bg-white/80"></span>
          Plataforma digital
        </span>
        <div class="relative">
          <svg class="h-8 w-8 text-white/90" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M6 24h6M36 24h6M12 24h4M32 24h4M16 16v16M32 16v16" />
          </svg>
          <h2 class="mt-4 text-lg font-black leading-tight">Tu progreso,<br />siempre a la mano.</h2>
          <p class="mt-3 max-w-xs text-xs leading-5 text-white/80">
            Revisa tus horarios, controla tu membresia y registra asistencia desde un solo lugar.
          </p>
        </div>
        <p class="relative text-xs font-semibold text-white/50">Silver Gym Surco &middot; Acceso de clientes y staff</p>
      </div>

      <section class="flex w-full flex-col justify-center rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-slate-900/10 sm:p-8 lg:p-10">
        <div class="mb-6">
          <p class="text-xs font-black uppercase tracking-[0.08em] text-orange-500">Acceso</p>
          <h1 class="mt-2 text-xl font-black text-slate-950">Ingreso Plataforma digital</h1>
        </div>

        <div v-if="googleError" class="mb-4 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          {{ googleError }}
        </div>

        <form class="space-y-4" @submit.prevent="handlePasswordLogin">
          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">Correo</span>
            <div class="relative">
              <svg class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 8l9 6 9-6M4 6h16a1 1 0 011 1v10a1 1 0 01-1 1H4a1 1 0 01-1-1V7a1 1 0 011-1z" /></svg>
              <input
                v-model="passwordForm.correo"
                type="email"
                autocomplete="email"
                class="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-11 pr-4 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
                placeholder="cliente@correo.com"
              />
            </div>
          </label>

          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">Contrasena</span>
            <div class="relative">
              <svg class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 10-8 0v4h8z" /></svg>
              <input
                v-model="passwordForm.password"
                type="password"
                autocomplete="current-password"
                class="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-11 pr-4 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
                placeholder="Tu contrasena"
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

        <div v-if="googleReady" class="my-6 flex items-center gap-3 text-xs uppercase tracking-[0.08em] text-slate-400">
          <span class="h-px flex-1 bg-slate-200"></span>
          Google
          <span class="h-px flex-1 bg-slate-200"></span>
        </div>

        <div v-if="googleReady" class="space-y-4">
          <div ref="googleButtonRef" class="flex min-h-[48px] items-center justify-center"></div>
        </div>

        <p class="mt-8 text-center text-sm text-slate-500">
          Aun no tienes cuenta?
          <router-link to="/registro" class="font-black text-orange-600 hover:text-orange-700">Registrate aqui</router-link>
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { GOOGLE_CONFIG } from '../config/googleConfig';
import { authenticateWithGoogleCredential, authenticateWithPassword, loadGoogleIdentityScript } from '../services/authService';
import { landingImageUrl } from '../config/publicStorage';

const router = useRouter();
const { signIn, initializeAuth, isAuthenticated, isAdmin } = useAuth();
const googleButtonRef = ref(null);
const googleError = ref('');
const googleReady = ref(Boolean(GOOGLE_CONFIG.webClientId));
const processing = ref(false);
const passwordForm = reactive({
  correo: '',
  password: '',
});

const panelImage = landingImageUrl('fitness.jpg');

/**
 * Gestiona esta acción de la vista.
 */
const handlePanelImageError = (event) => {
  event.currentTarget.style.display = 'none';
};

/**
 * Gestiona esta acción de la vista.
 */
const navigateByRole = (role) => {
  router.push(role === 'user' ? '/user' : '/admin');
};

/**
 * Gestiona esta acción de la vista.
 */
const completeLogin = async (credential) => {
  processing.value = true;
  try {
    const result = await authenticateWithGoogleCredential(credential);
    await signIn(result.token, {
      ...result.user,
      expiresIn: result.expiresIn,
      role: result.user.role,
      authSource: result.source,
    });
    navigateByRole(result.user.role);
  } catch (error) {
    googleError.value = error?.message || 'No se pudo completar el inicio de sesion';
  } finally {
    processing.value = false;
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const handlePasswordLogin = async () => {
  processing.value = true;
  googleError.value = '';
  try {
    const result = await authenticateWithPassword(passwordForm);
    await signIn(result.token, {
      ...result.user,
      expiresIn: result.expiresIn,
      role: result.user.role,
      authSource: result.source,
    });
    navigateByRole(result.user.role);
  } catch (error) {
    googleError.value = error?.message || 'Correo o contrasena incorrectos';
  } finally {
    processing.value = false;
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const renderGoogleButton = async () => {
  if (!GOOGLE_CONFIG.webClientId) {
    googleReady.value = false;
    return;
  }

  try {
    await loadGoogleIdentityScript();

    if (!window.google?.accounts?.id || !googleButtonRef.value) {
      throw new Error('Google no esta disponible');
    }

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CONFIG.webClientId,
      callback: async (response) => {
        await completeLogin(response.credential);
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
      text: 'signin_with',
      width: 320,
    });
  } catch (error) {
    googleError.value = error?.message || 'No se pudo cargar Google';
  }
};

onMounted(async () => {
  await initializeAuth();

  if (isAuthenticated.value) {
    navigateByRole(isAdmin.value ? 'admin' : 'user');
    return;
  }

  await renderGoogleButton();
});

watch(isAuthenticated, (nextValue) => {
  if (nextValue) {
    navigateByRole(isAdmin.value ? 'admin' : 'user');
  }
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
