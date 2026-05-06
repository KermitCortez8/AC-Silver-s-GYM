<template>
  <div class="min-h-screen bg-slate-950 text-slate-50">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-28 right-0 h-80 w-80 rounded-full bg-cyan-500/20 blur-3xl"></div>
      <div class="absolute bottom-0 left-0 h-72 w-72 rounded-full bg-indigo-500/20 blur-3xl"></div>
    </div>

    <div class="relative mx-auto grid min-h-screen max-w-7xl items-center gap-10 px-4 py-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
      <section class="space-y-8">
        <div class="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-200">
          Vue web edition
        </div>

        <div>
          <p class="text-sm uppercase tracking-[0.4em] text-cyan-300/80">{{ APP_CONFIG.appName }}</p>
          <h1 class="mt-4 max-w-2xl text-5xl font-black leading-[0.95] text-white sm:text-6xl">
            Sistema web para membresías, asistencia e inventario.
          </h1>
          <p class="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
            Inicio de sesión con Google, paneles separados por rol y módulos reales para usuarios,
            asistencia e inventario.
          </p>
        </div>

        <div class="grid gap-4 sm:grid-cols-3">
          <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
            <p class="text-sm text-slate-400">Autenticación</p>
            <p class="mt-2 text-2xl font-bold text-white">Google real</p>
          </div>
          <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
            <p class="text-sm text-slate-400">Datos</p>
            <p class="mt-2 text-2xl font-bold text-white">CRUD local</p>
          </div>
          <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
            <p class="text-sm text-slate-400">UI</p>
            <p class="mt-2 text-2xl font-bold text-white">Dashboard</p>
          </div>
        </div>

      </section>

      <section class="rounded-[2rem] border border-white/10 bg-white/8 p-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-8">
        <div class="mb-8 text-center">
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Acceso</p>
          <h2 class="mt-3 text-3xl font-black text-white">Bienvenido</h2>
          <p class="mt-3 text-slate-300">Ingresa con Google o usa una sesión de demo para explorar la app.</p>
        </div>

        <div v-if="googleError" class="mb-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
          {{ googleError }}
        </div>

        <div class="space-y-4">
          <div ref="googleButtonRef" class="flex min-h-[48px] items-center justify-center"></div>

          <button
            v-if="APP_CONFIG.enableDemoLogin"
            class="w-full rounded-2xl bg-white px-4 py-3 font-semibold text-slate-950 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
            @click="handleDemoLogin('user')"
          >
            {{ processing ? 'Cargando...' : 'Entrar como miembro de prueba' }}
          </button>

          <button
            v-if="APP_CONFIG.enableDemoLogin"
            class="w-full rounded-2xl border border-white/15 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
            @click="handleDemoLogin('admin')"
          >
            Entrar como admin de prueba
          </button>
        </div>

        <div class="mt-6 rounded-2xl border border-white/10 bg-slate-900/60 p-4 text-sm text-slate-300">
          Tu información se usa solo para autenticarte y mantener la sesión activa mientras navegas.
        </div>

        <div class="mt-4 text-center text-xs text-slate-500">
          Soporte: {{ APP_CONFIG.supportEmail }}
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { APP_CONFIG } from '../config/appConfig';
import { GOOGLE_CONFIG } from '../config/googleConfig';
import {
  authenticateWithGoogleCredential,
  createDemoCredentials,
  loadGoogleIdentityScript,
} from '../services/authService';

const router = useRouter();
const { signIn, initializeAuth, isAuthenticated, isAdmin } = useAuth();
const googleButtonRef = ref(null);
const googleError = ref('');
const processing = ref(false);

const navigateByRole = (role) => {
  router.push(role === 'admin' ? '/admin' : '/user');
};

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
    googleError.value = error?.message || 'No se pudo completar el inicio de sesión';
  } finally {
    processing.value = false;
  }
};

const renderGoogleButton = async () => {
  if (!GOOGLE_CONFIG.webClientId) {
    googleError.value = 'Configura VITE_GOOGLE_CLIENT_ID para habilitar Google real.';
    return;
  }

  try {
    await loadGoogleIdentityScript();

    if (!window.google?.accounts?.id || !googleButtonRef.value) {
      throw new Error('Google Identity Services no está disponible');
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
    googleError.value = error?.message || 'No se pudo cargar el botón de Google';
  }
};

const handleDemoLogin = async (role) => {
  processing.value = true;
  try {
    const result = createDemoCredentials(role);
    await signIn(result.token, {
      ...result.user,
      expiresIn: result.expiresIn,
      authSource: result.source,
    });
    navigateByRole(role);
  } catch (error) {
    googleError.value = error?.message || 'No se pudo iniciar la sesión de demo';
  } finally {
    processing.value = false;
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
