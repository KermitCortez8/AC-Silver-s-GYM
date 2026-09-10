<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(220,38,38,0.20),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(127,29,29,0.16),_transparent_36%),linear-gradient(180deg,#fafafa_0%,#e5e5e5_100%)] text-slate-950">
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
              class="w-full rounded-2xl border border-orange-100 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
              placeholder="cliente@correo.com"
            />
          </label>

          <label class="block space-y-2 text-left">
            <span class="text-sm font-semibold text-slate-700">Contrasena</span>
            <input
              v-model="passwordForm.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-2xl border border-orange-100 bg-white px-4 py-3 text-slate-950 outline-none placeholder:text-slate-400 focus:border-orange-400"
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

        <div class="my-6 flex items-center gap-3 text-xs uppercase tracking-[0.24em] text-slate-400">
          <span class="h-px flex-1 bg-orange-100"></span>
          Google
          <span class="h-px flex-1 bg-orange-100"></span>
        </div>

        <GoogleSignInButton :disabled="processing" @credential="completeLogin" />
        <form v-if="linkCredential" class="mt-5 space-y-3" @submit.prevent="completeLogin(linkCredential, linkPassword)">
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-slate-700">Contraseña actual del gimnasio</span>
            <input v-model="linkPassword" required type="password" autocomplete="current-password" class="w-full rounded-2xl border border-orange-100 px-4 py-3" />
          </label>
          <button type="submit" :disabled="processing" class="w-full rounded-2xl bg-orange-500 px-4 py-3 font-bold text-white disabled:opacity-60">Vincular Google y entrar</button>
          <button type="button" :disabled="processing" class="w-full text-sm text-slate-600 underline" @click="cancelLink">Cancelar vinculación</button>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import GoogleSignInButton from '../components/GoogleSignInButton.vue';
import { authenticateWithGoogleCredential, authenticateWithPassword } from '../services/authService';

const router = useRouter();
const { signIn, initializeAuth, isAuthenticated, dashboardPath } = useAuth();
const googleError = ref('');
const linkCredential = ref('');
const linkPassword = ref('');
const processing = ref(false);
const passwordForm = reactive({
  correo: '',
  password: '',
});

/**
 * Gestiona esta acción de la vista.
 */
const navigateByRole = (role) => {
  router.replace(role === 'trainer' ? '/trainer/dashboard' : ['admin', 'staff'].includes(role) ? '/admin/dashboard' : '/user/dashboard');
};

const cancelLink = () => {
  linkCredential.value = '';
  linkPassword.value = '';
  googleError.value = '';
};

/**
 * Gestiona esta acción de la vista.
 */
const completeLogin = async (credential, password = '') => {
  if (processing.value) return;
  processing.value = true;
  googleError.value = '';
  try {
    const result = await authenticateWithGoogleCredential(credential, password);
    await signIn(result.token, {
      ...result.user,
      expiresIn: result.expiresIn,
      role: result.user.role,
      authSource: result.source,
    });
    cancelLink();
    navigateByRole(result.user.role);
  } catch (error) {
    linkCredential.value = error?.code === 'google_link_required' ? credential : '';
    linkPassword.value = '';
    googleError.value = error?.message || 'No se pudo completar el inicio de sesion';
  } finally {
    processing.value = false;
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const handlePasswordLogin = async () => {
  if (processing.value) return;
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

onMounted(async () => {
  await initializeAuth();
  if (isAuthenticated.value) router.replace(dashboardPath.value);
});
</script>
