<template>
  <div class="space-y-8">
    <section class="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-7 shadow-2xl shadow-black/10 backdrop-blur">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-300/80">Panel principal</p>
        <h1 class="mt-3 text-4xl font-black text-white sm:text-5xl">Bienvenido, {{ user?.name || 'usuario' }}</h1>
        <p class="mt-4 max-w-3xl text-slate-300">
          El dashboard refleja métricas del backend, alertas operativas y accesos rápidos hacia cada flujo de trabajo.
        </p>

        <div class="mt-6 grid gap-4 sm:grid-cols-3">
          <div class="rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
            <p class="text-sm text-slate-400">Clientes</p>
            <p class="mt-2 text-3xl font-black text-white">{{ stats.totalMembers }}</p>
          </div>
          <div class="rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
            <p class="text-sm text-slate-400">Asistencia hoy</p>
            <p class="mt-2 text-3xl font-black text-white">{{ stats.attendanceToday }}</p>
          </div>
          <div class="rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
            <p class="text-sm text-slate-400">Inventario</p>
            <p class="mt-2 text-3xl font-black text-white">{{ stats.inventoryItems }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-slate-950/70 p-7 backdrop-blur">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Resumen rápido</p>
        <div class="mt-5 space-y-4">
          <div class="rounded-2xl bg-white/5 p-4">
            <p class="text-sm text-slate-400">Clientes activos</p>
            <p class="mt-1 text-3xl font-black text-white">{{ stats.activeMembers }}</p>
          </div>
          <div class="rounded-2xl bg-white/5 p-4">
            <p class="text-sm text-slate-400">Tasa de asistencia</p>
            <p class="mt-1 text-3xl font-black text-white">{{ stats.attendanceRate }}%</p>
          </div>

        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-7 backdrop-blur">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Accesos rápidos</p>
            <h2 class="mt-2 text-2xl font-black text-white">Flujos principales</h2>
          </div>
        </div>

        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <router-link
            v-for="item in quickLinks"
            :key="item.to"
            :to="item.to"
            class="group rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-5 transition hover:-translate-y-1 hover:border-cyan-400/40 hover:bg-slate-950"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-2xl">{{ item.icon }}</p>
                <h3 class="mt-3 text-lg font-bold text-white">{{ item.label }}</h3>
                <p class="mt-2 text-sm text-slate-400">{{ item.description }}</p>
              </div>
              <span class="text-slate-500 transition group-hover:text-cyan-300">→</span>
            </div>
          </router-link>
        </div>

        <div class="mt-6 rounded-[1.75rem] border border-white/10 bg-slate-950/50 p-5">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Cobertura del backend</p>
          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <article v-for="item in moduleCoverage" :key="item.title" class="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p class="font-bold text-white">{{ item.title }}</p>
              <p class="mt-1 text-sm text-slate-400">{{ item.summary }}</p>
              <p class="mt-2 text-sm text-cyan-200">{{ item.status }}</p>
            </article>
          </div>
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-7 backdrop-blur">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Actividad reciente</p>
        <div class="mt-6 space-y-4">
          <div v-for="entry in recentAttendance" :key="entry.id" class="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="font-semibold text-white">{{ entry.memberName }}</p>
                <p class="text-sm text-slate-400">{{ entry.note || entry.type }}</p>
              </div>
              <div class="text-right text-sm text-slate-300">
                <p>{{ entry.type }}</p>
                <p>{{ entry.date }} · {{ entry.time }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="membershipAlerts.length || activePromotions.length" class="mt-4 space-y-3">
          <div v-if="membershipAlerts.length" class="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
            <p class="font-semibold">Membresías por vencer: {{ membershipAlerts.length }}</p>
            <p class="mt-1 text-sm">Hay clientes que necesitan renovación pronto.</p>
          </div>
          <div v-if="activePromotions.length" class="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-cyan-50">
            <p class="font-semibold">Promociones activas: {{ activePromotions.length }}</p>
            <p class="mt-1 text-sm">Se muestran si el backend o la sesión tiene campañas cargadas.</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();

const stats = computed(() => gymStore.stats);
const recentAttendance = computed(() => gymStore.recentAttendance.slice(0, 5));
const lowStockInventory = computed(() => gymStore.lowStockInventory);
const membershipAlerts = computed(() => gymStore.membershipAlerts);
const activePromotions = computed(() => gymStore.activePromotions);

const moduleCoverage = computed(() => [
  {
    title: 'Clientes',
    summary: 'Expedientes, datos de contacto y membresía fija.',
    status: 'Conectado a /clientes',
  },
  {
    title: 'Usuarios',
    summary: 'Cuentas internas con rol, acceso y credenciales.',
    status: 'Conectado a /usuarios',
  },
  {
    title: 'Membresías',
    summary: 'Planificación, alta, renovación y rango de vigencia por cliente.',
    status: 'Conectado a /membresias',
  },
  {
    title: 'Asistencia',
    summary: 'Check-in por DNI o por código QR local con persistencia del backend.',
    status: 'Conectado a /asistencia',
  },
  {
    title: 'Operación',
    summary: 'Inventario, movimientos, tickets de atención, rutinas y horarios.',
    status: 'Conectado a /inventario y /gym/*',
  },
]);

const quickLinks = computed(() => {
  if (isAdmin.value) {
    return [
      { label: 'Clientes', description: 'Gestiona expedientes y membresías', to: '/admin/clients', icon: '◫' },
      { label: 'Usuarios', description: 'Gestiona cuentas internas y roles', to: '/admin/users', icon: '◫' },
      { label: 'Asistencia', description: 'Valida ingresos por DNI o QR', to: '/admin/attendance', icon: '◌' },
      { label: 'Inventario', description: 'Control de stock y movimientos', to: '/admin/inventory', icon: '▤' },
      { label: 'Horarios', description: 'Rutinas y asignaciones por socio', to: '/user/schedule', icon: '▣' },
    ];
  }

  return [
    { label: 'Horarios', description: 'Consulta la programación semanal', to: '/user/schedule', icon: '▣' },
    { label: 'Mi asistencia', description: 'Genera y usa tu pase QR', to: '/user/attendance', icon: '◌' },
    { label: 'Mi estado', description: 'Verifica tu plan y vigencia', to: '/user/dashboard', icon: '◫' },
  ];
});
</script>
