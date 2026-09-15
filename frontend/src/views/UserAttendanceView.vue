<template>
  <div class="attendance-page">
    <header class="att-page-header">
      <div>
        <p class="att-eyebrow">Mi actividad · Silver's Gym</p>
        <h1>Mi asistencia</h1>
        <p class="att-muted">
          Tu constancia, visita a visita. Consulta tus horarios y registros.
        </p>
      </div>
      <router-link class="att-button" to="/user/schedule"
        ><CalendarDays :size="16" />Ver mis horarios</router-link
      >
    </header>
    <div class="att-notice">
      <ShieldCheck :size="18" />
      <p>
        El administrador registra tus entradas y salidas. Aquí puedes consultar
        tu asistencia.
      </p>
    </div>
    <section class="att-panel">
      <div class="att-heading-row">
        <div>
          <p class="att-eyebrow">Mi semana</p>
          <h2>
            {{
              week
                ? `${dateLabel(visibleRange.from, { year: undefined })} – ${dateLabel(visibleRange.to)}`
                : 'Horario y visitas'
            }}
          </h2>
          <p class="att-muted">
            {{ visibleVisits }} visitas registradas en estas fechas · Hora de
            Perú
          </p>
        </div>
      </div>
      <div class="mb-4 rounded-xl" style="background: var(--app-surface); border: 1px solid var(--app-border)">
        <ScheduleWeekPicker :model-value="selectedDate" @update:model-value="selectDate" />
      </div>
      <p v-if="error" role="alert" class="att-message is-error">
        {{ error }} <button class="att-link" @click="load">Reintentar</button>
      </p>
      <div v-if="loading" class="att-empty" role="status">
        Cargando tu semana…
      </div>
      <div v-else-if="week" class="att-week-grid">
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
          <div v-if="!day.items.length" class="att-muted att-small">
            Sin horario
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
        </article>
      </div>
      <p class="att-muted att-small att-week-note">
        Se muestran tus matrículas actuales. Todas tus visitas anteriores están
        en el historial.
      </p>
    </section>
    <AttendanceHistory />
  </div>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import ScheduleWeekPicker from '../components/ScheduleWeekPicker.vue';
import { calendarDate, monthWeeks, weekStart } from '../utils/scheduleCalendar.js';
import {
  CalendarDays,
  ShieldCheck,
} from 'lucide-vue-next';
import { useAuth } from '../composables/useAuth';
import { attendanceGet } from '../services/attendanceService';
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
const { token } = useAuth();
const route = useRoute();
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
