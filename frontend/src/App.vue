<template>
  <div>
    <div v-if="!authStore.isInitialized" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950 text-slate-50">
      <div class="text-center">
        <div class="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-white/10 border-t-red-500"></div>
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-red-300">Cargando sesión...</p>
      </div>
    </div>

    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/authStore';

const authStore = useAuthStore();
</script>
