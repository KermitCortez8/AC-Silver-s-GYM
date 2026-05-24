<template>
  <div class="app-shell min-h-screen bg-slate-950 text-slate-50">
    <div class="relative mx-auto flex min-h-screen max-w-[1600px] overflow-hidden">
      <div class="pointer-events-none absolute -top-28 right-0 h-80 w-80 rounded-full bg-cyan-500/20 blur-3xl"></div>
      <div class="pointer-events-none absolute bottom-0 left-0 h-72 w-72 rounded-full bg-indigo-500/20 blur-3xl"></div>
      <!-- Sidebar -->
      <aside class="hidden xl:flex w-80 flex-col border-r border-white/10 bg-slate-900/80 backdrop-blur-xl shadow-2xl shadow-black/30">
        <div class="p-6 border-b border-white/10 bg-slate-900/60">
          <div class="text-xs uppercase tracking-[0.4em] text-cyan-300/80 font-semibold">{{ APP_CONFIG.appName }}</div>
          <h1 class="mt-3 text-3xl font-black leading-tight text-white">Silver<br />Control</h1>
          <p class="mt-3 text-sm text-slate-300 font-medium">Gestión completa de tu gimnasio.</p>
        </div>

        <!-- Sesión activa -->
        <div class="p-6 border-b border-white/10">
          <div class="rounded-smoother border border-white/10 bg-white/5 p-4 shadow-lg shadow-black/10">
            <p class="text-xs uppercase tracking-widest text-cyan-300/80 font-semibold">Sesión activa</p>
            <div class="mt-3 flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-smooth bg-gradient-to-br from-cyan-400 to-indigo-500 text-lg font-bold text-white shadow-lg shadow-cyan-500/20">
                {{ userInitials }}
              </div>
              <div>
                <p class="font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="text-sm text-slate-400">{{ user?.email || 'Sin correo' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Navegación -->
        <nav class="flex-1 p-4">
          <p class="px-3 text-xs uppercase tracking-widest text-slate-400 font-semibold">Navegación</p>
          <div class="mt-4 space-y-2">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-3 rounded-smooth border border-transparent px-4 py-3 transition"
              :class="isActive(link.to)
                ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-lg shadow-cyan-500/20'
                : 'text-slate-300 hover:bg-white/5 hover:text-white hover:border-white/10'"
            >
              <span class="text-lg">{{ link.icon }}</span>
              <span class="font-medium">{{ link.label }}</span>
            </router-link>
          </div>
        </nav>

        <!-- Logout -->
        <div class="p-6 border-t border-white/10 bg-gradient-to-t from-white/5 to-transparent">
          <button
            class="w-full rounded-smooth bg-gradient-to-r from-cyan-500 to-indigo-500 py-3 font-semibold text-white shadow-lg shadow-cyan-500/20 transition hover:opacity-95"
            @click="handleLogout"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>

      <!-- Contenido principal -->
      <div class="flex min-w-0 flex-1 flex-col">
        <!-- Header móvil -->
        <header class="sticky top-0 z-20 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl xl:hidden shadow-sm">
          <div class="flex items-center justify-between p-4">
            <div>
              <p class="text-xs uppercase tracking-widest text-cyan-300/80 font-semibold">{{ APP_CONFIG.appName }}</p>
              <h1 class="text-xl font-bold text-white">{{ currentSectionTitle }}</h1>
            </div>
            <button class="rounded-smooth border border-white/10 bg-white/5 px-4 py-2 text-sm font-bold text-white hover:bg-white/10 transition" @click="handleLogout">
              Salir
            </button>
          </div>
          <div class="overflow-x-auto px-4 pb-4">
            <div class="flex gap-2 min-w-max">
              <router-link
                v-for="link in navigationLinks"
                :key="link.to"
                :to="link.to"
                class="rounded-smooth px-4 py-2 text-sm font-medium transition"
                :class="isActive(link.to)
                  ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-white'
                  : 'bg-white/5 text-slate-300'"
              >
                {{ link.label }}
              </router-link>
            </div>
          </div>
        </header>

        <!-- Main content -->
        <main class="flex-1 p-4 sm:p-6 xl:p-8 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative">
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
      { label: 'Panel', to: '/admin/dashboard', icon: '●' },
      { label: 'Usuarios', to: '/admin/users', icon: '●' },
      { label: 'Asistencia', to: '/admin/attendance', icon: '●' },
      { label: 'Inventario', to: '/admin/inventory', icon: '●' },
      { label: 'Estadísticas', to: '/admin/statistics', icon: '●' },
    ];
  }

  return [
    { label: 'Panel', to: '/user/dashboard', icon: '●' },
    { label: 'Horarios', to: '/user/schedule', icon: '●' },
    { label: 'Mi asistencia', to: '/user/attendance', icon: '●' },
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
