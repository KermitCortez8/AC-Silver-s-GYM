<template>
  <div class="space-y-7">
    <template v-if="isAdmin">
      <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Dashboard</p>
            <h1 class="mt-2 text-3xl font-black text-white sm:text-4xl">Operacion general</h1>
            <p class="mt-2 text-slate-300">Resumen visual de clientes, horarios, matriculas, asistencia e inventario.</p>
          </div>
          <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white" @click="refreshDashboard">
            Actualizar datos
          </button>
        </div>
      </section>

      <section class="grid gap-4 md:grid-cols-2 2xl:grid-cols-5">
        <article v-for="item in adminCards" :key="item.label" class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <p class="text-sm text-slate-400">{{ item.label }}</p>
          <p class="mt-2 text-3xl font-black text-white">{{ item.value }}</p>
          <p class="mt-2 text-xs uppercase tracking-[0.18em]" :class="item.tone">{{ item.detail }}</p>
        </article>
      </section>

      <section class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <article class="dashboard-panel">
          <div class="panel-heading">
            <p>Clientes</p>
            <h2>Estado de membresias</h2>
          </div>
          <div class="chart-box">
            <Doughnut :data="membershipChartData" :options="doughnutOptions" />
          </div>
        </article>

        <article class="dashboard-panel">
          <div class="panel-heading">
            <p>Horarios</p>
            <h2>Cupos por servicio</h2>
          </div>
          <div class="chart-box">
            <Bar :data="serviceCapacityData" :options="barOptions" />
          </div>
        </article>
      </section>

      <section class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <article class="dashboard-panel">
          <div class="panel-heading">
            <p>Asistencia</p>
            <h2>Ultimos 7 dias</h2>
          </div>
          <div class="chart-box">
            <Line :data="attendanceTrendData" :options="lineOptions" />
          </div>
        </article>

        <article class="dashboard-panel">
          <div class="panel-heading">
            <p>Alertas</p>
            <h2>Operacion pendiente</h2>
          </div>
          <div class="mt-5 space-y-3">
            <div v-for="item in operationalAlerts" :key="item.label" class="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
              <div class="flex items-center justify-between gap-4">
                <div>
                  <p class="font-bold text-white">{{ item.label }}</p>
                  <p class="mt-1 text-sm text-slate-400">{{ item.detail }}</p>
                </div>
                <p class="text-2xl font-black" :class="item.color">{{ item.value }}</p>
              </div>
            </div>
          </div>
        </article>
      </section>
    </template>

    <template v-else>
      <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Inicio</p>
        <h1 class="mt-2 text-3xl font-black text-white sm:text-4xl">Hola, {{ user?.name || 'cliente' }}</h1>
        <p class="mt-2 text-slate-300">Aqui tienes tu estado de membresia y tu horario matriculado.</p>
      </section>

      <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article v-for="item in clientCards" :key="item.label" class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <p class="text-sm text-slate-400">{{ item.label }}</p>
          <p class="mt-2 text-2xl font-black text-white">{{ item.value }}</p>
          <p class="mt-2 text-xs uppercase tracking-[0.16em]" :class="item.tone">{{ item.detail }}</p>
        </article>
      </section>

      <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Mi horario</p>
            <h2 class="mt-2 text-2xl font-black text-white">Tabla semanal</h2>
          </div>
          <router-link to="/user/enrollment" class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-bold text-slate-950">
            Matricular horario
          </router-link>
        </div>

        <div class="mt-5">
          <ExcelScheduleGrid
            title="Horario"
            subtitle="Tu horario se actualiza automaticamente con cada matricula registrada."
            :items="clientScheduleItems"
            file-name="mi-horario.xlsx"
            empty-message="Tu horario esta vacio. Matriculate en un servicio para verlo aqui."
          />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ArcElement, BarElement, CategoryScale, Chart as ChartJS, Filler, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import { computed, onMounted } from 'vue';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import { attendanceBelongsToClient, buildClientIdentityFromUser, findClientForUser, resolveClientIdForUser, weekdayFromISO } from '../utils/clientIdentity';

ChartJS.register(ArcElement, BarElement, CategoryScale, Filler, Legend, LinearScale, LineElement, PointElement, Tooltip);

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();

const normalizeStatus = (value) => String(value || '').trim().toUpperCase();
const dateKey = (date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
const todayKey = () => dateKey(new Date());

const members = computed(() => gymStore.members || []);
const schedules = computed(() => gymStore.serviceSchedules || []);
const enrollments = computed(() => (gymStore.enrollments || []).filter((item) => item.estado !== 'CANCELADA'));
const attendance = computed(() => gymStore.attendance || []);
const inventory = computed(() => gymStore.inventory || []);

const currentClient = computed(() => {
  return findClientForUser(user.value, members.value);
});

const currentClientId = computed(() => Number(currentClient.value?.id_cliente || resolveClientIdForUser(user.value, members.value) || 0));
const currentClientIdentity = computed(() => currentClient.value || buildClientIdentityFromUser(user.value, members.value));

const clientEnrollments = computed(() => {
  const idCliente = currentClientId.value;
  if (!idCliente) return [];
  return enrollments.value.filter((item) => Number(item.id_cliente) === idCliente);
});

const attendanceFor = (item) =>
  attendance.value.find((entry) => {
    const byEnrollment = Number(entry.idMatricula || 0) === Number(item.id_matricula || 0) && Number(item.id_matricula || 0) > 0;
    const bySchedule = Number(entry.idHorarioServicio || 0) === Number(item.id_horario_servicio || 0) && Number(item.id_horario_servicio || 0) > 0;
    const byClientSchedule =
      attendanceBelongsToClient(entry, currentClientIdentity.value) &&
      String(entry.service || '').toLowerCase() === String(item.servicio || '').toLowerCase() &&
      weekdayFromISO(entry.date) === String(item.dia || '').toLowerCase();

    return byEnrollment || bySchedule || byClientSchedule;
  });

const clientScheduleItems = computed(() =>
  clientEnrollments.value.map((item) => {
    const saved = attendanceFor(item);
    return {
      ...item,
      cliente_nombre: saved ? 'OK Guardado' : 'Pendiente',
      checkLabel: saved
        ? `OK Entrada ${saved.entryTime || saved.time || '--:--'} / Salida ${saved.exitTime || 'pendiente'}`
        : 'Sin asistencia',
      entryTime: saved?.entryTime || '',
      exitTime: saved?.exitTime || '',
    };
  }),
);

const activeMembers = computed(() => members.value.filter((member) => normalizeStatus(member.membershipStatus || member.status).startsWith('ACT')).length);
const pendingMembers = computed(() => members.value.filter((member) => normalizeStatus(member.membershipStatus || member.status).includes('TRAMITE')).length);
const attendanceToday = computed(() => attendance.value.filter((entry) => String(entry.date || '').slice(0, 10) === todayKey()).length);
const usedSlots = computed(() => enrollments.value.length);
const totalSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos || 0), 0));

const adminCards = computed(() => [
  { label: 'Clientes', value: members.value.length, detail: `${activeMembers.value} activos`, tone: 'text-emerald-300' },
  { label: 'En tramite', value: pendingMembers.value, detail: 'pendientes de activar', tone: 'text-amber-300' },
  { label: 'Horarios', value: schedules.value.length, detail: `${schedules.value.filter((item) => item.activo !== false).length} activos`, tone: 'text-cyan-300' },
  { label: 'Matriculas', value: enrollments.value.length, detail: `${usedSlots.value}/${totalSlots.value || 0} cupos usados`, tone: 'text-sky-300' },
  { label: 'Asistencia hoy', value: attendanceToday.value, detail: 'registros del dia', tone: 'text-fuchsia-300' },
]);

const statusBuckets = computed(() => {
  const buckets = { Activos: 0, 'En tramite': 0, Inactivos: 0 };
  members.value.forEach((member) => {
    const status = normalizeStatus(member.membershipStatus || member.status);
    if (status.startsWith('ACT')) buckets.Activos += 1;
    else if (status.includes('TRAMITE')) buckets['En tramite'] += 1;
    else buckets.Inactivos += 1;
  });
  return buckets;
});

const membershipChartData = computed(() => ({
  labels: Object.keys(statusBuckets.value),
  datasets: [
    {
      data: Object.values(statusBuckets.value),
      backgroundColor: ['#34d399', '#fbbf24', '#64748b'],
      borderColor: '#0f172a',
      borderWidth: 2,
    },
  ],
}));

const services = ['fitness', 'musculacion', 'cardio', 'baile'];
const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service;

const serviceCapacityData = computed(() => ({
  labels: services.map(serviceLabel),
  datasets: [
    {
      label: 'Cupos usados',
      data: services.map((service) => schedules.value.filter((item) => item.servicio === service).reduce((sum, item) => sum + Number(item.cupos_usados || 0), 0)),
      backgroundColor: '#f97316',
      borderRadius: 8,
    },
    {
      label: 'Cupos libres',
      data: services.map((service) =>
        schedules.value
          .filter((item) => item.servicio === service)
          .reduce((sum, item) => sum + Math.max(0, Number(item.cupos || 0) - Number(item.cupos_usados || 0)), 0),
      ),
      backgroundColor: '#fde68a',
      borderRadius: 8,
    },
  ],
}));

const lastSevenDays = computed(() =>
  Array.from({ length: 7 }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - index));
    return dateKey(date);
  }),
);

const attendanceTrendData = computed(() => ({
  labels: lastSevenDays.value.map((day) => day.slice(5)),
  datasets: [
    {
      label: 'Asistencias',
      data: lastSevenDays.value.map((day) => attendance.value.filter((entry) => String(entry.date || '').slice(0, 10) === day).length),
      borderColor: '#f97316',
      backgroundColor: 'rgba(249, 115, 22, 0.18)',
      pointBackgroundColor: '#fbbf24',
      tension: 0.35,
      fill: true,
    },
  ],
}));

const chartTextColor = '#cbd5e1';
const gridColor = 'rgba(148, 163, 184, 0.18)';

const baseScale = {
  ticks: { color: chartTextColor },
  grid: { color: gridColor },
};

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: chartTextColor, boxWidth: 12 } },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: { stacked: true, ...baseScale },
    y: { stacked: true, beginAtZero: true, ...baseScale },
  },
};

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: chartTextColor, boxWidth: 12 } },
  },
  scales: {
    x: baseScale,
    y: { beginAtZero: true, ...baseScale },
  },
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom', labels: { color: chartTextColor, boxWidth: 12 } },
  },
};

const operationalAlerts = computed(() => [
  { label: 'Membresias por activar', value: pendingMembers.value, detail: 'Clientes con estado en tramite.', color: 'text-amber-300' },
  { label: 'Stock bajo', value: inventory.value.filter((item) => Number(item.quantity || 0) <= Number(item.minQuantity || 0)).length, detail: 'Items por debajo del minimo.', color: 'text-rose-300' },
  { label: 'Cupos libres', value: Math.max(0, totalSlots.value - usedSlots.value), detail: 'Capacidad disponible para matricula.', color: 'text-emerald-300' },
]);

const clientAttendanceCount = computed(() => {
  const ids = new Set(clientEnrollments.value.map((item) => Number(item.id_matricula)));
  return attendance.value.filter((entry) => ids.has(Number(entry.idMatricula)) || attendanceBelongsToClient(entry, currentClientIdentity.value)).length;
});

const clientCards = computed(() => {
  const client = currentClient.value || currentClientIdentity.value || {};
  const status = normalizeStatus(client.membershipStatus || client.status || user.value?.membershipStatus || user.value?.estado || 'SIN DATOS');
  return [
    { label: 'Membresia', value: status, detail: client.membershipEnd ? `vence ${client.membershipEnd}` : 'vigencia pendiente', tone: status.startsWith('ACT') ? 'text-emerald-300' : 'text-amber-300' },
    { label: 'Plan', value: client.plan || user.value?.plan || 'Sin plan', detail: client.promocion || 'sin promocion', tone: 'text-cyan-300' },
    { label: 'Horarios', value: clientEnrollments.value.length, detail: 'matriculas activas', tone: 'text-sky-300' },
    { label: 'Asistencias', value: clientAttendanceCount.value, detail: 'checks guardados', tone: 'text-fuchsia-300' },
  ];
});

const refreshDashboard = async () => {
  await gymStore.fetchFromBackend?.().catch((error) => console.warn('No se pudo refrescar dashboard:', error));

  if (!isAdmin.value && currentClientId.value) {
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value }).catch(() => {});
    await gymStore.refreshAttendanceFromBackend?.().catch(() => {});
  }
};

onMounted(refreshDashboard);
</script>

<style scoped>
.dashboard-panel {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.05);
  padding: 1.5rem;
  backdrop-filter: blur(16px);
}

.panel-heading p {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.panel-heading h2 {
  margin-top: 0.5rem;
  color: white;
  font-size: 1.5rem;
  font-weight: 900;
}

.chart-box {
  position: relative;
  height: 320px;
  margin-top: 1.25rem;
}
</style>
