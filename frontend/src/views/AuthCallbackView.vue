<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
    <div class="text-center">
      <div class="mb-4">
        <div class="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto"></div>
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-2">Procesando autenticación...</h2>
      <p class="text-gray-600">{{ statusMessage }}</p>
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

    const code = route.query.code;
    const error = route.query.error;

    if (error) {
      redirectToLogin('Google devolvió un error de autenticación. Volviendo al login.');
      return;
    }

    if (code) {
      redirectToLogin('Este flujo requiere intercambio en backend. Redirigiendo al login seguro.');
      return;
    }

    redirectToLogin('No se encontró una sesión válida. Redirigiendo al login.');
  } catch (error) {
    console.error('Error en autenticación:', error);
    redirectToLogin('No se pudo completar la autenticación. Redirigiendo al login.');
  }
});
</script>
