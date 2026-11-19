<template>
  <div class="attendance-page user-attendance">
    <header class="att-page-header">
      <div class="user-attendance-heading">
        <span class="user-attendance-icon" aria-hidden="true"><CalendarCheck :size="25" /></span>
        <h1>Mi asistencia</h1>
      </div>
      <router-link class="att-button" to="/user/schedule">
        <CalendarDays :size="16" aria-hidden="true" /> Ver mis horarios
      </router-link>
    </header>

    <div class="att-tabs user-attendance-nav" role="group" aria-label="Vistas de mi asistencia">
      <button type="button" :aria-pressed="!showHistory" aria-controls="attendance-week"
        @click="showHistory = false">
        <CalendarDays :size="16" aria-hidden="true" /> Calendario
      </button>
      <button type="button" :aria-pressed="showHistory" aria-controls="attendance-history"
        @click="openHistory">
        <History :size="16" aria-hidden="true" /> Historial
      </button>
    </div>

    <div v-show="!showHistory" id="attendance-week" :aria-busy="loading">
      <ExcelScheduleGrid
        v-model:date="selectedDate"
        :items="calendarItems"
        title="Calendario de asistencia"
        subtitle="Consulta el estado y las horas de tus visitas."
        :empty-title="visitType ? 'Sin actividad de este tipo' : 'Sin actividad en esta semana'"
        :empty-message="visitType ? 'Cambia el filtro o elige otra semana.' : 'Elige otra semana para consultar tus registros.'"
        fixed-dates
        :show-export="false"
        @range-change="visibleRange = $event"
      >
        <template #filters>
          <div class="user-visit-filters" role="group" aria-label="Tipo de asistencia">
            <button v-for="filter in visitTypes" :key="filter.value" type="button"
              :aria-pressed="visitType === filter.value" @click="visitType = filter.value">
              <component :is="filter.icon" :size="15" aria-hidden="true" /> {{ filter.label }}
            </button>
          </div>
        </template>
        <template #summary>
          <strong v-if="week && !loading">{{ visibleVisits }} {{ visibleVisits === 1 ? 'visita registrada' : 'visitas registradas' }}</strong>
        </template>
        <template v-if="loading || error" #feedback>
          <p v-if="error" class="att-message is-error week-feedback" role="alert">
            {{ error }}
            <button type="button" class="att-link" @click="load">Reintentar</button>
          </p>
          <div v-else class="att-empty week-feedback" role="status">Cargando tu asistencia…</div>
        </template>
      </ExcelScheduleGrid>
    </div>

    <div v-show="showHistory" id="attendance-history">
      <AttendanceHistory v-if="historyOpened && token" :key="token" />
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { CalendarCheck, CalendarDays, Dumbbell, History, Layers } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { useAuth } from '../../application/composables/useAuth';
import { useAttendance } from '../../application/services/attendance.js';
import { calendarDate, weekStart } from '../../domain/utils/scheduleCalendar.js';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { dateLabel, shortTime } from '../utils/attendance.js';
import '../styles/attendance.css';

const AttendanceHistory = defineAsyncComponent(() => import('../components/attendance/AttendanceHistory.vue'));

const { token } = useAuth();
const { attendanceGet } = useAttendance();
const route = useRoute();
const selectedDate = ref(calendarDate(route.query.fecha));
const selectedWeek = computed(() => weekStart(selectedDate.value));
const visibleRange = ref(null);
const showHistory = ref(false);
const historyOpened = ref(false);
const visitType = ref('');
const visitTypes = [
  { value: '', label: 'Todas', icon: Layers },
  { value: 'horario', label: 'Por horario', icon: CalendarDays },
  { value: 'general', label: 'Gimnasio general', icon: Dumbbell },
];
const week = ref(null);
const loading = ref(Boolean(token.value));
const error = ref('');
let requestId = 0;

const openHistory = () => {
  historyOpened.value = true;
  showHistory.value = true;
};

const visitStates = {
  completada: { statusLabel: 'Completada', statusTone: 'is-visit-completed' },
  dentro: { statusLabel: 'En curso', statusTone: 'is-visit-inside' },
  incompleta: { statusLabel: 'Incompleta', statusTone: 'is-visit-incomplete' },
};
const visitStatus = (visit, date) => visitStates[visit?.estado] || {
  statusLabel: date > week.value.hoy ? 'Programado' : 'Sin registro',
  statusTone: 'is-visit-neutral',
};

const checkLabel = (visit) => {
  if (!visit) return '';
  const entry = shortTime(visit.hora_entrada || visit.hora);
  if (!visit.hora_salida) return `Entrada ${entry} · Salida pendiente`;
  const exitDate = visit.fecha_salida && visit.fecha_salida !== visit.fecha
    ? ` (${dateLabel(visit.fecha_salida, { year: undefined })})` : '';
  const label = visit.cierre_automatico ? 'Cierre automático' : 'Salida';
  return `Entrada ${entry} · ${label} ${shortTime(visit.hora_salida)}${exitDate}`;
};

const classItem = (item) => ({
  calendarId: `clase-${item.id_matricula}`,
  type: 'horario',
  fecha: item.fecha,
  servicio: item.servicio,
  rutina_nombre: item.rutina_nombre || item.nombre_rutina,
  hora_inicio: item.hora_inicio,
  hora_fin: item.hora_fin,
  recorded: Boolean(item.asistencia),
  ...visitStatus(item.asistencia, item.fecha),
  checkLabel: checkLabel(item.asistencia),
});

const generalItem = (visit) => {
  const entry = visit.hora_entrada || visit.hora;
  const [hour, minute] = shortTime(entry).split(':').map(Number);
  // La cuadrícula necesita altura para una entrada sin salida; la hora real del fin queda vacía.
  const visualEnd = Math.min(24 * 60, hour * 60 + minute + 30);
  const endTime = visit.fecha_salida > visit.fecha
    ? '24:00'
    : visit.hora_salida && shortTime(visit.hora_salida) > shortTime(entry)
      ? visit.hora_salida
      : `${String(Math.floor(visualEnd / 60)).padStart(2, '0')}:${String(visualEnd % 60).padStart(2, '0')}`;
  return {
    calendarId: `general-${visit.id_asistencia}`,
    type: 'general',
    fecha: visit.fecha,
    servicio: 'gimnasio',
    rutina_nombre: 'Visita al gimnasio',
    hora_inicio: entry,
    hora_fin: visit.hora_salida,
    calendarEndTime: endTime,
    recorded: true,
    ...visitStatus(visit, visit.fecha),
    checkLabel: checkLabel(visit),
  };
};

const calendarItems = computed(() => {
  if (!week.value) return [];
  const classes = week.value.horarios.map(classItem);
  const visits = (week.value.generales || []).map(generalItem);
  return [...classes, ...visits].filter((item) => !visitType.value || item.type === visitType.value);
});
const visibleVisits = computed(() => {
  const range = visibleRange.value;
  return range ? calendarItems.value.filter((item) => item.recorded && item.fecha >= range.from && item.fecha <= range.to).length : 0;
});

const load = async () => {
  const id = ++requestId;
  const sessionToken = token.value;
  week.value = null;
  error.value = '';
  loading.value = Boolean(sessionToken);
  if (!sessionToken) return;

  try {
    const result = await attendanceGet('/mi-semana', { inicio: selectedWeek.value }, sessionToken);
    if (id === requestId) week.value = result;
  } catch (err) {
    if (id === requestId) error.value = err.message;
  } finally {
    if (id === requestId) loading.value = false;
  }
};

watch(() => route.query.fecha, (value) => { selectedDate.value = calendarDate(value); });
watch([token, selectedWeek], load);
onMounted(load);
onBeforeUnmount(() => { requestId++; });
</script>

<style scoped>
.user-attendance {
  gap: 18px;
}
.user-attendance-heading {
  display: flex;
  align-items: center;
  gap: 14px;
}
.user-attendance-heading h1 {
  margin: 0;
}
.user-attendance-icon {
  display: grid;
  width: 54px;
  height: 54px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 16px;
  background: var(--app-accent-soft);
  color: var(--app-accent-text);
}
.user-attendance-nav {
  justify-self: start;
}
.user-attendance-nav button,
.user-visit-filters button {
  min-height: 40px;
}
.user-attendance-nav button[aria-pressed='true'],
.user-visit-filters button[aria-pressed='true'] {
  background: var(--app-accent-soft);
  color: var(--app-accent-text);
  border-color: var(--app-accent);
}
.user-attendance-nav button:focus-visible,
.user-visit-filters button:focus-visible {
  outline: 2px solid var(--app-accent);
  outline-offset: 2px;
}
#attendance-week,
#attendance-history {
  min-width: 0;
}
.user-visit-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  padding: 0 24px 16px;
}
.user-visit-filters button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  color: var(--app-text-soft);
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
}
.user-visit-filters button:hover {
  color: var(--app-text);
  background: var(--app-surface-soft);
}
.week-feedback {
  margin: 0 24px 20px;
}
@media (max-width: 720px) {
  .user-attendance .att-page-header,
  .user-attendance-heading {
    gap: 8px;
  }
  .user-attendance-heading h1 {
    font-size: 22px;
  }
  .user-attendance-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
  }
  .user-attendance .att-page-header .att-button {
    gap: 5px;
    padding: 7px 9px;
    font-size: 11px;
  }
  .user-visit-filters {
    gap: 5px;
    padding: 0 16px 12px;
  }
  .user-visit-filters button {
    gap: 5px;
    padding: 6px 7px;
  }
  .week-feedback {
    margin: 0 16px 16px;
  }
}
</style>
