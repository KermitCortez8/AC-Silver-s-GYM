import { useDashboardCharts } from './useDashboardCharts.js';
import { computed, onMounted, ref } from 'vue';
import { useVisibleRefresh } from '../useVisibleRefresh.js';
import { CalendarDays, ClipboardCheck, Package, ShoppingBag, UsersRound } from 'lucide-vue-next';
import { summarizeDashboardClients, peruDateKey } from '../../../domain/utils/clientDashboard.js';
import { useAuth } from '../../../application/composables/useAuth';
import { useTheme } from '../useTheme';
import { useGymStore } from '../../../application/stores/gymStore';
import { attendanceBelongsToClient, buildClientIdentityFromUser, findClientForUser, resolveClientIdForUser, weekdayFromISO } from '../../../domain/utils/clientIdentity';

/** Coordina los datos y las acciones del panel administrativo y personal. */
export const useDashboardOverview = () => {
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
  const storeProducts = computed(() => gymStore.productos_tienda || []);

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

  const {
    membershipChartData, paymentChartData, services, serviceLabel, readableStatus,
    serviceUsedColors, serviceFreeColors, serviceCapacityData, lastSevenDays, attendanceTrendData,
    chartTextColor, gridColor, baseScale, barOptions, lineOptions,
    doughnutOptions,
  } = useDashboardCharts({ membershipSegments, clientSummary, schedules, attendance, isDarkTheme });

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
      to: { path: '/admin/store', query: { stock: 'bajo' } },
      value: storeProducts.value.filter(
        (product) => Number(product.cantidad || 0) <= Number(product.minimo || 0),
      ).length,
      detail: 'Productos de Tienda en el mínimo o por debajo.',
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

  onMounted(() => { if (isAdmin.value) refreshDashboard(); });
  useVisibleRefresh(() => refreshDashboard(true), { canRefresh: () => !isAdmin.value });

  return {
    user, isAdmin, userRole, isDarkTheme,
    gymStore, isRefreshing, refreshError, lastUpdated, quickActions,
    normalizeStatus, todayKey, members, schedules, enrollments,
    attendance, storeProducts, currentClient, currentClientId, currentClientIdentity,
    clientEnrollments, attendanceFor, clientScheduleItems, clientSummary, activeMembers,
    pendingMembers, usedSlots, totalSlots, adminCards, membershipSegments,
    membershipChartData, paymentChartData, services, serviceLabel, readableStatus,
    serviceUsedColors, serviceFreeColors, serviceCapacityData, lastSevenDays, attendanceTrendData,
    chartTextColor, gridColor, baseScale, barOptions, lineOptions,
    doughnutOptions, operationalAlerts, clientAttendanceCount, clientCards, refreshDashboard,
  };
};
