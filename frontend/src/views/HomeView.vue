<template>
  <div class="workspace-view space-y-6">
    <header class="ws-panel ws-hero ws-toolbar">
      <div>
        <p class="ws-eyebrow">
          {{ isAdmin ? 'Administración · Resumen' : 'Mi gimnasio' }}
        </p>
        <h1 class="ws-title">
          {{
            isAdmin
              ? 'Todo listo para un gran día'
              : `Hola, ${user?.name || 'cliente'}`
          }}
        </h1>
        <p class="ws-description">
          {{
            isAdmin
              ? 'Revisa la actividad del gimnasio y organiza las tareas de tu equipo.'
              : 'Tu membresía, tus clases y tu progreso, en un solo lugar.'
          }}
        </p>
      </div>
      <div class="flex flex-col items-start gap-2">
        <button
          class="ws-btn"
          :disabled="isRefreshing"
          @click="refreshDashboard(true)"
        >
          <RefreshCw :size="16" :class="{ 'ws-spin': isRefreshing }" />{{
            isRefreshing ? 'Actualizando…' : 'Actualizar datos'
          }}
        </button>
        <p v-if="lastUpdated" class="ws-muted text-xs" role="status">
          Actualizado a las {{ lastUpdated }}
        </p>
      </div>
    </header>
    <p
      v-if="refreshError"
      role="alert"
      class="ws-notice ws-tint-danger ws-danger"
    >
      {{ refreshError }}
    </p>

    <nav class="grid gap-3 md:grid-cols-3" aria-label="Accesos rápidos">
      <RouterLink
        v-for="action in quickActions"
        :key="action.to"
        :to="action.to"
        class="ws-action-link"
        ><component :is="action.icon" :size="22" /><span
          ><strong class="text-sm">{{ action.label }}</strong
          ><small>{{ action.detail }}</small></span
        ><ChevronRight :size="18"
      /></RouterLink>
    </nav>

    <section
      class="dashboard-metrics"
      :class="
        isAdmin ? 'dashboard-metrics--admin' : 'dashboard-metrics--client'
      "
      aria-label="Resumen de actividad"
      :aria-busy="isRefreshing"
    >
      <article
        v-for="item in isAdmin ? adminCards : clientCards"
        :key="item.label"
        class="ws-metric"
      >
        <p class="ws-muted text-sm">{{ item.label }}</p>
        <p class="ws-metric-value">{{ item.value }}</p>
        <p class="text-xs font-medium" :class="item.tone">{{ item.detail }}</p>
      </article>
    </section>

    <template v-if="isAdmin">
      <section class="grid gap-5 xl:grid-cols-2">
        <article class="ws-panel">
          <div class="ws-toolbar">
            <div>
              <p class="ws-eyebrow">Clientes</p>
              <h2 class="ws-heading mt-1">Estado de membresías</h2>
            </div>
            <RouterLink to="/admin/clients" class="ws-btn"
              >Ver clientes <ArrowUpRight :size="16"
            /></RouterLink>
          </div>
          <div v-if="members.length" class="chart-box">
            <Doughnut
              :data="membershipChartData"
              :options="doughnutOptions"
              aria-label="Distribución de clientes por estado de membresía"
            />
          </div>
          <div v-else class="ws-empty mt-5">
            <UsersRound :size="30" />
            <h3>Aún no hay clientes</h3>
            <p>
              El resumen aparecerá cuando registres a tus primeros clientes.
            </p>
          </div>
          <nav
            v-if="members.length"
            class="mt-4 grid gap-2 sm:grid-cols-3"
            aria-label="Filtrar clientes por membresía"
          >
            <RouterLink
              v-for="segment in membershipSegments"
              :key="segment.key"
              :to="{ path: '/admin/clients', query: { status: segment.key } }"
              class="membership-segment ws-hover"
            >
              <span class="flex items-center gap-2"
                ><span
                  class="h-2 w-2 rounded-full"
                  :style="{ backgroundColor: segment.color }"
                ></span
                >{{ segment.label }}</span
              >
              <strong>{{ segment.count }}</strong>
            </RouterLink>
          </nav>
        </article>
        <article class="ws-panel">
          <div class="ws-toolbar">
            <div>
              <p class="ws-eyebrow">Cobros de membresías</p>
              <h2 class="ws-heading mt-1">Pagos por origen del cliente</h2>
            </div>
            <RouterLink
              :to="{ path: '/admin/clients', query: { payment: 'PENDIENTE' } }"
              class="ws-btn"
              >Revisar pagos <ArrowUpRight :size="16"
            /></RouterLink>
          </div>
          <div v-if="members.length" class="chart-box">
            <Bar
              :data="paymentChartData"
              :options="barOptions"
              aria-label="Clientes con pago confirmado, pendiente o sin información según su origen"
            />
          </div>
          <div v-else class="ws-empty mt-5">
            <UsersRound :size="30" />
            <h3>Pagos de tus clientes</h3>
            <p>Los cobros aparecerán aquí cuando registres clientes.</p>
          </div>
          <p class="ws-muted text-sm mt-4">
            {{ clientSummary.pendingPayment }} pendientes de pago ·
            {{ clientSummary.readyToActivate }} con pago confirmado por activar.
          </p>
          <p class="ws-muted text-xs mt-2">
            Un pago confirmado requiere activación para habilitar la membresía.
            Se muestra el último pago de cada cliente.
          </p>
        </article>
      </section>
      <section class="grid gap-5 xl:grid-cols-2">
        <article class="ws-panel">
          <div class="ws-toolbar">
            <div>
              <p class="ws-eyebrow">Horarios</p>
              <h2 class="ws-heading mt-1">Cupos por servicio</h2>
            </div>
            <RouterLink to="/admin/service-schedules" class="ws-btn"
              >Ver horarios <ArrowUpRight :size="16"
            /></RouterLink>
          </div>
          <div v-if="schedules.length" class="chart-box">
            <Bar
              :data="serviceCapacityData"
              :options="barOptions"
              aria-label="Cupos ocupados y disponibles por servicio"
            />
          </div>
          <div v-else class="ws-empty mt-5">
            <CalendarDays :size="30" />
            <h3>Organiza tus clases</h3>
            <p>Los horarios registrados aparecerán en este resumen.</p>
          </div>
        </article>
        <article class="ws-panel">
          <p class="ws-eyebrow">Asistencia</p>
          <h2 class="ws-heading mt-1">Últimos 7 días</h2>
          <div class="chart-box">
            <Line
              :data="attendanceTrendData"
              :options="lineOptions"
              aria-label="Asistencias registradas en los últimos siete días"
            />
          </div>
        </article>
      </section>
      <section>
        <article class="ws-panel">
          <p class="ws-eyebrow">Organiza tu día</p>
          <h2 class="ws-heading mt-1">Por revisar</h2>
          <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <RouterLink
              v-for="item in operationalAlerts"
              :key="item.label"
              :to="item.to"
              class="ws-action-link"
              ><div class="flex-1">
                <p class="font-bold text-sm">{{ item.label }}</p>
                <p class="ws-muted text-xs mt-1">{{ item.detail }}</p>
              </div>
              <span class="text-2xl font-black" :class="item.color">{{
                item.value
              }}</span
              ><ChevronRight :size="16"
            /></RouterLink>
          </div>
        </article>
      </section>
    </template>
    <section v-else class="ws-panel">
      <div class="ws-toolbar">
        <div>
          <p class="ws-eyebrow">Mi semana</p>
          <h2 class="ws-heading mt-1">Tu próximo entrenamiento empieza aquí</h2>
          <p class="ws-muted text-sm mt-2">
            Consulta tus clases y organiza el tiempo para ti.
          </p>
        </div>
        <RouterLink to="/user/schedule" class="ws-btn ws-primary"
          ><CalendarDays :size="17" />{{
            clientEnrollments.length
              ? 'Gestionar mis horarios'
              : 'Elegir un horario'
          }}</RouterLink
        >
      </div>
      <div class="mt-5">
        <ExcelScheduleGrid
          title="Mi horario"
          subtitle="Tus clases se actualizan con cada matrícula registrada."
          :items="clientScheduleItems"
          file-name="mi-horario.xlsx"
          empty-message="Todavía no tienes clases. Elige un horario para empezar a entrenar."
        />
      </div>
    </section>
  </div>
</template>
<script setup>
import { clientMembershipLabel } from '../utils/clientDirectory.js';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import { computed, defineAsyncComponent, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import {
  ArrowUpRight,
  CalendarDays,
  ChevronRight,
  ClipboardCheck,
  Package,
  RefreshCw,
  ShoppingBag,
  UsersRound,
} from 'lucide-vue-next';
import {
  summarizeDashboardClients,
  peruDateKey,
  lastSevenPeruDays,
} from '../utils/clientDashboard.js';
import { useAuth } from '../composables/useAuth';
import { useTheme } from '../composables/useTheme';
import { useGymStore } from '../stores/gymStore';
import {
  attendanceBelongsToClient,
  buildClientIdentityFromUser,
  findClientForUser,
  resolveClientIdForUser,
  weekdayFromISO,
} from '../utils/clientIdentity';

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
);

const ExcelScheduleGrid = defineAsyncComponent(
  () => import('../components/ExcelScheduleGrid.vue'),
);
const { user, isAdmin, userRole } = useAuth();
const { isDarkTheme } = useTheme();
const gymStore = useGymStore();
const isRefreshing = ref(false);
const refreshError = ref('');
const lastUpdated = ref('');
const quickActions = computed(() =>
  isAdmin.value
    ? [
        userRole.value === 'admin'
          ? {
              to: '/admin/attendance',
              label: 'Registrar asistencia',
              detail: 'Entradas y salidas del gimnasio',
              icon: ClipboardCheck,
            }
          : {
              to: '/admin/enrollment',
              label: 'Gestionar matrículas',
              detail: 'Inscripciones a horarios',
              icon: CalendarDays,
            },
        {
          to: '/admin/clients',
          label: 'Gestionar clientes',
          detail: 'Membresías y activaciones',
          icon: UsersRound,
        },
        {
          to: '/admin/inventory/movements',
          label: 'Movimientos de stock',
          detail: 'Entradas, salidas y ajustes',
          icon: Package,
        },
      ]
    : [
        {
          to: '/user/schedule',
          label: 'Mis horarios',
          detail: 'Encuentra tu próxima clase',
          icon: CalendarDays,
        },
        {
          to: '/user/attendance',
          label: 'Mi asistencia',
          detail: 'Consulta tus visitas al gimnasio',
          icon: ClipboardCheck,
        },
        {
          to: '/user/store',
          label: 'Explorar la tienda',
          detail: 'Todo para tu entrenamiento',
          icon: ShoppingBag,
        },
      ],
);

/**
 * Normaliza el valor recibido.
 */
const normalizeStatus = (value) =>
  String(value || '')
    .trim()
    .toUpperCase();
/**
 * Gestiona esta acción de la vista.
 */
const todayKey = () => peruDateKey();

const members = computed(() => gymStore.members || []);
const schedules = computed(() => gymStore.serviceSchedules || []);
const enrollments = computed(() =>
  (gymStore.enrollments || []).filter((item) => item.estado !== 'CANCELADA'),
);
const attendance = computed(() => gymStore.attendance || []);
const inventory = computed(() => gymStore.inventory || []);

const currentClient = computed(() => {
  return findClientForUser(user.value, members.value);
});

const currentClientId = computed(() =>
  Number(
    currentClient.value?.id_cliente ||
      resolveClientIdForUser(user.value, members.value) ||
      0,
  ),
);
const currentClientIdentity = computed(
  () =>
    currentClient.value ||
    buildClientIdentityFromUser(user.value, members.value),
);

const clientEnrollments = computed(() => {
  const idCliente = currentClientId.value;
  if (!idCliente) return [];
  return enrollments.value.filter(
    (item) => Number(item.id_cliente) === idCliente,
  );
});

/**
 * Gestiona esta acción de la vista.
 */
const attendanceFor = (item) =>
  attendance.value.find((entry) => {
    const byEnrollment =
      Number(entry.idMatricula || 0) === Number(item.id_matricula || 0) &&
      Number(item.id_matricula || 0) > 0;
    const bySchedule =
      Number(entry.idHorarioServicio || 0) ===
        Number(item.id_horario_servicio || 0) &&
      Number(item.id_horario_servicio || 0) > 0;
    const byClientSchedule =
      attendanceBelongsToClient(entry, currentClientIdentity.value) &&
      String(entry.service || '').toLowerCase() ===
        String(item.servicio || '').toLowerCase() &&
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

const clientSummary = computed(() => summarizeDashboardClients(members.value));
const activeMembers = computed(() => clientSummary.value.memberships.active);
const pendingMembers = computed(() => clientSummary.value.readyToActivate);
const usedSlots = computed(() => enrollments.value.length);
const totalSlots = computed(() =>
  schedules.value.reduce((sum, item) => sum + Number(item.cupos || 0), 0),
);

const adminCards = computed(() => [
  {
    label: 'Clientes registrados',
    value: members.value.length,
    detail: `${activeMembers.value} con membresía activa`,
    tone: 'ws-success',
  },
  {
    label: 'En trámite',
    value: clientSummary.value.memberships.pending,
    detail: `${pendingMembers.value} con pago confirmado por activar`,
    tone: 'ws-warning',
  },
  {
    label: 'Vencidas',
    value: clientSummary.value.memberships.expired,
    detail: 'membresías con acceso bloqueado',
    tone: 'ws-danger',
  },
]);

const membershipSegments = computed(() => [
  {
    key: 'active',
    label: 'Activo',
    count: clientSummary.value.memberships.active,
    color: '#22c55e',
  },
  {
    key: 'pending',
    label: 'En trámite',
    count: clientSummary.value.memberships.pending,
    color: '#fbbf24',
  },
  {
    key: 'expired',
    label: 'Vencida',
    count: clientSummary.value.memberships.expired,
    color: '#f43f5e',
  },
]);

const membershipChartData = computed(() => ({
  labels: membershipSegments.value.map((item) => item.label),
  datasets: [
    {
      data: membershipSegments.value.map((item) => item.count),
      backgroundColor: membershipSegments.value.map((item) => item.color),
      borderColor: isDarkTheme.value ? '#171717' : '#f5f5f5',
      borderWidth: 2,
    },
  ],
}));

const paymentChartData = computed(() => ({
  labels: clientSummary.value.origins.map((origin) => origin.label),
  datasets: [
    { label: 'Pagado', key: 'paid', backgroundColor: '#22c55e' },
    { label: 'Pendiente', key: 'pending', backgroundColor: '#fbbf24' },
    { label: 'Sin información', key: 'unknown', backgroundColor: '#94a3b8' },
  ].map(({ key, ...dataset }) => ({
    ...dataset,
    data: clientSummary.value.origins.map((origin) => origin[key]),
    borderRadius: 6,
  })),
}));

const services = ['fitness', 'musculacion', 'cardio', 'baile'];
/**
 * Gestiona esta acción de la vista.
 */
const serviceLabel = (service) =>
  ({
    fitness: 'Fitness',
    musculacion: 'Musculacion',
    cardio: 'Cardio',
    baile: 'Baile',
  })[service] || service;
/**
 * Obtiene los datos necesarios.
 */
const readableStatus = (status) =>
  clientMembershipLabel({ membershipStatus: status });
const serviceUsedColors = ['#84cc16', '#38bdf8', '#f59e0b', '#fb7185'];
const serviceFreeColors = ['#d9f99d', '#bfdbfe', '#fde68a', '#fecdd3'];

const serviceCapacityData = computed(() => ({
  labels: services.map(serviceLabel),
  datasets: [
    {
      label: 'Cupos usados',
      data: services.map((service) =>
        schedules.value
          .filter((item) => item.servicio === service)
          .reduce((sum, item) => sum + Number(item.cupos_usados || 0), 0),
      ),
      backgroundColor: serviceUsedColors,
      borderColor: serviceUsedColors,
      borderWidth: 1,
      borderRadius: 8,
    },
    {
      label: 'Cupos libres',
      to: '/admin/service-schedules',
      data: services.map((service) =>
        schedules.value
          .filter((item) => item.servicio === service)
          .reduce(
            (sum, item) =>
              sum +
              Math.max(
                0,
                Number(item.cupos || 0) - Number(item.cupos_usados || 0),
              ),
            0,
          ),
      ),
      backgroundColor: serviceFreeColors,
      borderColor: serviceUsedColors,
      borderWidth: 1,
      borderRadius: 8,
    },
  ],
}));

const lastSevenDays = computed(() => lastSevenPeruDays());

const attendanceTrendData = computed(() => ({
  labels: lastSevenDays.value.map((day) => day.slice(5)),
  datasets: [
    {
      label: 'Asistencias',
      data: lastSevenDays.value.map(
        (day) =>
          attendance.value.filter(
            (entry) => String(entry.date || '').slice(0, 10) === day,
          ).length,
      ),
      borderColor: '#0ea5e9',
      backgroundColor: 'rgba(14, 165, 233, 0.18)',
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#0284c7',
      tension: 0.35,
      fill: true,
    },
  ],
}));

const chartTextColor = computed(() =>
  isDarkTheme.value ? '#d4d4d4' : '#404040',
);
const gridColor = computed(() =>
  isDarkTheme.value ? 'rgba(163, 163, 163, 0.18)' : 'rgba(64, 64, 64, 0.16)',
);
const baseScale = computed(() => ({
  ticks: { color: chartTextColor.value },
  grid: { color: gridColor.value },
}));

const barOptions = computed(() => ({
  animation: false,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: chartTextColor.value, boxWidth: 12 } },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: { stacked: true, ...baseScale.value },
    y: {
      stacked: true,
      beginAtZero: true,
      ...baseScale.value,
      ticks: { color: chartTextColor.value, precision: 0 },
    },
  },
}));

const lineOptions = computed(() => ({
  animation: false,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: chartTextColor.value, boxWidth: 12 } },
  },
  scales: {
    x: baseScale.value,
    y: {
      beginAtZero: true,
      ...baseScale.value,
      ticks: { color: chartTextColor.value, precision: 0 },
    },
  },
}));

const doughnutOptions = computed(() => ({
  animation: false,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { color: chartTextColor.value, boxWidth: 12 },
    },
  },
}));

const operationalAlerts = computed(() => [
  {
    label: 'Membresías por activar',
    to: {
      path: '/admin/clients',
      query: { status: 'pending', payment: 'PAGADO' },
    },
    value: pendingMembers.value,
    detail: 'Pago confirmado, activación pendiente.',
    color: 'ws-warning',
  },
  {
    label: 'Pagos pendientes',
    to: { path: '/admin/clients', query: { payment: 'PENDIENTE' } },
    value: clientSummary.value.pendingPayment,
    detail: 'Clientes con pago por confirmar.',
    color: 'ws-warning',
  },
  {
    label: 'Membresías vencidas',
    to: { path: '/admin/clients', query: { status: 'expired' } },
    value: clientSummary.value.memberships.expired,
    detail: 'Requieren renovación para recuperar el acceso.',
    color: 'ws-danger',
  },
  {
    label: 'Stock bajo',
    to: '/admin/inventory',
    value: inventory.value.filter(
      (item) => Number(item.quantity || 0) <= Number(item.minQuantity || 0),
    ).length,
    detail: 'Artículos en el mínimo o por debajo.',
    color: 'ws-danger',
  },
  {
    label: 'Cupos libres',
    to: '/admin/service-schedules',
    value: Math.max(0, totalSlots.value - usedSlots.value),
    detail: 'Disponibilidad para nuevas matrículas.',
    color: 'ws-success',
  },
]);

const clientAttendanceCount = computed(() => {
  const ids = new Set(
    clientEnrollments.value.map((item) => Number(item.id_matricula)),
  );
  return attendance.value.filter(
    (entry) =>
      ids.has(Number(entry.idMatricula)) ||
      attendanceBelongsToClient(entry, currentClientIdentity.value),
  ).length;
});

const clientCards = computed(() => {
  const client = currentClient.value || currentClientIdentity.value || {};
  const status = normalizeStatus(
    client.membershipStatus ||
      client.status ||
      user.value?.membershipStatus ||
      user.value?.estado ||
      'SIN DATOS',
  );
  const displayStatus = readableStatus(status);
  return [
    {
      label: 'Membresía',
      value: displayStatus,
      detail: client.membershipEnd
        ? `vence ${client.membershipEnd}`
        : 'vigencia pendiente',
      tone: status.startsWith('ACT')
        ? 'ws-success'
        : status.startsWith('VENC')
          ? 'ws-danger'
          : 'ws-warning',
    },
    {
      label: 'Plan',
      value: client.plan || user.value?.plan || 'Sin plan',
      detail: client.promocion || 'sin promoción',
      tone: 'ws-info',
    },
    {
      label: 'Horarios',
      value: clientEnrollments.value.length,
      detail: 'matrículas activas',
      tone: 'ws-info',
    },
    {
      label: 'Asistencias',
      value: clientAttendanceCount.value,
      detail: 'visitas registradas',
      tone: 'ws-info',
    },
  ];
});

/**
 * Actualiza los datos actuales.
 */
const refreshDashboard = async (force = false) => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  refreshError.value = '';
  try {
    await gymStore.fetchFromBackend?.({ section: 'dashboard', force });
    lastUpdated.value = new Intl.DateTimeFormat('es-PE', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Lima',
    }).format(new Date());
  } catch {
    refreshError.value =
      'No se pudieron actualizar los datos. Vuelve a intentarlo con «Actualizar datos».';
  } finally {
    isRefreshing.value = false;
  }
};

onMounted(() => refreshDashboard());
</script>

<style scoped>
.dashboard-metrics {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr);
}
@media (min-width: 768px) {
  .dashboard-metrics--admin {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (min-width: 1280px) {
  .dashboard-metrics--client {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.chart-box {
  position: relative;
  height: 280px;
  margin-top: 1.5rem;
}
.membership-segment {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 0.8rem;
  border: 1px solid var(--ws-border);
  border-radius: 0.8rem;
  font-size: 0.8rem;
}
@media (max-width: 480px) {
  .chart-box {
    height: 230px;
  }
}
</style>
