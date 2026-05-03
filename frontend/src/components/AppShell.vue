<template>
  <div class="min-h-screen bg-slate-950 text-slate-50">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-28 -right-20 h-80 w-80 rounded-full bg-cyan-500/20 blur-3xl"></div>
      <div class="absolute top-40 -left-16 h-72 w-72 rounded-full bg-indigo-500/20 blur-3xl"></div>
    </div>

    <div class="relative mx-auto flex min-h-screen max-w-[1600px]">
      <aside class="hidden xl:flex w-80 flex-col border-r border-white/10 bg-slate-900/80 backdrop-blur-xl">
        <div class="p-6 border-b border-white/10">
          <div class="text-xs uppercase tracking-[0.35em] text-cyan-300/80">{{ APP_CONFIG.appName }}</div>
          <h1 class="mt-3 text-3xl font-black leading-tight">Control<br />Center</h1>
          <p class="mt-3 text-sm text-slate-300">Panel web para usuarios y administración del gimnasio.</p>
        </div>

        <div class="p-6 border-b border-white/10">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Sesión activa</p>
            <div class="mt-3 flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/20 text-lg font-bold text-cyan-200">
                {{ userInitials }}
              </div>
              <div>
                <p class="font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="text-sm text-slate-300">{{ user?.email || 'Sin correo' }}</p>
              </div>
            </div>
          </div>
        </div>

        <nav class="flex-1 p-4">
          <p class="px-3 text-xs uppercase tracking-[0.35em] text-slate-400">Navegación</p>
          <div class="mt-4 space-y-2">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-3 rounded-2xl px-4 py-3 transition"
              :class="isActive(link.to)
                ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                : 'text-slate-200 hover:bg-white/8 hover:text-white'"
            >
              <span class="text-lg">{{ link.icon }}</span>
              <span class="font-medium">{{ link.label }}</span>
            </router-link>
          </div>
        </nav>

        <div class="p-6 border-t border-white/10">
          <button
            class="w-full rounded-2xl bg-white/10 px-4 py-3 font-semibold text-white transition hover:bg-white/15"
            @click="handleLogout"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl xl:hidden">
          <div class="flex items-center justify-between p-4">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-cyan-300/80">{{ APP_CONFIG.appName }}</p>
              <h1 class="text-xl font-black">{{ currentSectionTitle }}</h1>
            </div>
            <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold" @click="handleLogout">
              Salir
            </button>
          </div>
          <div class="overflow-x-auto px-4 pb-4">
            <div class="flex gap-2 min-w-max">
              <router-link
                v-for="link in navigationLinks"
                :key="link.to"
                :to="link.to"
                class="rounded-full px-4 py-2 text-sm font-medium transition"
                :class="isActive(link.to)
                  ? 'bg-cyan-500 text-slate-950'
                  : 'bg-white/5 text-slate-200'"
              >
                {{ link.label }}
              </router-link>
            </div>
          </div>
        </header>

        <main class="flex-1 p-4 sm:p-6 xl:p-8">
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { APP_CONFIG } from '../config/appConfig';

const props = defineProps({
  mode: {
    type: String,
    default: 'user',
  },
});

const route = useRoute();
const router = useRouter();
const { user, signOut, isAdmin } = useAuth();

const navigationLinks = computed(() => {
  if (props.mode === 'admin' || isAdmin.value) {
    return [
      { label: 'Panel', to: '/admin/dashboard', icon: '🏠' },
      { label: 'Usuarios', to: '/admin/users', icon: '👥' },
      { label: 'Asistencia', to: '/admin/attendance', icon: '✓' },
      { label: 'Inventario', to: '/admin/inventory', icon: '📦' },
    ];
  }

  return [
    { label: 'Panel', to: '/user/dashboard', icon: '🏠' },
    { label: 'Horarios', to: '/user/schedule', icon: '🕐' },
    { label: 'Mi asistencia', to: '/user/attendance', icon: '✓' },
  ];
});

const currentSectionTitle = computed(() => {
  const active = navigationLinks.value.find((link) => route.path.startsWith(link.to));
  return active?.label || 'Panel';
});

const userInitials = computed(() => {
  const name = user.value?.name || 'GC';
  return name
    .split(' ')
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
});

const isActive = (path) => route.path.startsWith(path);

const handleLogout = async () => {
  await signOut();
  router.push('/login');
};
</script>
