<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#fff7ed_0%,#ffedd5_42%,#fef3c7_100%)] text-slate-50">
    <div class="relative flex min-h-screen w-full">
      <aside class="hidden w-64 flex-col border-r border-orange-200/20 bg-[#241307]/95 backdrop-blur-xl lg:flex 2xl:w-72">
        <div class="border-b border-orange-200/20 p-5 2xl:p-6">
          <p class="text-xs uppercase tracking-[0.38em] text-amber-200">{{ APP_CONFIG.appName }}</p>
          <h1 class="mt-3 text-2xl font-black leading-none text-white 2xl:text-3xl">Plataforma digital</h1>
          <p class="mt-3 text-sm leading-6 text-orange-100/80">Gestion central para clientes, horarios, asistencia y ventas.</p>
        </div>

        <div class="border-b border-orange-200/20 p-5 2xl:p-6">
          <div class="rounded-2xl border border-orange-200/20 bg-white/10 p-4">
            <p class="text-xs uppercase tracking-[0.3em] text-orange-100/70">Sesion activa</p>
            <div class="mt-4 flex min-w-0 items-center gap-3">
              <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-amber-300 text-lg font-black text-orange-950">
                {{ userInitials }}
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="truncate text-sm text-orange-100/80">{{ user?.email || 'Sin correo' }}</p>
                <p v-if="user?.id_usuario" class="truncate text-xs uppercase tracking-[0.25em] text-amber-200">{{ user.id_usuario }}</p>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-orange-100/80">
              <span class="rounded-full bg-amber-300/20 px-2.5 py-1 text-amber-100">{{ isAdmin ? 'Administrador' : 'Usuario' }}</span>
              <span class="rounded-full bg-white/10 px-2.5 py-1">Acceso activo</span>
            </div>
          </div>
        </div>

        <nav class="min-h-0 flex-1 overflow-y-auto p-4">
          <p class="px-3 text-xs uppercase tracking-[0.3em] text-orange-100/50">Navegacion</p>
          <div class="mt-4 space-y-2">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex min-w-0 items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition"
              :class="isActive(link.to)
                ? 'bg-amber-300 text-orange-950 shadow-lg shadow-amber-500/20'
                : 'text-orange-50 hover:bg-white/10 hover:text-white'"
            >
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/10 text-xs font-black">{{ link.icon }}</span>
              <span class="truncate">{{ link.label }}</span>
            </router-link>
          </div>
        </nav>

        <div class="border-t border-orange-200/20 p-5 2xl:p-6">
          <button class="w-full rounded-2xl border border-orange-200/20 bg-white/10 px-4 py-3 font-semibold text-white transition hover:bg-white/15" @click="handleLogout">
            Cerrar sesion
          </button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-orange-200/20 bg-[#241307]/95 backdrop-blur-xl lg:hidden">
          <div class="flex items-center justify-between gap-4 px-4 py-3 sm:px-5">
            <div class="min-w-0">
              <p class="text-xs uppercase tracking-[0.32em] text-amber-200">{{ APP_CONFIG.appName }}</p>
              <h1 class="truncate text-xl font-black text-white">{{ currentSectionTitle }}</h1>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <div class="hidden min-w-0 text-right sm:block">
                <p class="truncate text-sm font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="truncate text-xs text-orange-100/70">{{ user?.id_usuario || user?.email || 'Sesion activa' }}</p>
              </div>
              <button class="rounded-xl border border-orange-200/20 bg-white/10 px-3 py-2 text-sm font-semibold text-white" @click="handleLogout">Salir</button>
            </div>
          </div>
        </header>

        <main class="flex-1 bg-[#2a1609]/92 px-3 py-4 pb-24 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur-sm sm:px-5 sm:py-5 lg:px-6 lg:pb-8 xl:px-8 2xl:px-10">
          <div class="mx-auto w-full max-w-[1800px]">
            <slot />
          </div>
        </main>

        <nav class="fixed inset-x-0 bottom-0 z-30 border-t border-orange-200/20 bg-[#241307]/95 px-2 py-2 backdrop-blur-xl lg:hidden">
          <div class="mx-auto grid max-w-2xl auto-cols-fr grid-flow-col gap-1 overflow-x-auto">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex min-w-20 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-center text-[0.68rem] font-bold transition"
              :class="isActive(link.to) ? 'bg-amber-300 text-orange-950' : 'text-orange-50 hover:bg-white/10'"
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
