import { computed } from 'vue';
import { ArcElement, BarElement, CategoryScale, Chart as ChartJS, Filler, Legend, LinearScale, LineElement, PointElement, Tooltip } from 'chart.js';
import { clientMembershipLabel } from '../../../domain/utils/clientDirectory.js';
import { lastSevenPeruDays } from '../../../domain/utils/clientDashboard.js';

/** Datos y opciones de los gráficos del panel, reactivos al tema y al catálogo. */
export const useDashboardCharts = ({ membershipSegments, clientSummary, schedules, attendance, isDarkTheme }) => {
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
      musculacion: 'Musculación',
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

  return {
    membershipChartData, paymentChartData, services, serviceLabel, readableStatus,
    serviceUsedColors, serviceFreeColors, serviceCapacityData, lastSevenDays, attendanceTrendData,
    chartTextColor, gridColor, baseScale, barOptions, lineOptions,
    doughnutOptions,
  };
};
