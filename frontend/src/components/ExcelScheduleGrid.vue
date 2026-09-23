<template>
  <section class="excel-shell" :class="{ 'excel-shell--interactive': interactive }">
    <div class="excel-header">
      <div class="calendar-heading">
        <span class="calendar-icon"><CalendarDays :size="21" aria-hidden="true" /></span>
        <div><h2>{{ title }}</h2><p>{{ subtitle }}</p></div>
      </div>
      <div class="calendar-actions">
        <div v-if="!isMobile" class="view-switch" role="group" aria-label="Vista del horario">
          <button type="button" :aria-pressed="viewMode === 'week'" @click="viewMode = 'week'"><CalendarDays :size="15" /> Semana</button>
          <button type="button" :aria-pressed="viewMode === 'agenda'" @click="viewMode = 'agenda'"><List :size="15" /> Agenda</button>
        </div>
        <button type="button" class="excel-export" :disabled="isExporting" @click="exportExcel">
          <Download :size="15" aria-hidden="true" /><span>{{ isExporting ? 'Exportando…' : 'Exportar semana' }}</span>
        </button>
      </div>
    </div>

    <ScheduleWeekPicker v-model="selectedDate" />
    <div class="calendar-summary">
      <p><strong>{{ occurrences.length }} {{ occurrences.length === 1 ? 'sesión' : 'sesiones' }}</strong><span>{{ dateLabel(visibleWeek.from) }} – {{ dateLabel(visibleWeek.to) }}</span></p>
      <div class="service-legend" aria-label="Servicios visibles">
        <span v-for="service in visibleServices" :key="service"><i :style="{ background: eventBorderColor(service) }"></i>{{ serviceLabel(service) }}</span>
      </div>
    </div>
    <p v-if="exportError && !modalFeedback" role="alert" class="calendar-error">{{ exportError }}</p>
    <div v-if="(isMobile || viewMode === 'agenda') && occurrences.length" class="mobile-agenda">
      <section v-for="day in agendaDays" :key="day.fecha" class="agenda-day">
        <header class="agenda-day-heading">
          <div><span class="agenda-date">{{ day.fecha.slice(-2) }}</span><div><h3>{{ dateLabel(day.fecha, { weekday: 'long', day: undefined, month: undefined, year: undefined }) }}</h3><span>{{ dateLabel(day.fecha, { day: undefined }) }}</span></div></div>
          <span class="day-count">{{ day.items.length }} {{ day.items.length === 1 ? 'sesión' : 'sesiones' }}</span>
        </header>
        <button v-for="item in day.items" :key="`${item.id_matricula || item.id_horario_servicio}-${item.fecha}`"
          type="button" class="agenda-event" :disabled="!interactive"
          :class="{ 'agenda-selected': itemId(item) === String(selectedItemId) }"
          :style="{ '--service-color': eventBorderColor(item.servicio) }" @click="selectCalendarItem(item)">
          <span class="agenda-time"><strong>{{ displayTime(item.hora_inicio) }}</strong><span>{{ displayTime(item.hora_fin) }}</span></span>
          <span class="agenda-content"><span class="agenda-service">{{ serviceLabel(item.servicio) }}</span><strong>{{ item.rutina_nombre || 'Clase de ' + serviceLabel(item.servicio) }}</strong><span class="agenda-meta">{{ duration(item) }}<template v-if="item.checkLabel"> · {{ item.checkLabel }}</template></span></span>
          <span class="agenda-availability"><span class="availability-badge" :class="badgeTone(item)">{{ availabilityLabel(item) }}</span><span v-if="item.cupos && !item.is_enrolled" class="capacity-track"><span :style="{ width: `${Math.min(100, 100 * Number(item.cupos_usados || 0) / Number(item.cupos))}%` }"></span></span></span>
          <ChevronRight v-if="interactive" :size="17" class="agenda-chevron" aria-hidden="true" />
        </button>
      </section>
    </div>
    <div v-else-if="occurrences.length" class="excel-calendar">
      <ScheduleTimeGrid :options="calendarOptions" />
    </div>
    <div v-else class="calendar-empty" role="status"><CalendarDays :size="32" /><h3>Una semana por organizar</h3><p>{{ items.length ? 'No hay sesiones en esta semana con los filtros actuales.' : emptyMessage }}</p></div>
    <footer class="calendar-footer"><span><span class="status-dot"></span> {{ interactive ? 'Selecciona una clase para gestionarla' : 'Tu horario y asistencia, semana a semana' }}</span><span>Horarios semanales · Perú</span></footer>
  </section>
</template>

<script setup>
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { CalendarDays, ChevronRight, Download, List } from 'lucide-vue-next';
import ScheduleWeekPicker from './ScheduleWeekPicker.vue';
import { dateLabel, limaDate } from '../utils/attendance.js';
import { calendarDate, monthWeeks, scheduleOccurrences, weekStart } from '../utils/scheduleCalendar.js';
const ScheduleTimeGrid = defineAsyncComponent(() => import('./ScheduleTimeGrid.vue'));

const props = defineProps({
  modalFeedback: Boolean,
  date: { type: String, default: '' },
  title: {
    type: String,
    default: 'Horario',
  },
  subtitle: {
    type: String,
    default: 'Para ver el detalle, presione sobre el bloque del horario',
  },
  items: {
    type: Array,
    default: () => [],
  },
  fileName: {
    type: String,
    default: 'horario.xlsx',
  },
  emptyMessage: {
    type: String,
    default: 'No hay horarios para mostrar.',
  },
  interactive: {
    type: Boolean,
    default: false,
  },
  selectedItemId: {
    type: [String, Number],
    default: '',
  },
});

const emit = defineEmits(['select', 'range-change', 'notification']);
const selectedDate = ref(calendarDate(props.date));
watch(() => props.date, (date) => { selectedDate.value = calendarDate(date); });
const visibleWeek = computed(() => monthWeeks(selectedDate.value.slice(0, 7)).find((week) => week.start === weekStart(selectedDate.value)));
watch(visibleWeek, (week) => emit('range-change', { ...week, month: selectedDate.value.slice(0, 7) }), { immediate: true });
const occurrences = computed(() => scheduleOccurrences(props.items, selectedDate.value, selectedDate.value.slice(0, 7)));
const agendaDays = computed(() => {
  const grouped = new Map();
  for (const item of occurrences.value) {
    if (!grouped.has(item.fecha)) grouped.set(item.fecha, { fecha: item.fecha, items: [] });
    grouped.get(item.fecha).items.push(item);
  }
  return [...grouped.values()];
});
const viewport = typeof window === 'undefined' ? null : window.matchMedia('(max-width: 720px)');
const isMobile = ref(viewport?.matches ?? false);
const resize = (event) => { isMobile.value = event.matches; };
onMounted(() => viewport?.addEventListener('change', resize));
onBeforeUnmount(() => viewport?.removeEventListener('change', resize));
const viewMode = ref('week');
const visibleServices = computed(() => [...new Set(occurrences.value.map((item) => item.servicio))]);
const today = limaDate();
const isExporting = ref(false);
const exportError = ref('');

const dayLabels = {
  lunes: 'Lun',
  martes: 'Mar',
  miercoles: 'Mie',
  jueves: 'Jue',
  viernes: 'Vie',
  sabado: 'Sab.',
  domingo: 'Dom',
};

const dayByIndex = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'];

/**
 * Normaliza el valor recibido.
 */
const normalizeDay = (day) =>
  String(day || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

/**
 * Normaliza el valor recibido.
 */
const normalizeTime = (value) => {
  const [hour = '00', minute = '00'] = String(value || '').split(':');
  return `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}:00`;
};

/**
 * Gestiona esta acción de la vista.
 */
const displayTime = (value) => normalizeTime(value).slice(0, 5);

/**
 * Gestiona esta acción de la vista.
 */
const timeToMinutes = (value) => {
  const [hour = 0, minute = 0] = normalizeTime(value).split(':').map(Number);
  return hour * 60 + minute;
};

/**
 * Gestiona esta acción de la vista.
 */
const minutesToSlotTime = (value) => {
  if (value >= 24 * 60) return '24:00:00';
  const safeValue = Math.max(0, Math.min(24 * 60 - 1, value));
  const hour = Math.floor(safeValue / 60);
  const minute = safeValue % 60;
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;
};

/**
 * Gestiona esta acción de la vista.
 */
const serviceLabel = (service) =>
  ({
    fitness: 'Fitness',
    musculacion: 'Musculacion',
    cardio: 'Cardio',
    baile: 'Baile',
  })[String(service || '').trim().toLowerCase()] || service || 'Servicio';

const availableSlots = (item = {}) =>
  Math.max(0, Number(item.cupos || 0) - Number(item.cupos_usados || 0));

/**
 * Gestiona esta acción de la vista.
 */
const eventColor = (service) =>
  ({
    fitness: '#d9f99d',
    musculacion: '#bfdbfe',
    cardio: '#fde68a',
    baile: '#fecdd3',
  })[String(service || '').trim().toLowerCase()] || '#e2e8f0';

/**
 * Gestiona esta acción de la vista.
 */
const eventBorderColor = (service) =>
  ({
    fitness: '#84cc16',
    musculacion: '#38bdf8',
    cardio: '#f59e0b',
    baile: '#fb7185',
  })[String(service || '').trim().toLowerCase()] || '#94a3b8';

const duration = (item) => `${timeToMinutes(item.hora_fin) - timeToMinutes(item.hora_inicio)} min`;
const availabilityLabel = (item) => item.activo === false ? 'Pausado' : item.is_enrolled ? 'En tu horario' : item.cupos !== undefined ? availableSlots(item) ? `${availableSlots(item)} cupos libres` : 'Completo' : 'Programado';
const badgeTone = (item) => item.activo === false ? 'is-paused' : item.is_enrolled ? 'is-enrolled' : availableSlots(item) === 0 ? 'is-full' : availableSlots(item) <= 2 ? 'is-limited' : 'is-available';

const visibleTimeRange = computed(() => {
  const validItems = occurrences.value.filter((item) => item.hora_inicio && item.hora_fin);
  if (!validItems.length) {
    return { min: '06:00:00', max: '22:00:00' };
  }

  const starts = validItems.map((item) => timeToMinutes(item.hora_inicio));
  const ends = validItems.map((item) => timeToMinutes(item.hora_fin));
  const min = Math.max(0, Math.floor((Math.min(...starts) - 60) / 30) * 30);
  const maxBase = Math.min(24 * 60, Math.ceil((Math.max(...ends) + 60) / 30) * 30);
  const max = Math.max(maxBase, Math.min(24 * 60, min + 240));

  return {
    min: minutesToSlotTime(min),
    max: minutesToSlotTime(max),
  };
});

/**
 * Gestiona esta acción de la vista.
 */
const escapeHtml = (value) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

/**
 * Gestiona esta acción de la vista.
 */
const eventMeta = (item) => {
  if (item.checkLabel) return item.checkLabel;
  if (item.cliente_nombre) return item.cliente_nombre;
  if (item.cupos !== undefined) return `${item.cupos_usados || 0}/${item.cupos} cupos`;
  return `${displayTime(item.hora_inicio)}-${displayTime(item.hora_fin)}`;
};

const itemId = (item = {}) =>
  String(item.id_horario_servicio || item.id_matricula || '');

const selectCalendarItem = (item) => {
  if (!props.interactive) return;
  emit('select', item);
};

const calendarEvents = computed(() =>
  occurrences.value
    .map((item) => {
      const day = normalizeDay(item.dia);
      const date = item.fecha;
      if (!date || !item.hora_inicio || !item.hora_fin) return null;
      const startTime = normalizeTime(item.hora_inicio);
      const endTime = normalizeTime(item.hora_fin);
      const service = serviceLabel(item.servicio);

      const titleLines = [
        item.codigo_dia || service,
        service,
        item.rutina_nombre,
        eventMeta(item),
      ].filter(Boolean);

      return {
        id: String(item.id_horario_servicio || item.id_matricula || `${item.servicio}-${day}-${item.hora_inicio}`),
        title: titleLines.join('\n'),
        start: `${date}T${startTime}`,
        end: `${date}T${endTime}`,
        backgroundColor: eventColor(item.servicio),
        borderColor: eventBorderColor(item.servicio),
        textColor: '#17212f',
        extendedProps: item,
      };
    })
    .filter(Boolean),
);

const calendarOptions = computed(() => ({
  initialView: 'timeGridWeek',
  initialDate: visibleWeek.value.start,
  locale: 'es',
  timeZone: 'local',
  headerToolbar: false,
  allDaySlot: false,
  firstDay: 1,
  slotMinTime: visibleTimeRange.value.min,
  slotMaxTime: visibleTimeRange.value.max,
  slotDuration: '00:30:00',
  slotLabelInterval: '01:00:00',
  scrollTime: visibleTimeRange.value.min,
  height: 'auto',
  expandRows: false,
  nowIndicator: false,
  now: today,
  dayHeaderClassNames: ({ date }) => date.getMonth() + 1 !== Number(selectedDate.value.slice(5, 7)) ? ['outside-month'] : [],
  slotEventOverlap: false,
  eventMinHeight: 78,
  eventOrder: 'start,servicio,title',
  events: calendarEvents.value,
  eventClassNames: ({ event }) => {
    const classes = [];
    if (props.interactive) classes.push('excel-event-selectable');
    if (itemId(event.extendedProps) === String(props.selectedItemId || '')) {
      classes.push('excel-event-selected');
    }
    if (event.extendedProps?.is_enrolled) {
      classes.push('excel-event-is-enrolled');
    }
    return classes;
  },
  eventClick: ({ event }) => selectCalendarItem(event.extendedProps || {}),
  dayHeaderContent: (arg) => {
    const dayKey = dayByIndex[arg.date.getDay()];
    const date = `${arg.date.getFullYear()}-${String(arg.date.getMonth() + 1).padStart(2, '0')}-${String(arg.date.getDate()).padStart(2, '0')}`;
    return { html: `<span class="calendar-day-name">${dayLabels[dayKey] || ''}</span><span class="calendar-day-number ${date === today ? 'is-today' : ''}">${arg.date.getDate()}</span>` };
  },
  slotLabelFormat: {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  },
  eventContent: (arg) => {
    const item = arg.event.extendedProps || {};
    const service = serviceLabel(item.servicio);
    const time = `${displayTime(item.hora_inicio)} – ${displayTime(item.hora_fin)}`;
    const routine = item.rutina_nombre || item.nombre_ejercicio || item.nombre_rutina || `Clase de ${service}`;
    const isEnrolled = Boolean(item.is_enrolled);
    const badgeHtml = `<span class="excel-tag ${badgeTone(item)}">${escapeHtml(availabilityLabel(item))}</span>`;

    return {
      html: `
        <div class="excel-event-card ${isEnrolled ? 'excel-event-card--enrolled' : ''}">
          <div class="excel-event-header">
            <span class="excel-event-service">${escapeHtml(service)}</span>
          </div>
          <span class="excel-event-exercise">${escapeHtml(routine)}</span>
          <span class="excel-event-time">${escapeHtml(time)}</span>
          ${badgeHtml}
          ${item.checkLabel ? `<span class="excel-event-time">${escapeHtml(item.checkLabel)}</span>` : ''}
        </div>
      `,
    };
  },
  eventDidMount: ({ el, event }) => {
    const item = event.extendedProps || {};
    const exercise = item.rutina_nombre || item.nombre_ejercicio || item.nombre_rutina || serviceLabel(item.servicio);
    const accessibleDescription = [
      exercise,
      serviceLabel(item.servicio),
      dateLabel(item.fecha, { weekday: 'long' }),
      `${displayTime(item.hora_inicio)} - ${displayTime(item.hora_fin)}`,
      item.cupos !== undefined ? `Cupos: ${availableSlots(item)} libres de ${item.cupos}` : '',
      item.is_enrolled ? 'Ya matriculado' : '',
    ].filter(Boolean).join(' | ');
    el.title = accessibleDescription;

    if (props.interactive) {
      el.tabIndex = 0;
      el.setAttribute('role', 'button');
      el.setAttribute('aria-label', `${accessibleDescription}. Seleccionar horario.`);
      el.addEventListener('keydown', (eventKey) => {
        if (eventKey.key !== 'Enter' && eventKey.key !== ' ') return;
        eventKey.preventDefault();
        selectCalendarItem(item);
      });
    }
  },
}));

/**
 * Gestiona esta acción de la vista.
 */
const exportExcel = async () => {
  if (isExporting.value) return;
  isExporting.value = true;
  exportError.value = '';
  try {
    const XLSX = await import('xlsx');
    const rows = occurrences.value.map((item) => ({
      Servicio: serviceLabel(item.servicio),
      Fecha: item.fecha,
      Semana: `${visibleWeek.value.from} – ${visibleWeek.value.to}`,
      Dia: item.dia || '',
      Codigo: item.codigo_dia || '',
      Rutina: item.rutina_nombre || '',
      Zonas: item.zonas_musculares || '',
      Inicio: item.hora_inicio || '',
      Salida: item.hora_fin || '',
      Cupos: item.cupos ?? '',
      Matriculados: item.cupos_usados ?? '',
      Cliente: item.cliente_nombre || '',
      Entrada: item.entryTime || '',
      SalidaRegistrada: item.exitTime || '',
      Check: item.checkLabel || '',
    }));

    const worksheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Horario');
    XLSX.writeFile(workbook, `${props.fileName.replace(/\.xlsx$/, '')}-${visibleWeek.value.from}.xlsx`);
    if (props.modalFeedback) emit('notification', { tone: 'success', message: 'La descarga del horario de esta semana se ha iniciado.' });
  } catch {
    exportError.value = 'No se pudo exportar. Inténtalo de nuevo.';
    if (props.modalFeedback) emit('notification', { tone: 'error', message: exportError.value });
  } finally { isExporting.value = false; }
};
</script>

<style scoped>
.excel-shell { --calendar-surface: #fff; --calendar-muted: #f8fafc; --calendar-line: #e8ecf1; --calendar-text: #17212f; --calendar-secondary: #687586; width: 100%; min-width: 0; border: 1px solid var(--app-border); border-radius: 18px; background: var(--calendar-surface); color: var(--calendar-text); overflow: hidden; box-shadow: 0 6px 24px var(--app-shadow); }
:global([data-theme="dark"] .excel-shell) { --calendar-surface: #1d1e22; --calendar-muted: #24252a; --calendar-line: #303238; --calendar-text: #f1f3f6; --calendar-secondary: #a5abb6; }
.excel-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 22px 24px; border-bottom: 1px solid var(--calendar-line); }
.calendar-heading { display: flex; align-items: center; min-width: 0; gap: 12px; }
.calendar-icon { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: var(--app-accent-soft); color: var(--app-accent-text); flex: 0 0 auto; }
.calendar-heading h2 { margin: 0; font-size: 18px; font-weight: 750; letter-spacing: -.025em; color: var(--calendar-text); }
.calendar-heading p { margin: 5px 0 0; font-size: 12px; line-height: 1.5; color: var(--calendar-secondary); max-width: 430px; }
.calendar-actions, .view-switch { display: flex; align-items: center; gap: 8px; }
.view-switch { padding: 4px; gap: 2px; background: var(--calendar-muted); border: 1px solid var(--calendar-line); border-radius: 10px; }
.calendar-actions button { display: inline-flex; justify-content: center; align-items: center; gap: 7px; white-space: nowrap; font: inherit; font-size: 12px; font-weight: 650; min-height: 36px; padding: 8px 12px; border-radius: 7px; color: var(--calendar-secondary); cursor: pointer; }
.view-switch button { background: transparent; border: 0; }
.view-switch button[aria-pressed="true"] { background: var(--calendar-surface); color: var(--calendar-text); box-shadow: 0 1px 4px #00000015; }
.calendar-actions .excel-export { border: 1px solid var(--calendar-line); color: var(--calendar-text); min-height: 44px; background: transparent; }
.calendar-actions button:hover { color: var(--app-accent-text); }
button:focus-visible { outline: 2px solid var(--app-accent); outline-offset: 3px; }
.calendar-summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 24px 18px; }
.calendar-summary p { display: flex; flex-wrap: wrap; gap: 8px 12px; margin: 0; font-size: 11px; color: var(--calendar-secondary); }
.calendar-summary strong { color: var(--calendar-text); font-weight: 650; }
.service-legend { display: flex; flex-wrap: wrap; gap: 12px; }
.service-legend span { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--calendar-secondary); }
.service-legend i { width: 6px; height: 6px; border-radius: 50%; }
.excel-calendar { overflow: auto; max-height: 660px; border-top: 1px solid var(--calendar-line); scrollbar-width: thin; }
:deep(.fc) { width: 100%; min-width: 740px; font-family: inherit; font-size: 12px; --fc-border-color: var(--calendar-line); --fc-page-bg-color: var(--calendar-surface); --fc-neutral-bg-color: var(--calendar-muted); --fc-today-bg-color: transparent; }
:deep(.fc-scrollgrid) { border: 0; }
:deep(.fc-col-header-cell) { background: var(--calendar-muted); }
:deep(.fc-col-header-cell-cushion) { display: flex; flex-direction: column; align-items: center; gap: 5px; padding: 12px 4px; }
:deep(.calendar-day-name) { font-size: 10px; font-weight: 650; text-transform: uppercase; letter-spacing: .07em; color: var(--calendar-secondary); }
:deep(.calendar-day-number) { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; font-size: 16px; font-weight: 700; color: var(--calendar-text); }
:deep(.calendar-day-number.is-today) { background: var(--app-accent); color: #fff; }
:deep(.outside-month) { opacity: .45; }
:deep(.fc-timegrid-slot) { height: 48px; }
:deep(.fc-timegrid-slot-minor) { border-top: 1px dashed var(--calendar-line); }
:deep(.fc-timegrid-slot-label) { color: var(--calendar-secondary); font-size: 10px; background: var(--calendar-muted); }
:deep(.fc-timegrid-slot-label-cushion) { padding: 0 10px; }
:deep(.fc-timegrid-event) { border-radius: 8px; border-width: 0 0 0 3px; margin: 3px 3px 0; box-shadow: 0 2px 4px #00000008; overflow: hidden; }
:deep(.fc-event-main) { padding: 0; }
:deep(.excel-event-card) { display: flex; flex-direction: column; gap: 4px; padding: 8px; color: #17212f; line-height: 1.25; height: 100%; overflow: hidden; }
:deep(.excel-event-service) { font-size: 9px; font-weight: 750; text-transform: uppercase; letter-spacing: .05em; opacity: .75; }
:deep(.excel-event-exercise) { font-size: 12px; font-weight: 750; overflow-wrap: anywhere; }
:deep(.excel-event-time) { font-size: 10px; }
:deep(.excel-tag) { width: fit-content; font-size: 9px; font-weight: 650; padding: 2px 5px; border-radius: 4px; margin-top: auto; background: #ffffffa8; color: #294535; }
:deep(.excel-tag.is-full) { color: #9f1239; background: #fff1f2; }
:deep(.excel-tag.is-enrolled) { color: #075985; background: #e0f2fe; }
:deep(.excel-tag.is-paused) { color: #52525b; background: #f4f4f5; }
:deep(.excel-event-selected), :deep(.excel-event-selectable:focus-visible) { outline: 2px solid var(--app-accent); outline-offset: 2px; z-index: 4; }
:deep(.excel-event-selectable) { cursor: pointer; }
:deep(.excel-event-selectable:hover) { filter: brightness(.97); }
.mobile-agenda { padding: 0 24px 20px; }
.agenda-day + .agenda-day { margin-top: 22px; }
.agenda-day-heading, .agenda-day-heading > div { display: flex; align-items: center; gap: 10px; }
.agenda-day-heading { justify-content: space-between; padding: 12px 0; }
.agenda-date { font-size: 24px; font-weight: 750; letter-spacing: -.04em; }
.agenda-day-heading h3 { margin: 0 0 2px; font-size: 12px; font-weight: 700; text-transform: capitalize; }
.agenda-day-heading div div > span, .day-count { font-size: 10px; color: var(--calendar-secondary); }
.agenda-event { display: flex; align-items: center; gap: 18px; width: 100%; text-align: left; padding: 18px; margin-bottom: 8px; border: 1px solid var(--calendar-line); border-left: 3px solid var(--service-color); border-radius: 10px; background: var(--calendar-surface); color: var(--calendar-text); cursor: pointer; }
.agenda-event:disabled { opacity: 1; cursor: default; }
.agenda-event:not(:disabled):hover { background: var(--calendar-muted); }
.agenda-time { display: flex; flex-direction: column; gap: 5px; padding-right: 18px; border-right: 1px solid var(--calendar-line); }
.agenda-time strong { font-size: 16px; font-weight: 750; }
.agenda-time > span { font-size: 11px; color: var(--calendar-secondary); }
.agenda-content { display: flex; flex: 1; min-width: 0; flex-direction: column; gap: 5px; }
.agenda-service { font-size: 9px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: var(--calendar-secondary); }
.agenda-content > strong { font-size: 14px; font-weight: 700; }
.agenda-meta { font-size: 11px; color: var(--calendar-secondary); }
.agenda-availability { display: flex; flex-direction: column; gap: 10px; }
.availability-badge { font-size: 10px; font-weight: 650; border-radius: 5px; padding: 5px 8px; background: var(--calendar-muted); white-space: nowrap; }
.availability-badge.is-enrolled { background: #0284c718; color: var(--calendar-text); }
.availability-badge.is-full { background: #e11d481a; color: var(--app-accent-text); }
.capacity-track { height: 3px; border-radius: 2px; background: var(--calendar-line); overflow: hidden; }
.capacity-track > span { display: block; height: 100%; background: var(--service-color); }
.agenda-chevron { color: var(--calendar-secondary); }
.agenda-selected { outline: 2px solid var(--app-accent); outline-offset: 1px; }
.calendar-footer { display: flex; justify-content: space-between; gap: 10px; border-top: 1px solid var(--calendar-line); padding: 13px 24px; color: var(--calendar-secondary); font-size: 10px; }
.calendar-footer > span:first-child { display: flex; align-items: center; gap: 7px; }
.status-dot { width: 5px; height: 5px; border-radius: 50%; background: #22c55e; }
.calendar-empty { display: flex; flex-direction: column; align-items: center; padding: 48px 24px; text-align: center; color: var(--calendar-secondary); }
.calendar-empty h3 { margin: 14px 0 8px; color: var(--calendar-text); font-size: 16px; }
.calendar-empty p, .calendar-error { font-size: 12px; }
.calendar-error { padding: 12px 24px; color: var(--app-accent-text); }
@media (max-width: 1100px) { .excel-header { flex-wrap: wrap; } .calendar-summary { flex-wrap: wrap; } }
@media (max-width: 720px) {
  .excel-shell { border-radius: 14px; }
  .excel-header { padding: 16px; gap: 14px; }
  .calendar-icon { display: none; }
  .calendar-heading h2 { font-size: 16px; }
  .calendar-heading p { font-size: 11px; }
  .calendar-actions { width: 100%; }
  .calendar-actions .excel-export { padding: 0; border: 0; min-height: 28px; font-size: 11px; }
  .calendar-summary { padding: 0 16px 16px; gap: 10px; }
  .calendar-summary p > span { display: none; }
  .service-legend { gap: 10px; }
  .mobile-agenda { padding: 0 16px 14px; }
  .agenda-event { gap: 12px; padding: 14px 12px; flex-wrap: wrap; }
  .agenda-time { padding-right: 12px; }
  .agenda-content { flex-basis: calc(100% - 75px); }
  .agenda-content > strong { font-size: 13px; }
  .agenda-availability { margin-left: 63px; }
  .capacity-track { display: none; }
  .agenda-chevron { margin-left: auto; }
  .calendar-footer { padding: 12px 16px; }
  .calendar-footer > span:last-child { display: none; }
}
@media (prefers-reduced-motion: no-preference) { .agenda-event, .calendar-actions button { transition: background .15s, outline-color .15s; } }
</style>
