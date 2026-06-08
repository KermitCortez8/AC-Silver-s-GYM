<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.16),_transparent_32%),linear-gradient(180deg,#020617_0%,#08101f_100%)] text-slate-50">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-28 right-0 h-96 w-96 rounded-full bg-cyan-400/20 blur-3xl"></div>
      <div class="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-emerald-400/15 blur-3xl"></div>
    </div>

    <div class="relative grid min-h-screen w-full items-center gap-10 px-5 py-10 sm:px-8 lg:grid-cols-[1fr_520px] lg:px-12 2xl:px-16">
      <section class="space-y-8">
        <div class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200">
          <span class="h-2 w-2 rounded-full bg-cyan-400"></span>
          Backend FastAPI conectado
        </div>

        <div>
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-300/80">{{ APP_CONFIG.appName }}</p>
          <h1 class="mt-4 max-w-2xl text-5xl font-black leading-[0.95] text-white sm:text-6xl">
            Un frontend nuevo para clientes, asistencia, inventario y operación.
          </h1>
          <p class="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
            La interfaz se sincroniza con el backend real y conserva Google Sign-In, panel de administración y la vista de miembro.
          </p>
        </div>

        <div class="grid gap-4 sm:grid-cols-3">
          <div class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
            <p class="text-sm text-slate-400">Autenticación</p>
            <p class="mt-2 text-2xl font-black text-white">Google + backend</p>
          </div>
          <div class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
            <p class="text-sm text-slate-400">Flujos</p>
            <p class="mt-2 text-2xl font-black text-white">Clientes y asistencia</p>
          </div>
          <div class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
            <p class="text-sm text-slate-400">Operación</p>
            <p class="mt-2 text-2xl font-black text-white">Inventario y tickets</p>
          </div>
        </div>
      </section>

      <section class="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-8">
        <div class="mb-8 text-center">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-300/80">Acceso</p>
          <h2 class="mt-3 text-3xl font-black text-white">Iniciar sesión</h2>
          <p class="mt-3 text-slate-300">Usa tu cuenta de Google o una sesión demo para explorar el panel nuevo.</p>
        </div>

        <div v-if="googleError" class="mb-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
          {{ googleError }}
        </div>

        <form class="space-y-4" @submit.prevent="handlePasswordLogin">
          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-300">Correo</span>
            <input
              v-model="passwordForm.correo"
              type="email"
              autocomplete="email"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-300"
              placeholder="cliente@correo.com"
            />
          </label>

          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-300">Contrasena</span>
            <input
              v-model="passwordForm.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-300"
              placeholder="Tu contrasena"
            />
          </label>

          <button
            type="submit"
            class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
          >
            {{ processing ? 'Validando...' : 'Entrar con correo' }}
          </button>
        </form>

        <div class="my-5 flex items-center gap-3 text-xs uppercase tracking-[0.24em] text-slate-500">
          <span class="h-px flex-1 bg-white/10"></span>
          Google
          <span class="h-px flex-1 bg-white/10"></span>
        </div>

        <div class="space-y-4">
          <div ref="googleButtonRef" class="flex min-h-[48px] items-center justify-center"></div>

          <button
            v-if="APP_CONFIG.enableDemoLogin"
            class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
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

        <div class="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          El backend responde en <span class="text-white">/auth/password</span>, <span class="text-white">/auth/google</span> y valida la sesion en <span class="text-white">/auth/me</span>.
        </div>

        <div class="mt-4 text-center text-sm text-slate-400">
          <router-link to="/registro" class="font-semibold text-cyan-200 hover:text-cyan-100">Crear cuenta de cliente</router-link>
        </div>

        <div class="mt-4 text-center text-xs text-slate-500">
          Soporte: {{ APP_CONFIG.supportEmail }}
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { APP_CONFIG } from '../config/appConfig';
import { GOOGLE_CONFIG } from '../config/googleConfig';
import { authenticateWithGoogleCredential, authenticateWithPassword, createDemoCredentials, loadGoogleIdentityScript } from '../services/authService';

const router = useRouter();
const { signIn, initializeAuth, isAuthenticated, isAdmin } = useAuth();
const googleButtonRef = ref(null);
const googleError = ref('');
const processing = ref(false);
const passwordForm = reactive({
  correo: '',
  password: '',
});

const navigateByRole = (role) => {
  router.push(role === 'user' ? '/user' : '/admin');
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
