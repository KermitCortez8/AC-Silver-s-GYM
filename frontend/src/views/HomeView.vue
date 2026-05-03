<template>
  <div class="space-y-8">
    <section class="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-7 shadow-2xl shadow-black/10 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Panel principal</p>
        <h1 class="mt-3 text-4xl font-black text-white sm:text-5xl">Bienvenido, {{ user?.name || 'usuario' }}</h1>
        <p class="mt-4 max-w-3xl text-slate-300">
          Aquí ves el resumen del gimnasio con métricas en vivo, accesos rápidos y módulos reales de administración.
        </p>

        <div class="mt-6 grid gap-4 sm:grid-cols-3">
          <StatCard label="Miembros" :value="stats.totalMembers" description="Usuarios registrados en la plataforma" icon="👥" />
          <StatCard label="Asistencia hoy" :value="stats.attendanceToday" description="Ingresos registrados en la fecha actual" icon="✓" />
          <StatCard label="Inventario" :value="stats.inventoryItems" description="Productos y equipos registrados" icon="📦" />
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-slate-900/80 p-7 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Resumen rápido</p>
        <div class="mt-5 space-y-4">
          <div class="rounded-2xl bg-white/5 p-4">
            <p class="text-sm text-slate-400">Miembros activos</p>
            <p class="mt-1 text-3xl font-black text-white">{{ stats.activeMembers }}</p>
          </div>
          <div class="rounded-2xl bg-white/5 p-4">
            <p class="text-sm text-slate-400">Asistencia promedio</p>
            <p class="mt-1 text-3xl font-black text-white">{{ stats.attendanceRate }}%</p>
          </div>
          <div class="rounded-2xl bg-white/5 p-4">
            <p class="text-sm text-slate-400">Stock bajo</p>
            <p class="mt-1 text-3xl font-black text-white">{{ stats.lowStockItems }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-7 backdrop-blur">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Accesos rápidos</p>
            <h2 class="mt-2 text-2xl font-black text-white">Módulos principales</h2>
          </div>
        </div>

        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <router-link
            v-for="item in quickLinks"
            :key="item.to"
            :to="item.to"
            class="group rounded-3xl border border-white/10 bg-slate-900/80 p-5 transition hover:-translate-y-1 hover:border-cyan-400/40 hover:bg-slate-900"
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
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-7 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Actividad reciente</p>
        <div class="mt-6 space-y-4">
          <div
            v-for="entry in recentAttendance"
            :key="entry.id"
            class="rounded-2xl border border-white/10 bg-slate-900/80 p-4"
          >
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

        <div v-if="lowStockInventory.length" class="mt-6 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
          <p class="font-semibold">Hay {{ lowStockInventory.length }} artículos con stock bajo.</p>
          <p class="mt-1 text-sm">Revisa inventario para evitar quiebres de stock.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import StatCard from '../components/StatCard.vue';

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();

const stats = computed(() => gymStore.stats);
const recentAttendance = computed(() => gymStore.recentAttendance.slice(0, 5));
const lowStockInventory = computed(() => gymStore.lowStockInventory);

const quickLinks = computed(() => {
  if (isAdmin.value) {
    return [
      { label: 'Usuarios', description: 'Alta, edición y baja de miembros', to: '/admin/users', icon: '👥' },
      { label: 'Asistencia', description: 'Registrar entradas y salidas', to: '/admin/attendance', icon: '✓' },
      { label: 'Inventario', description: 'Control de equipos y productos', to: '/admin/inventory', icon: '📦' },
      { label: 'Horarios', description: 'Consulta de clases y franjas', to: '/user/schedule', icon: '🕐' },
    ];
  }

  return [
    { label: 'Horarios', description: 'Ver la programación semanal', to: '/user/schedule', icon: '🕐' },
    { label: 'Mi asistencia', description: 'Revisar tus registros recientes', to: '/user/attendance', icon: '✓' },
    { label: 'Estado de membresía', description: 'Ver plan y vigencia actual', to: '/user/dashboard', icon: '💳' },
  ];
});
</script>
