<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-950 text-slate-50">
    <div class="text-center">
      <div class="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-white/10 border-t-cyan-400"></div>
      <h2 class="text-2xl font-semibold text-white mb-2">Procesando autenticación...</h2>
      <p class="text-slate-300">{{ statusMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuth } from '../composables/useAuth';

const router = useRouter();
const route = useRoute();
const authStore = useAuth();
const statusMessage = ref('Por favor espera mientras completamos tu inicio de sesión.');

const redirectToLogin = (reason) => {
  statusMessage.value = reason;
  window.setTimeout(() => {
    router.replace('/login');
  }, 1200);
};

const redirectByRole = (role) => {
  router.replace(role === 'admin' ? '/admin' : '/user');
};

onMounted(async () => {
  try {
    await authStore.initializeAuth();

    if (authStore.isAuthenticated.value) {
      redirectByRole(authStore.isAdmin.value ? 'admin' : 'user');
      return;
    }

    if (route.query.error) {
      redirectToLogin('Google devolvió un error de autenticación. Volviendo al login.');
      return;
    }

    redirectToLogin('No se encontró una sesión válida. Redirigiendo al login.');
  } catch (error) {
    console.error('Error en autenticación:', error);
    redirectToLogin('No se pudo completar la autenticación. Redirigiendo al login.');
  }
});
</script>
