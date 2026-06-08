<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.45),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(249,115,22,0.28),_transparent_36%),linear-gradient(180deg,#fff7ed_0%,#ffedd5_100%)] text-slate-950">
    <header class="border-b border-orange-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <router-link to="/" class="text-xl font-black italic text-orange-600">Silver Gym Surco</router-link>
        <router-link to="/registro" class="rounded-full bg-orange-500 px-4 py-2 text-sm font-black text-white transition hover:bg-orange-600">
          Registrarse
        </router-link>
      </div>
    </header>

    <main class="mx-auto flex min-h-[calc(100vh-73px)] max-w-[1200px] items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <section class="w-full max-w-xl rounded-[2rem] border border-orange-100 bg-white p-6 shadow-2xl shadow-orange-900/10 sm:p-8">
        <div class="mb-8 text-center">
          <p class="text-xs font-black uppercase tracking-[0.32em] text-orange-500">Acceso</p>
          <h1 class="mt-3 text-4xl font-black text-slate-950">Ingreso Plataforma digital</h1>
        </div>

        <div v-if="googleError" class="mb-4 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          {{ googleError }}
        </div>

        <form class="space-y-4" @submit.prevent="handlePasswordLogin">
          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">Correo</span>
            <input
              v-model="passwordForm.correo"
              type="email"
              autocomplete="email"
              class="w-full rounded-2xl border border-orange-100 bg-[#fff7ed] px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
              placeholder="cliente@correo.com"
            />
          </label>

          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">Contrasena</span>
            <input
              v-model="passwordForm.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-2xl border border-orange-100 bg-[#fff7ed] px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
              placeholder="Tu contrasena"
            />
          </label>

          <button
            type="submit"
            class="w-full rounded-2xl bg-orange-500 px-4 py-3 font-black text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
          >
            {{ processing ? 'Validando...' : 'Entrar con correo' }}
          </button>
        </form>

        <div v-if="googleReady" class="my-6 flex items-center gap-3 text-xs uppercase tracking-[0.24em] text-slate-400">
          <span class="h-px flex-1 bg-orange-100"></span>
          Google
          <span class="h-px flex-1 bg-orange-100"></span>
        </div>

        <div v-if="googleReady" class="space-y-4">
          <div ref="googleButtonRef" class="flex min-h-[48px] items-center justify-center"></div>
        </div>

        <div v-if="APP_CONFIG.enableDemoLogin" class="mt-5 grid gap-3 sm:grid-cols-2">
          <button
            class="rounded-2xl border border-orange-200 bg-orange-50 px-4 py-3 font-bold text-orange-700 transition hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
            @click="handleDemoLogin('user')"
          >
            Miembro de prueba
          </button>

          <button
            class="rounded-2xl border border-orange-200 bg-orange-50 px-4 py-3 font-bold text-orange-700 transition hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="processing"
            @click="handleDemoLogin('admin')"
          >
            Admin de prueba
          </button>
        </div>
      </section>
    </main>
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
const googleReady = ref(Boolean(GOOGLE_CONFIG.webClientId));
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
    googleError.value = error?.message || 'No se pudo completar el inicio de sesion';
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
    googleError.value = error?.message || 'No se pudo iniciar la sesion de prueba';
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
