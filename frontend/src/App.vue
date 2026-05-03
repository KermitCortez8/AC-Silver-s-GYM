<template>
  <div>
    <div v-if="!authStore.isInitialized" class="flex min-h-screen items-center justify-center bg-slate-950 text-slate-50">
      <div class="text-center">
        <div class="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-cyan-400/20 border-t-cyan-300"></div>
        <p class="text-sm uppercase tracking-[0.35em] text-cyan-200">Cargando sesión...</p>
      </div>
    </div>

    <router-view v-else />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from './stores/authStore';

const authStore = useAuthStore();

onMounted(async () => {
  // Inicializar autenticación al montar la app
  await authStore.initializeAuth();
});
</script>
