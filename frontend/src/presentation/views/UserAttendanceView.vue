<template>
  <div class="attendance-page user-attendance">
    <header class="att-page-header">
      <div>
        <h1>Mi asistencia</h1>
        <p class="att-muted">Consulta tus clases, entradas y salidas del gimnasio.</p>
      </div>
      <router-link class="att-button" to="/user/schedule"
        ><CalendarDays :size="16" />Ver mis horarios</router-link
      >
    </header>
    <div class="att-tabs user-attendance-nav" role="group" aria-label="Vistas de mi asistencia">
      <button type="button" :aria-pressed="!showHistory" aria-controls="attendance-week"
        @click="showHistory = false">
        <CalendarDays :size="16" aria-hidden="true" /> Semana
      </button>
      <button type="button" :aria-pressed="showHistory" aria-controls="attendance-history"
        @click="showHistory = true">
        <History :size="16" aria-hidden="true" /> Historial
      </button>
    </div>
    <section v-show="!showHistory" id="attendance-week" class="att-panel" aria-labelledby="attendance-week-title">
      <div class="att-heading-row user-week-heading">
        <div>
          <h2 id="attendance-week-title">Actividad de la semana</h2>
          <p class="att-muted">{{ dateLabel(visibleRange.from, { year: undefined }) }} – {{ dateLabel(visibleRange.to) }}</p>
        </div>
        <p v-if="week && !loading" class="user-week-total">
          <strong>{{ visibleVisits }}</strong> {{ visibleVisits === 1 ? 'visita registrada' : 'visitas registradas' }}
        </p>
      </div>
      <div class="user-week-picker">
        <ScheduleWeekPicker :model-value="selectedDate" @update:model-value="selectDate" />
      </div>
      <p v-if="error" role="alert" class="att-message is-error">
        {{ error }} <button class="att-link" @click="load">Reintentar</button>
      </p>
      <div v-if="loading" class="att-empty" role="status">
        Cargando tu semana…
      </div>
      <div v-else-if="week" class="user-week-grid">
        <article
          v-for="day in weekDays"
          :key="day.date"
          class="att-week-day"
          :class="{ 'is-current': day.date === week.hoy }"
        >
          <header>
            <span>{{ day.name }}</span
            ><strong>{{ day.date.slice(-2) }}</strong
            ><span v-if="day.date === week.hoy" class="att-badge today"
              >Hoy</span
            >
          </header>
          <div v-if="!day.items.length && !day.generalVisits.length" class="att-muted att-small">
            Sin actividad
          </div>
          <div
            v-for="item in day.items"
            :key="item.id_matricula"
            class="att-week-event"
          >
            <strong>{{ services[item.servicio] }}</strong>
            <p>
              {{ shortTime(item.hora_inicio) }} – {{ shortTime(item.hora_fin) }}
            </p>
            <span
              class="att-badge"
              :class="item.asistencia?.estado || 'neutral'"
              >{{
                item.asistencia
                  ? states[item.asistencia.estado]
                  : item.fecha > week.hoy
                    ? 'Programado'
                    : 'Sin registro'
              }}</span
            >
            <p v-if="item.asistencia" class="att-week-times">
              Entrada
              {{
                shortTime(item.asistencia.hora_entrada || item.asistencia.hora)
              }}<br />Salida {{ shortTime(item.asistencia.hora_salida) }}
            </p>
          </div>
          <div v-for="visit in day.generalVisits" :key="visit.id_asistencia" class="att-week-event">
            <strong>Gimnasio general</strong>
            <p>Entrada {{ shortTime(visit.hora_entrada || visit.hora) }}<br />{{ visit.cierre_automatico ? 'Cierre automático' : 'Salida' }} {{ shortTime(visit.hora_salida) }}</p>
            <span class="att-badge" :class="visit.estado">{{ states[visit.estado] }}</span>
          </div>
        </article>
      </div>
    </section>
    <div v-show="showHistory" id="attendance-history">
      <AttendanceHistory v-if="historyOpened" />
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import ScheduleWeekPicker from '../components/ScheduleWeekPicker.vue';
import { calendarDate, monthWeeks, weekStart } from '../../domain/utils/scheduleCalendar.js';
import {
  CalendarDays,
  History,
} from 'lucide-vue-next';
import { useAuth } from '../../application/composables/useAuth';
import { useAttendance } from '../../application/services/attendance.js';
import {
  addDays,
  dateLabel,
  days,
  services,
  shortTime,
  states,
} from '../utils/attendance';
import AttendanceHistory from '../components/attendance/AttendanceHistory.vue';
import '../styles/attendance.css';

const { attendanceGet } = useAttendance();

const { token } = useAuth();
const route = useRoute();
const showHistory = ref(false);
const historyOpened = ref(false);
watch(showHistory, (open) => {
  if (open) historyOpened.value = true;
});
const selectedDate = ref(calendarDate(route.query.fecha));
const visibleRange = computed(() => monthWeeks(selectedDate.value.slice(0, 7)).find((range) => range.start === weekStart(selectedDate.value)));
let requestId = 0;
const week = ref(null),
  loading = ref(false),
  error = ref('');
const visibleVisits = computed(() => {
  if (!week.value || loading.value) return '—';
  if (!week.value.visitas_por_fecha) return week.value.visitas;
  return Object.entries(week.value.visitas_por_fecha).reduce((sum, [date, count]) =>
    sum + (date >= visibleRange.value.from && date <= visibleRange.value.to ? count : 0), 0);
});
const weekDays = computed(() =>
  Object.values(days).map((name, index) => {
    const date = addDays(week.value.inicio, index);
    return {
      name,
      date,
      items: week.value.horarios.filter((item) => item.fecha === date),
      generalVisits: (week.value.generales || []).filter((item) => item.fecha === date),
    };
  }).filter((day) => day.date >= visibleRange.value.from && day.date <= visibleRange.value.to),
);
const load = async () => {
  const id = ++requestId;
  loading.value = true;
  error.value = '';
  try {
    const result = await attendanceGet(
      '/mi-semana',
      { inicio: weekStart(selectedDate.value) },
      token.value,
    );
    if (id === requestId) week.value = result;
  } catch (err) {
    if (id !== requestId) return;
    error.value = err.message;
    week.value = null;
  } finally {
    if (id === requestId) loading.value = false;
  }
};
const selectDate = (date) => {
  selectedDate.value = date;
  load();
};
watch(() => route.query.fecha, (value) => selectDate(calendarDate(value)));
onMounted(load);
</script>

<style scoped>
.user-attendance-nav {
  justify-self: start;
}
.user-attendance-nav button {
  font-size: 0.875rem;
}
.user-attendance-nav button[aria-pressed='true'] {
  background: var(--app-accent-soft);
  color: var(--app-accent-text);
}
#attendance-history {
  min-width: 0;
}
.user-week-heading {
  flex-wrap: wrap;
}
.user-week-total {
  padding: 8px 12px;
  border-radius: 10px;
  background: var(--app-accent-soft);
  color: var(--app-accent-text);
  font-size: 0.875rem;
}
.user-week-picker {
  margin: 16px 0;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  background: var(--app-surface-soft);
}
.user-week-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 170px), 1fr));
  gap: 12px;
}
.user-week-grid .att-week-day {
  min-height: 0;
  padding: 14px;
  background: var(--app-surface-soft);
}
.user-week-grid .att-week-day > header > span:first-child {
  font-size: 0.8125rem;
}
.user-week-grid .att-week-event {
  overflow-wrap: anywhere;
}
.user-week-grid .att-week-event > strong,
.user-week-grid .att-week-event > p {
  font-size: 0.875rem;
}
.user-week-grid .att-week-event + .att-week-event {
  border-top: 1px solid var(--app-border);
}
</style>
