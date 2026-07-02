<template>
  <div class="app-shell min-h-screen text-slate-50">
    <div class="relative flex min-h-screen w-full">
      <aside class="app-sidebar hidden w-64 flex-col border-r backdrop-blur-xl lg:flex 2xl:w-72">
        <div class="border-b border-red-500/20 p-5 2xl:p-6">
          <p class="text-xs uppercase tracking-[0.38em] text-red-400">{{ APP_CONFIG.appName }}</p>
          <h1 class="mt-3 text-2xl font-black leading-none text-white 2xl:text-3xl">Plataforma digital</h1>
          <p class="mt-3 text-sm leading-6 text-slate-300">Gestion central para clientes, horarios, asistencia y ventas.</p>
        </div>

        <div class="border-b border-red-500/20 p-5 2xl:p-6">
          <div class="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
            <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Sesion activa</p>
            <div class="mt-4 flex min-w-0 items-center gap-3">
              <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-red-600 text-lg font-black text-white shadow-lg shadow-red-950/40">
                {{ userInitials }}
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="truncate text-sm text-slate-300">{{ user?.email || 'Sin correo' }}</p>
                <p v-if="user?.id_usuario" class="truncate text-xs uppercase tracking-[0.25em] text-red-400">{{ user.id_usuario }}</p>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-300">
              <span class="rounded-full bg-red-500/15 px-2.5 py-1 text-red-200">{{ roleLabel }}</span>
              <span class="rounded-full bg-white/10 px-2.5 py-1">Acceso activo</span>
            </div>
          </div>
        </div>

        <nav class="min-h-0 flex-1 overflow-y-auto p-4">
          <p class="px-3 text-xs uppercase tracking-[0.3em] text-slate-500">Navegacion</p>
          <div class="mt-4 space-y-2">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex min-w-0 items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition"
              :class="isActive(link.to)
                ? 'bg-red-600 text-white shadow-lg shadow-red-950/40'
                : 'text-slate-300 hover:bg-white/10 hover:text-white'"
            >
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/10 text-xs font-black">{{ link.icon }}</span>
              <span class="truncate">{{ link.label }}</span>
            </router-link>
          </div>
        </nav>

        <div class="space-y-3 border-t border-red-500/20 p-5 2xl:p-6">
          <button
            type="button"
            class="theme-switch w-full"
            :aria-label="isDarkTheme ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'"
            :aria-pressed="isDarkTheme"
            @click="toggleTheme"
          >
            <span>
              <span class="block text-left text-xs uppercase tracking-[0.2em] text-slate-400">Apariencia</span>
              <span class="mt-1 block text-left font-semibold">{{ isDarkTheme ? 'Tema oscuro' : 'Tema claro' }}</span>
            </span>
            <span class="theme-switch-track" aria-hidden="true">
              <span class="theme-switch-thumb"></span>
            </span>
          </button>
          <button class="w-full rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 font-semibold text-white transition hover:border-red-500/40 hover:bg-red-500/10" @click="handleLogout">
            Cerrar sesion
          </button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="app-mobile-header sticky top-0 z-20 border-b backdrop-blur-xl lg:hidden">
          <div class="flex items-center justify-between gap-4 px-4 py-3 sm:px-5">
            <div class="min-w-0">
              <p class="text-xs uppercase tracking-[0.32em] text-red-400">{{ APP_CONFIG.appName }}</p>
              <h1 class="truncate text-xl font-black text-white">{{ currentSectionTitle }}</h1>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <div class="hidden min-w-0 text-right sm:block">
                <p class="truncate text-sm font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="truncate text-xs text-slate-400">{{ user?.id_usuario || user?.email || 'Sesion activa' }}</p>
              </div>
              <button
                type="button"
                class="theme-compact-button"
                :aria-label="isDarkTheme ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'"
                @click="toggleTheme"
              >
                {{ isDarkTheme ? 'Claro' : 'Oscuro' }}
              </button>
              <button class="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm font-semibold text-white" @click="handleLogout">Salir</button>
            </div>
          </div>
        </header>

        <main class="app-main flex-1 px-3 py-4 pb-24 backdrop-blur-sm sm:px-5 sm:py-5 lg:px-6 lg:pb-8 xl:px-8 2xl:px-10">
          <div class="mx-auto w-full max-w-[1800px]">
            <slot />
          </div>
        </main>

        <nav class="app-mobile-nav fixed inset-x-0 bottom-0 z-30 border-t px-2 py-2 backdrop-blur-xl lg:hidden">
          <div class="mx-auto grid max-w-2xl auto-cols-fr grid-flow-col gap-1 overflow-x-auto">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex min-w-20 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-center text-[0.68rem] font-bold transition"
              :class="isActive(link.to) ? 'bg-red-600 text-white' : 'text-slate-300 hover:bg-white/10'"
            >
              <span class="text-xs">{{ link.icon }}</span>
              <span class="leading-tight">{{ shortLabel(link.label) }}</span>
            </router-link>
          </div>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { useTheme } from '../composables/useTheme';
import { APP_CONFIG } from '../config/appConfig';

const props = defineProps({
  mode: {
    type: String,
    default: 'user',
  },
});

const route = useRoute();
const router = useRouter();
const { user, signOut, isAdmin, isTrainer } = useAuth();
const { isDarkTheme, toggleTheme } = useTheme();

const navigationLinks = computed(() => {
  if (props.mode === 'trainer' || isTrainer.value) {
    return [
      { label: 'Supervision', to: '/trainer/dashboard', icon: 'SU' },
      { label: 'Rutinas', to: '/trainer/routines', icon: 'RU' },
      { label: 'Monitoreo', to: '/trainer/routine-monitor', icon: 'MO' },
    ];
  }

  if (props.mode === 'admin' || isAdmin.value) {
    return [
      { label: 'Inicio', to: '/admin/dashboard', icon: 'IN' },
      { label: 'Clientes', to: '/admin/clients', icon: 'CL' },
      { label: 'Usuarios', to: '/admin/users', icon: 'US' },
      { label: 'Horarios', to: '/admin/service-schedules', icon: 'HO' },
      { label: 'Matricula', to: '/admin/enrollment', icon: 'MA' },
      { label: 'Asistencia', to: '/admin/attendance', icon: 'AS' },
      { label: 'Inventario', to: '/admin/inventory', icon: 'IV' },
      { label: 'Tienda', to: '/admin/store', icon: 'TI' },
      { label: 'Pedidos', to: '/admin/orders', icon: 'PE' },
    ];
  }

  return [
    { label: 'Inicio', to: '/user/dashboard', icon: 'IN' },
    { label: 'Tienda', to: '/user/store', icon: 'TI' },
    { label: 'Horarios', to: '/user/schedule', icon: 'HO' },
    { label: 'Matricula', to: '/user/enrollment', icon: 'MA' },
    { label: 'Mi asistencia', to: '/user/attendance', icon: 'AS' },
  ];
});

const currentSectionTitle = computed(() => navigationLinks.value.find((link) => route.path.startsWith(link.to))?.label || 'Panel');
const roleLabel = computed(() => {
  if (isAdmin.value) return 'Administrador';
  if (isTrainer.value) return 'Trainer';
  return 'Usuario';
});

const userInitials = computed(() => {
  const name = user.value?.name || 'AC';
  return name
    .split(' ')
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
});

const isActive = (path) => route.path.startsWith(path);

const shortLabel = (label) =>
  ({
    'Mi asistencia': 'Asistencia',
    Inventario: 'Invent.',
    Matricula: 'Matric.',
  })[label] || label;

const handleLogout = async () => {
  await signOut();
  router.push('/login');
};
</script>
