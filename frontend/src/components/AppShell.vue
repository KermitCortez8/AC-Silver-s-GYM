<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),_transparent_32%),linear-gradient(180deg,#020617_0%,#08101f_100%)] text-slate-50">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-24 right-[-4rem] h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl"></div>
      <div class="absolute top-48 left-[-5rem] h-96 w-96 rounded-full bg-emerald-400/10 blur-3xl"></div>
    </div>

    <div class="relative flex min-h-screen w-full">
      <aside class="hidden w-72 flex-col border-r border-white/10 bg-slate-950/70 backdrop-blur-xl 2xl:w-80 xl:flex">
        <div class="border-b border-white/10 p-6">
          <p class="text-xs uppercase tracking-[0.45em] text-cyan-300/80">{{ APP_CONFIG.appName }}</p>
          <h1 class="mt-3 text-3xl font-black leading-none text-white">Gym Operations</h1>
          <p class="mt-3 text-sm leading-6 text-slate-300">Un solo panel para accesos, clientes, inventario, rutinas y tickets.</p>
        </div>

        <div class="border-b border-white/10 p-6">
          <div class="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
            <p class="text-[0.65rem] uppercase tracking-[0.4em] text-slate-400">Sesión activa</p>
            <div class="mt-4 flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400/15 text-lg font-black text-cyan-100">
                {{ userInitials }}
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="truncate text-sm text-slate-300">{{ user?.email || 'Sin correo' }}</p>
                <p v-if="user?.id_usuario" class="truncate text-xs uppercase tracking-[0.3em] text-cyan-200/80">{{ user.id_usuario }}</p>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-2 text-xs text-slate-300">
              <span class="rounded-full bg-emerald-400/15 px-2.5 py-1 text-emerald-100">{{ isAdmin ? 'Administrador' : 'Usuario' }}</span>
              <span class="rounded-full bg-white/5 px-2.5 py-1">Token activo</span>
            </div>
          </div>
        </div>

        <nav class="flex-1 p-4">
          <p class="px-3 text-[0.65rem] uppercase tracking-[0.4em] text-slate-500">Navegación</p>
          <div class="mt-4 space-y-2">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition"
              :class="isActive(link.to)
                ? 'bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-400/20'
                : 'text-slate-200 hover:bg-white/8 hover:text-white'"
            >
              <span class="text-lg">{{ link.icon }}</span>
              <span>{{ link.label }}</span>
            </router-link>
          </div>
        </nav>

        <div class="border-t border-white/10 p-6">
          <button class="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10" @click="handleLogout">
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-white/10 bg-slate-950/70 backdrop-blur-xl xl:hidden">
          <div class="flex items-center justify-between gap-4 p-4">
            <div>
              <p class="text-[0.65rem] uppercase tracking-[0.4em] text-cyan-300/80">{{ APP_CONFIG.appName }}</p>
              <h1 class="text-xl font-black text-white">{{ currentSectionTitle }}</h1>
            </div>
            <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white" @click="handleLogout">Salir</button>
          </div>
          <div class="overflow-x-auto px-4 pb-4">
            <div class="flex min-w-max gap-2">
              <router-link
                v-for="link in navigationLinks"
                :key="link.to"
                :to="link.to"
                class="rounded-full px-4 py-2 text-sm font-medium transition"
                :class="isActive(link.to) ? 'bg-cyan-400 text-slate-950' : 'bg-white/5 text-slate-200'"
              >
                {{ link.label }}
              </router-link>
            </div>
          </div>
        </header>

        <main class="flex-1 px-4 py-5 sm:px-6 lg:px-8 xl:px-10 2xl:px-12">
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
      { label: 'Inicio', to: '/admin/dashboard', icon: '▣' },
      { label: 'Clientes', to: '/admin/clients', icon: '◫' },
      { label: 'Usuarios', to: '/admin/users', icon: '◫' },
      { label: 'Horarios', to: '/admin/service-schedules', icon: '▣' },
      { label: 'Matricula', to: '/admin/enrollment', icon: '◫' },
      { label: 'Asistencia', to: '/admin/attendance', icon: '◌' },
      { label: 'Inventario', to: '/admin/inventory', icon: '▤' },
      { label: 'Tienda', to: '/admin/store', icon: '▥' },
    ];
  }

  return [
    { label: 'Inicio', to: '/user/dashboard', icon: '▣' },
    { label: 'Tienda', to: '/user/store', icon: '▥' },
    { label: 'Horarios', to: '/user/schedule', icon: '◫' },
    { label: 'Matricula', to: '/user/enrollment', icon: '▣' },
    { label: 'Mi asistencia', to: '/user/attendance', icon: '◌' },
  ];
});

const currentSectionTitle = computed(() => navigationLinks.value.find((link) => route.path.startsWith(link.to))?.label || 'Panel');

const userInitials = computed(() => {
  const name = user.value?.name || 'AC';
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
