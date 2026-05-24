<template>
  <div v-if="isAdmin" class="space-y-8">
    <section class="space-y-6">
      <div class="rounded-smoother border border-white/10 bg-slate-900/80 p-8 shadow-2xl shadow-black/20">
        <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80 font-semibold">Panel de administración</p>
        <h1 class="mt-3 text-4xl font-black text-white sm:text-5xl">Bienvenido, {{ user?.name || 'Administrador' }}</h1>
        <p class="mt-4 max-w-3xl text-slate-300 font-medium">
          Gestiona el gimnasio con métricas en vivo, asistencias y estadísticas detalladas.
        </p>

        <div class="mt-8 grid gap-4 sm:grid-cols-4">
          <div class="rounded-smooth border border-cyan-400/20 bg-white/5 backdrop-blur p-5 shadow-md hover:shadow-lg transition">
            <p class="text-xs uppercase tracking-widest text-cyan-300/80 font-semibold">Miembros</p>
            <p class="mt-2 text-4xl font-bold text-white">{{ stats.totalMembers }}</p>
            <p class="mt-1 text-xs text-slate-400">Total registrados</p>
          </div>
          <div class="rounded-smooth border border-indigo-400/20 bg-white/5 backdrop-blur p-5 shadow-md hover:shadow-lg transition">
            <p class="text-xs uppercase tracking-widest text-indigo-300/80 font-semibold">Hoy</p>
            <p class="mt-2 text-4xl font-bold text-white">{{ stats.attendanceToday }}</p>
            <p class="mt-1 text-xs text-slate-400">Ingresos hoy</p>
          </div>
          <div class="rounded-smooth border border-emerald-400/20 bg-white/5 backdrop-blur p-5 shadow-md hover:shadow-lg transition">
            <p class="text-xs uppercase tracking-widest text-emerald-300/80 font-semibold">Activos</p>
            <p class="mt-2 text-4xl font-bold text-white">{{ stats.activeMembers }}</p>
            <p class="mt-1 text-xs text-slate-400">Este mes</p>
          </div>
          <div class="rounded-smooth border border-amber-400/20 bg-white/5 backdrop-blur p-5 shadow-md hover:shadow-lg transition">
            <p class="text-xs uppercase tracking-widest text-amber-300/80 font-semibold">Inventario</p>
            <p class="mt-2 text-4xl font-bold text-white">{{ stats.inventoryItems }}</p>
            <p class="mt-1 text-xs text-slate-400">Productos</p>
          </div>
        </div>
      </div>

      <StatisticsCharts />
    </section>

    <section class="space-y-6">
      <div class="flex gap-3 border-b border-white/10 pb-0">
        <button
          v-for="tab in adminTabs"
          :key="tab"
          @click="activeAdminTab = tab"
          :class="[
            'px-5 py-3 font-semibold transition border-b-2 text-base',
            activeAdminTab === tab
              ? 'border-cyan-400 text-white'
              : 'border-transparent text-slate-400 hover:text-white',
          ]"
        >
          {{ tab }}
        </button>
      </div>

      <div class="rounded-smoother border border-white/10 bg-slate-900/80 p-6 shadow-2xl shadow-black/20">
        <div v-if="activeAdminTab === 'Horarios'" class="text-slate-200">
          <ScheduleView />
        </div>
        <div v-else-if="activeAdminTab === 'Asistencias'" class="text-slate-200">
          <AttendanceView />
        </div>
      </div>
    </section>
  </div>

  <div v-else class="space-y-8">
    <!-- VISTA USUARIO/CLIENTE -->
    <!-- Encabezado con saludo personalizado -->
    <section class="space-y-6">
      <div class="rounded-smoother border border-white/10 bg-slate-900/80 p-8 shadow-2xl shadow-black/20">
        <h1 class="text-4xl font-black text-white sm:text-5xl">
          ¡Bienvenido{{ user?.name ? `, ${user.name.split(' ')[0]}` : '' }}!
        </h1>
        <p class="mt-4 text-slate-300 font-medium">
          Te alegra vernos. Aquí puedes ver tus horarios, asistencias y comprar en nuestra tienda.
        </p>
      </div>
    </section>

    <!-- Pestañas para usuarios -->
    <section class="space-y-6">
      <div class="flex gap-3 border-b border-white/10 overflow-x-auto pb-0">
        <button
          v-for="tab in userTabs"
          :key="tab"
          @click="activeUserTab = tab"
          :class="[
            'px-5 py-3 font-semibold transition whitespace-nowrap border-b-2 text-base',
            activeUserTab === tab
              ? 'border-cyan-400 text-white'
              : 'border-transparent text-slate-400 hover:text-white',
          ]"
        >
          {{ tab }}
        </button>
      </div>

      <!-- Contenido de las pestañas -->
      <div class="rounded-smoother border border-white/10 bg-slate-900/80 p-8 shadow-2xl shadow-black/20">
        <!-- Horarios -->
        <div v-if="activeUserTab === 'Horarios'" class="space-y-6">
          <h2 class="text-3xl font-bold text-white">Mis Horarios</h2>
          <div class="grid gap-5 md:grid-cols-2">
            <div
              v-for="schedule in userSchedules"
              :key="schedule.id"
              class="rounded-smooth border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition"
            >
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="font-bold text-lg text-white">{{ schedule.class }}</h3>
                  <p class="text-sm text-cyan-300 font-semibold">{{ schedule.instructor }}</p>
                </div>
              </div>
              <div class="mt-4 space-y-2 text-sm text-slate-300">
                <p><strong class="text-cyan-300">Hora:</strong> {{ schedule.time }}</p>
                <p><strong class="text-cyan-300">Lugar:</strong> {{ schedule.location }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Asistencias -->
        <div v-else-if="activeUserTab === 'Asistencias'" class="space-y-6">
          <h2 class="text-3xl font-bold text-white">Mi Calendario de Asistencias</h2>
          <AttendanceCalendar />
        </div>

        <!-- Tienda -->
        <div v-else-if="activeUserTab === 'Tienda'" class="space-y-6">
          <h2 class="text-3xl font-bold text-white">Tienda</h2>
          <Store />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import StatCard from '../components/StatCard.vue';
import AttendanceCalendar from '../components/AttendanceCalendar.vue';
import Store from '../components/Store.vue';
import StatisticsCharts from '../components/StatisticsCharts.vue';
import ScheduleView from './ScheduleView.vue';
import AttendanceView from './AttendanceView.vue';

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();

const stats = computed(() => gymStore.stats);
const recentAttendance = computed(() => gymStore.recentAttendance.slice(0, 5));
const lowStockInventory = computed(() => gymStore.lowStockInventory);

const activeAdminTab = ref('Horarios');
const activeUserTab = ref('Horarios');

const adminTabs = ['Horarios', 'Asistencias'];
const userTabs = ['Horarios', 'Asistencias', 'Tienda'];

// Horarios de ejemplo para usuarios
const userSchedules = ref([
  {
    id: 1,
    class: 'CrossFit',
    instructor: 'Carlos',
    time: 'Lunes y Miércoles 6:00 AM',
    location: 'Zona A',
  },
  {
    id: 2,
    class: 'Yoga',
    instructor: 'María',
    time: 'Martes y Jueves 7:00 PM',
    location: 'Zona B',
  },
  {
    id: 3,
    class: 'Spinning',
    instructor: 'Juan',
    time: 'Lunes, Miércoles y Viernes 5:30 PM',
    location: 'Zona C',
  },
]);
</script>

