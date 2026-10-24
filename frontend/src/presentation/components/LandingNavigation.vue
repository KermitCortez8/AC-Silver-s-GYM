<template>
  <nav class="hidden items-center gap-6 text-sm font-bold uppercase tracking-[0.04em] text-slate-700 lg:flex">
    <router-link
      v-for="item in items"
      :key="item.id"
      :to="item.to"
      custom
      v-slot="{ href, navigate }"
    >
      <a
        :href="href"
        :class="route.path === '/nosotros' && item.id === 'nosotros' ? 'text-orange-600' : 'transition hover:text-orange-600'"
        :aria-current="route.path === '/nosotros' && item.id === 'nosotros' ? 'page' : undefined"
        @click="selectItem($event, item, navigate)"
      >
        {{ item.label }}
      </a>
    </router-link>
  </nav>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router';
import { registerLandingSelection } from '../utils/landingEasterEgg';

const route = useRoute();
const router = useRouter();
const items = [
  { id: 'servicios', label: 'Servicios', to: { path: '/', hash: '#servicios' } },
  { id: 'nosotros', label: 'Nosotros', to: '/nosotros' },
  { id: 'membresias', label: 'Membresias', to: { path: '/', hash: '#membresias' } },
  { id: 'ubicacion', label: 'Ubicacion', to: { path: '/', hash: '#ubicacion' } },
];

const selectItem = (event, item, navigate) => {
  // Conserva abrir enlaces en otra pestaña sin avanzar el contador de esta.
  if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
    return;
  }

  if (registerLandingSelection(item.id)) {
    event.preventDefault();
    router.push({ name: 'TpRemix' });
    return;
  }

  navigate(event);
};
</script>
