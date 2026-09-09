<template>
  <div>
    <div v-if="!authStore.isInitialized" class="app-loading-screen fixed inset-0 z-50 flex items-center justify-center">
      <div class="text-center">
        <div class="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-white/10 border-t-red-500"></div>
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-red-300">Cargando sesión...</p>
      </div>
    </div>

    <router-view />
    <div v-if="authStore.isAuthenticated && gymStore.syncError" role="alert" class="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-3xl rounded-2xl border border-red-300 bg-red-50 p-4 text-red-950 shadow-xl">
      <p class="font-bold">No se pudieron actualizar todos los datos</p>
      <p class="mt-1 max-h-32 overflow-y-auto text-sm">{{ gymStore.syncError }}</p>
      <p class="mt-1 text-sm">Los datos que ves pueden estar desactualizados.</p>
      <button type="button" :disabled="gymStore.isSyncing" class="mt-3 rounded-lg bg-red-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50" @click="retrySync">
        {{ gymStore.isSyncing ? 'Actualizando…' : 'Reintentar' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/authStore';
import { useGymStore } from './stores/gymStore';

const authStore = useAuthStore();
const gymStore = useGymStore();
const retrySync = () => gymStore.fetchFromBackend().catch(() => {
  // El store conserva el error para mostrarlo en el aviso.
});
</script>
