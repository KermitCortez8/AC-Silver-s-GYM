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
                ? `${dateLabel(week.inicio, { year: undefined })} – ${dateLabel(week.fin)}`
                : 'Horario y visitas'
            }}
          </h2>
          <p class="att-muted">
            {{ week?.visitas ?? '—' }} visitas registradas esta semana · Hora de
            Perú
          </p>
        </div>
        <div class="att-row-actions">
          <button
            class="att-button"
            aria-label="Semana anterior"
            :disabled="loading"
            @click="move(-7)"
          >
            <ChevronLeft :size="16" /></button
          ><button class="att-button" :disabled="loading" @click="currentWeek">
            Hoy</button
          ><button
            class="att-button"
            aria-label="Semana siguiente"
            :disabled="loading"
            @click="move(7)"
          >
            <ChevronRight :size="16" />
          </button>
        </div>
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
import { computed, onMounted, ref } from 'vue';
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-vue-next';
import { useAuth } from '../composables/useAuth';
import { attendanceGet } from '../services/attendanceService';
import {
  addDays,
  dateLabel,
  days,
  limaDate,
  services,
  shortTime,
  states,
} from '../utils/attendance';
import AttendanceHistory from '../components/attendance/AttendanceHistory.vue';
import '../styles/attendance.css';
const { token } = useAuth();
const week = ref(null),
  start = ref(''),
  loading = ref(false),
  error = ref('');
const weekDays = computed(() =>
  Object.values(days).map((name, index) => {
    const date = addDays(week.value.inicio, index);
    return {
      name,
      date,
      items: week.value.horarios.filter((item) => item.fecha === date),
    };
  }),
);
const load = async () => {
  loading.value = true;
  error.value = '';
  try {
    week.value = await attendanceGet(
      '/mi-semana',
      { inicio: start.value },
      token.value,
    );
  } catch (err) {
    error.value = err.message;
    week.value = null;
  } finally {
    loading.value = false;
  }
};
const move = (delta) => {
  start.value = addDays(week.value?.inicio || start.value || limaDate(), delta);
  load();
};
const currentWeek = () => {
  start.value = '';
  load();
};
onMounted(load);
</script>
