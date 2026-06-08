<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.30),_transparent_34%),radial-gradient(circle_at_top_right,_rgba(249,115,22,0.22),_transparent_30%),linear-gradient(180deg,#fff7ed_0%,#ffedd5_44%,#fef3c7_100%)] text-slate-50">
    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div class="absolute -top-24 right-[-4rem] h-80 w-80 rounded-full bg-orange-400/25 blur-3xl"></div>
      <div class="absolute top-48 left-[-5rem] h-96 w-96 rounded-full bg-yellow-300/20 blur-3xl"></div>
    </div>

    <div class="relative flex min-h-screen w-full">
      <aside class="hidden w-72 flex-col border-r border-orange-200/20 bg-[#241307]/90 backdrop-blur-xl 2xl:w-80 xl:flex">
        <div class="border-b border-orange-200/20 p-6">
          <p class="text-xs uppercase tracking-[0.45em] text-amber-200">{{ APP_CONFIG.appName }}</p>
          <h1 class="mt-3 text-3xl font-black leading-none text-white">Plataforma digital</h1>
          <p class="mt-3 text-sm leading-6 text-orange-100/80">Gestion central para clientes, horarios, asistencia y ventas.</p>
        </div>

        <div class="border-b border-orange-200/20 p-6">
          <div class="rounded-2xl border border-orange-200/20 bg-white/10 p-4">
            <p class="text-xs uppercase tracking-[0.35em] text-orange-100/70">Sesion activa</p>
            <div class="mt-4 flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-300 text-lg font-black text-orange-950">
                {{ userInitials }}
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-white">{{ user?.name || 'Invitado' }}</p>
                <p class="truncate text-sm text-orange-100/80">{{ user?.email || 'Sin correo' }}</p>
                <p v-if="user?.id_usuario" class="truncate text-xs uppercase tracking-[0.3em] text-amber-200">{{ user.id_usuario }}</p>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-2 text-xs text-orange-100/80">
              <span class="rounded-full bg-amber-300/20 px-2.5 py-1 text-amber-100">{{ isAdmin ? 'Administrador' : 'Usuario' }}</span>
              <span class="rounded-full bg-white/10 px-2.5 py-1">Acceso activo</span>
            </div>
          </div>
        </div>

        <nav class="flex-1 p-4">
          <p class="px-3 text-xs uppercase tracking-[0.35em] text-orange-100/50">Navegacion</p>
          <div class="mt-4 space-y-2">
            <router-link
              v-for="link in navigationLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition"
              :class="isActive(link.to)
                ? 'bg-amber-300 text-orange-950 shadow-lg shadow-amber-500/20'
                : 'text-orange-50 hover:bg-white/10 hover:text-white'"
            >
              <span class="text-lg">{{ link.icon }}</span>
              <span>{{ link.label }}</span>
            </router-link>
          </div>
        </nav>

        <div class="border-t border-orange-200/20 p-6">
          <button class="w-full rounded-2xl border border-orange-200/20 bg-white/10 px-4 py-3 font-semibold text-white transition hover:bg-white/15" @click="handleLogout">
            Cerrar sesion
          </button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-orange-200/20 bg-[#241307]/90 backdrop-blur-xl xl:hidden">
          <div class="flex items-center justify-between gap-4 p-4">
            <div>
              <p class="text-xs uppercase tracking-[0.35em] text-amber-200">{{ APP_CONFIG.appName }}</p>
              <h1 class="text-xl font-black text-white">{{ currentSectionTitle }}</h1>
            </div>
            <button class="rounded-full border border-orange-200/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white" @click="handleLogout">Salir</button>
          </div>
          <div class="overflow-x-auto px-4 pb-4">
            <div class="flex min-w-max gap-2">
              <router-link
                v-for="link in navigationLinks"
                :key="link.to"
                :to="link.to"
                class="rounded-full px-4 py-2 text-sm font-medium transition"
                :class="isActive(link.to) ? 'bg-amber-300 text-orange-950' : 'bg-white/10 text-orange-50'"
              >
                {{ link.label }}
              </router-link>
            </div>
          </div>
        </header>

        <main class="flex-1 bg-[#2a1609]/90 px-4 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur-sm sm:px-6 lg:px-8 xl:px-10 2xl:px-12">
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
