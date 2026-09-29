<template>
  <div class="schedule-admin space-y-5">
    <header class="schedule-page-header">
      <div><p class="schedule-eyebrow">Planificación del gimnasio</p><h1>Horarios por servicio</h1><p class="schedule-description">Organiza tus clases, revisa los cupos y planifica cada semana.</p></div>
      <div class="schedule-page-actions">
        <button type="button" class="schedule-secondary" :disabled="isRefreshing" @click="refreshAll(true)"><RefreshCw :size="16" :class="{ 'animate-spin': isRefreshing }" />{{ isRefreshing ? 'Actualizando…' : 'Actualizar' }}</button>
        <button type="button" class="schedule-primary" @click="openNewSchedule"><Plus :size="17" />Nuevo horario</button>
      </div>
    </header>
    <section class="schedule-workspace" aria-label="Calendario de clases">
      <div class="schedule-toolbar">
        <div class="schedule-metrics"><span><strong>{{ activeSchedules }}</strong> horarios activos</span><span><strong>{{ usedSlots }} / {{ totalSlots }}</strong> cupos ocupados</span></div>
        <div class="schedule-search-actions"><label class="schedule-search"><Search :size="16" aria-hidden="true" /><input v-model="filters.search" placeholder="Buscar una clase…" aria-label="Buscar horario" /></label><button type="button" class="schedule-secondary" :aria-expanded="showFilters" aria-controls="schedule-filters" @click="showFilters = !showFilters"><SlidersHorizontal :size="15" />Filtros<span v-if="extraFilterCount" class="filter-count">{{ extraFilterCount }}</span></button></div>
      </div>
      <nav class="service-tabs" aria-label="Filtrar por servicio">
        <button v-for="service in serviceFilters" :key="service.value" type="button" :aria-pressed="filters.servicio === service.value" @click="filters.servicio = service.value">
          <span v-if="service.value !== 'todos'" class="service-tab-dot" :style="{ background: servicePalette[service.value].border }"></span>{{ service.value === 'todos' ? 'Todas las clases' : service.label }}<span class="service-tab-count">{{ service.value === 'todos' ? schedules.length : schedules.filter((item) => item.servicio === service.value).length }}</span>
        </button>
      </nav>
      <div v-if="showFilters" id="schedule-filters" class="schedule-extra-filters">
        <label>Día<select v-model="filters.dia"><option value="todos">Todos los días</option><option v-for="day in days" :key="day.value" :value="day.value">{{ day.label }}</option></select></label>
        <label>Disponibilidad<select v-model="filters.estado"><option v-for="status in statusFilters" :key="status.value" :value="status.value">{{ status.label }}</option></select></label>
        <label>Ordenar<select v-model="filters.sortBy"><option v-for="option in sortOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
        <button type="button" class="schedule-secondary" @click="resetFilters">Limpiar filtros</button>
      </div>
      <ExcelScheduleGrid title="Calendario de clases" subtitle="Elige tu semana y selecciona una clase para editarla."
        interactive modal-feedback @notification="showNotification" @select="editSchedule" @range-change="visibleRange = $event" :items="filteredSchedules" file-name="horarios-servicio.xlsx" />
    </section>

    <section class="schedule-list-section">
      <button type="button" class="schedule-list-toggle" :aria-expanded="showList" aria-controls="schedule-list" @click="showList = !showList"><span><List :size="17" /><strong>Gestionar lista de horarios</strong><span>{{ weeklySchedules.length }} sesiones esta semana</span></span><ChevronDown :size="18" :class="{ 'rotate-180': showList }" /></button>
      <div id="schedule-list" v-if="showList">
      <div v-if="weeklySchedules.length" class="mt-5 overflow-hidden rounded-2xl border schedule-border schedule-surface shadow-xl shadow-black/10">
        <div class="hidden overflow-x-auto lg:block">
          <table class="w-full min-w-[960px] text-left text-sm">
            <thead class="sticky top-0 z-10 schedule-inset text-[11px] uppercase tracking-[0.22em] schedule-muted">
              <tr>
                <th class="px-5 py-4">Servicio</th>
                <th class="px-5 py-4">Rutina</th>
                <th class="px-5 py-4">Fecha</th>
                <th class="px-5 py-4">Horario</th>
                <th class="px-5 py-4">Cupos</th>
                <th class="px-5 py-4">Estado</th>
                <th class="px-5 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y schedule-dividers">
              <tr
                v-for="schedule in weeklySchedules"
                :key="schedule.id_horario_servicio"
                class="group schedule-surface transition schedule-row"
                :style="serviceStyle(schedule.servicio)"
              >
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <span class="schedule-service-accent h-10 w-1.5 rounded-full"></span>
                    <div class="min-w-0">
                      <p class="truncate font-black schedule-text">{{ serviceLabel(schedule.servicio) }}</p>
                      <p class="mt-1 text-xs schedule-muted">Horario #{{ schedule.id_horario_servicio }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4">
                  <p class="font-bold schedule-text">{{ routineName(schedule.id_rutina) }}</p>
                  <p class="mt-1 text-xs schedule-muted">{{ routineZones(schedule.id_rutina) }}</p>
                </td>
                <td class="px-5 py-4">
                  <p class="font-bold schedule-text">{{ dateLabel(schedule.fecha, { weekday: 'long' }) }}</p>
                  <span class="schedule-service-badge mt-1 inline-flex rounded-full px-2.5 py-1 text-xs font-black">
                    {{ schedule.codigo_dia }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <p class="font-black schedule-text">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</p>
                  <p class="mt-1 text-xs schedule-muted">{{ durationLabel(schedule) }}</p>
                </td>
                <td class="px-5 py-4">
                  <div class="max-w-[220px]">
                    <div class="flex items-center justify-between gap-3 text-xs">
                      <span class="font-bold schedule-text">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</span>
                      <span class="schedule-muted">{{ availableSlots(schedule) }} libres</span>
                    </div>
                    <div class="mt-2 h-2 overflow-hidden rounded-full schedule-track">
                      <div class="schedule-service-progress h-full rounded-full" :style="{ width: `${slotsPercent(schedule)}%` }"></div>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4">
                  <span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-black" :class="statusClass(schedule)">
                    {{ isScheduleActive(schedule) ? 'Activo' : 'Pausado' }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <div class="flex justify-end gap-2">
                    <button class="rounded-xl border schedule-border bg-white/5 px-3 py-2 text-sm font-bold schedule-text transition hover:bg-white/10" @click="editSchedule(schedule)">Editar</button>
                    <button class="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm font-bold schedule-danger transition hover:bg-rose-400/10" @click="removeSchedule(schedule)">Eliminar</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="grid gap-3 p-3 lg:hidden">
          <article
            v-for="schedule in weeklySchedules"
            :key="`mobile-${schedule.id_horario_servicio}`"
            class="rounded-2xl border schedule-border schedule-surface p-4"
            :style="serviceStyle(schedule.servicio)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 items-center gap-3">
                <span class="schedule-service-accent h-11 w-1.5 rounded-full"></span>
                <div class="min-w-0">
                  <p class="truncate text-base font-black schedule-text">{{ serviceLabel(schedule.servicio) }}</p>
                  <p class="mt-1 text-xs schedule-muted">
                    {{ dateLabel(schedule.fecha, { weekday: 'long' }) }}
                    <span class="schedule-service-badge ml-1 inline-flex rounded-full px-2 py-0.5 font-black">{{ schedule.codigo_dia }}</span>
                  </p>
                </div>
              </div>
              <span class="shrink-0 rounded-full px-3 py-1 text-xs font-black" :class="statusClass(schedule)">
                {{ isScheduleActive(schedule) ? 'Activo' : 'Pausado' }}
              </span>
            </div>

            <div class="mt-4 grid gap-3 rounded-2xl border schedule-border schedule-inset p-3 text-sm sm:grid-cols-2">
              <div>
                <p class="text-xs uppercase tracking-[0.18em] schedule-muted">Horario</p>
                <p class="mt-1 font-black schedule-text">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</p>
                <p class="text-xs schedule-muted">{{ durationLabel(schedule) }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-[0.18em] schedule-muted">Rutina</p>
                <p class="mt-1 font-black schedule-text">{{ routineName(schedule.id_rutina) }}</p>
                <p class="text-xs schedule-muted">{{ routineZones(schedule.id_rutina) }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-[0.18em] schedule-muted">Cupos</p>
                <p class="mt-1 font-black schedule-text">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</p>
                <p class="text-xs schedule-muted">{{ availableSlots(schedule) }} libres</p>
              </div>
            </div>

            <div class="mt-3 h-2 overflow-hidden rounded-full schedule-track">
              <div class="schedule-service-progress h-full rounded-full" :style="{ width: `${slotsPercent(schedule)}%` }"></div>
            </div>

            <div class="mt-4 grid grid-cols-2 gap-2">
              <button class="rounded-xl border schedule-border bg-white/5 px-3 py-2 text-sm font-bold schedule-text" @click="editSchedule(schedule)">Editar</button>
              <button class="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm font-bold schedule-danger" @click="removeSchedule(schedule)">Eliminar</button>
            </div>
          </article>
        </div>
      </div>

      <p v-if="!weeklySchedules.length" class="mt-6 rounded-2xl border schedule-border bg-white/5 px-4 py-3 text-sm schedule-muted">
        No hay sesiones en esta semana con los filtros actuales.
      </p>
      </div>
    </section>

    <ScheduleModal v-if="isEditorOpen" wide :title="form.id_horario_servicio ? 'Editar horario' : 'Nuevo horario'" :busy="isSaving" @close="closeEditor">
        <form class="schedule-editor" novalidate @submit.prevent="saveSchedule">
          <p class="editor-intro">Define el servicio, la rutina y los cupos de tu clase semanal.</p>
          <div class="mt-6 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm schedule-soft">Servicio</span>
              <select autofocus v-model="form.servicio" class="field-input">
                <option value="fitness">Fitness</option>
                <option value="musculacion">Musculación</option>
                <option value="cardio">Cardio</option>
                <option value="baile">Baile</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Rutina específica</span>
              <select v-model.number="form.id_rutina" class="field-input">
                <option :value="0">Selecciona una rutina</option>
                <option v-for="routine in routinesForSelectedService" :key="routine.id_rutina" :value="routine.id_rutina">
                  {{ routine.nombre_rutina }} - {{ routine.zonas_musculares || 'Sin zonas' }}
                </option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Día de cada semana</span>
              <select v-model="form.dia" class="field-input">
                <option v-for="day in days" :key="day.value" :value="day.value">{{ day.label }}</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Código del día</span>
              <input v-model="form.codigo_dia" class="field-input" placeholder="LUN" maxlength="10" />
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Hora de inicio</span>
              <input v-model="form.hora_inicio" type="time" class="field-input" />
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Hora de salida</span>
              <input v-model="form.hora_fin" type="time" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm schedule-soft">Cupos</span>
              <input v-model.number="form.cupos" type="number" min="1" class="field-input" />
            </label>
          </div>

          <p class="mt-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm schedule-soft">
            Este horario se repite cada semana. Al editarlo, el cambio se aplica a las próximas clases y sus recordatorios. La duración debe ser de 1 o 2 horas.
          </p>

          <label class="mt-5 flex items-center gap-3 text-sm font-bold schedule-text">
            <input v-model="form.activo" type="checkbox" class="h-4 w-4 schedule-checkbox" />
            Disponible para matrícula
          </label>

          <footer class="editor-actions">
            <button type="button" class="schedule-secondary" :disabled="isSaving" @click="closeEditor">Cancelar</button>
            <button type="submit" class="schedule-primary" :disabled="isSaving">{{ isSaving ? 'Guardando…' : 'Guardar horario' }}</button>
          </footer>
        </form>
    </ScheduleModal>
    <ScheduleModal v-if="pendingDelete" title="¿Eliminar este horario?" :busy="isDeleting" @close="pendingDelete = null">
      <div class="notice-icon is-danger"><Trash2 :size="24" /></div>
      <p class="notice-message">Vas a eliminar el horario de <strong>{{ serviceLabel(pendingDelete.servicio) }}</strong> del {{ dayLabel(pendingDelete.dia) }}, de {{ pendingDelete.hora_inicio }} a {{ pendingDelete.hora_fin }}.</p>
      <p class="notice-detail">Esta acción no se puede deshacer.</p>
      <footer class="editor-actions">
        <button type="button" autofocus class="schedule-secondary" :disabled="isDeleting" @click="pendingDelete = null">Cancelar</button>
        <button type="button" class="schedule-primary" :disabled="isDeleting" @click="confirmRemoveSchedule">{{ isDeleting ? 'Eliminando…' : 'Eliminar horario' }}</button>
      </footer>
    </ScheduleModal>
    <ScheduleModal v-if="feedback" :title="feedbackTone === 'error' ? 'No se pudo completar la acción' : 'Todo listo'" @close="feedback = ''">
      <div class="notice-icon" :class="{ 'is-danger': feedbackTone === 'error' }"><CircleAlert v-if="feedbackTone === 'error'" :size="24" /><CircleCheck v-else :size="24" /></div>
      <p class="notice-message" role="status">{{ feedback }}</p>
      <footer class="editor-actions"><button type="button" autofocus class="schedule-primary" @click="feedback = ''">Entendido</button></footer>
    </ScheduleModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { ChevronDown, CircleAlert, CircleCheck, List, Plus, RefreshCw, Search, SlidersHorizontal, Trash2 } from 'lucide-vue-next';
import ScheduleModal from '../components/ScheduleModal.vue';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { dateLabel, limaDate } from '../utils/attendance.js';
import { monthWeeks, scheduleOccurrences, weekStart } from '../utils/scheduleCalendar.js';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const schedules = computed(() => gymStore.serviceSchedules);
const routines = computed(() => gymStore.routines || []);
const showFilters = ref(false);
const showList = ref(false);
const extraFilterCount = computed(() => Number(filters.dia !== 'todos') + Number(filters.estado !== 'todos') + Number(filters.sortBy !== 'servicio-dia-hora'));
const isSaving = ref(false);
const isRefreshing = ref(false);
const today = limaDate();
const visibleRange = ref({ ...monthWeeks(today.slice(0, 7)).find((week) => week.start === weekStart(today)), month: today.slice(0, 7) });
const weeklySchedules = computed(() => {
  const occurrences = new Map(scheduleOccurrences(filteredSchedules.value, visibleRange.value.start, visibleRange.value.month).map((item) => [item.id_horario_servicio, item]));
  return filteredSchedules.value.flatMap((item) => occurrences.has(item.id_horario_servicio) ? [occurrences.get(item.id_horario_servicio)] : []);
});
const isEditorOpen = ref(false);
const feedback = ref('');
const pendingDelete = ref(null);
const isDeleting = ref(false);
const feedbackTone = ref('success');
const showNotification = ({ tone, message }) => {
  feedbackTone.value = tone;
  feedback.value = message;
};

const filters = reactive({
  search: '',
  servicio: 'todos',
  dia: 'todos',
  estado: 'todos',
  sortBy: 'servicio-dia-hora',
});

const days = [
  { value: 'lunes', code: 'LUN', label: 'Lunes' },
  { value: 'martes', code: 'MAR', label: 'Martes' },
  { value: 'miercoles', code: 'MIE', label: 'Miércoles' },
  { value: 'jueves', code: 'JUE', label: 'Jueves' },
  { value: 'viernes', code: 'VIE', label: 'Viernes' },
  { value: 'sabado', code: 'SAB', label: 'Sábado' },
  { value: 'domingo', code: 'DOM', label: 'Domingo' },
];

const serviceFilters = [
  { value: 'todos', label: 'Todos los servicios' },
  { value: 'fitness', label: 'Fitness' },
  { value: 'musculacion', label: 'Musculación' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'baile', label: 'Baile' },
];

const statusFilters = [
  { value: 'todos', label: 'Todos' },
  { value: 'activos', label: 'Activos' },
  { value: 'pausados', label: 'Pausados' },
  { value: 'con-cupos', label: 'Con cupos' },
  { value: 'llenos', label: 'Llenos' },
];

const sortOptions = [
  { value: 'servicio-dia-hora', label: 'Servicio, día y hora' },
  { value: 'dia-hora', label: 'Día y hora' },
  { value: 'cupos-disponibles', label: 'Cupos disponibles' },
  { value: 'estado', label: 'Estado' },
];

/**
 * Gestiona esta acción de la vista.
 */
const defaultForm = () => ({
  id_horario_servicio: null,
  servicio: 'fitness',
  id_rutina: 0,
  dia: 'lunes',
  codigo_dia: 'LUN',
  hora_inicio: '06:00',
  hora_fin: '07:00',
  cupos: 10,
  activo: true,
});

const form = reactive(defaultForm());

/**
 * Normaliza el valor recibido.
 */
const normalizeService = (service) => String(service || '').trim().toLowerCase();
/**
 * Gestiona esta acción de la vista.
 */
const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[normalizeService(service)] || service;
/**
 * Gestiona esta acción de la vista.
 */
const dayLabel = (day) => days.find((entry) => entry.value === day)?.label || day;
/**
 * Gestiona esta acción de la vista.
 */
const dayOrder = (day) => days.findIndex((entry) => entry.value === day);
/**
 * Gestiona esta acción de la vista.
 */
const serviceOrder = (service) => Math.max(0, serviceFilters.findIndex((entry) => entry.value === service) - 1);
const routineById = computed(() =>
  routines.value.reduce((result, routine) => {
    result[Number(routine.id_rutina)] = routine;
    return result;
  }, {}),
);
/**
 * Gestiona esta acción de la vista.
 */
const routineName = (idRutina) => routineById.value[Number(idRutina)]?.nombre_rutina || 'Sin rutina';
/**
 * Gestiona esta acción de la vista.
 */
const routineZones = (idRutina) => routineById.value[Number(idRutina)]?.zonas_musculares || 'Rutina pendiente';
const routinesForSelectedService = computed(() =>
  routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(form.servicio || '').toLowerCase()),
);
/**
 * Valida los datos recibidos.
 */
const isScheduleActive = (schedule) => schedule.activo !== false;
const activeSchedules = computed(() => schedules.value.filter((item) => item.activo !== false).length);
const totalSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos || 0), 0));
const usedSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos_usados || 0), 0));

/**
 * Gestiona esta acción de la vista.
 */
const timeToMinutes = (value) => {
  const [hour = 0, minute = 0] = String(value || '').split(':').map(Number);
  return hour * 60 + minute;
};

/**
 * Gestiona esta acción de la vista.
 */
const availableSlots = (schedule) => Math.max(0, Number(schedule.cupos || 0) - Number(schedule.cupos_usados || 0));

/**
 * Gestiona esta acción de la vista.
 */
const durationLabel = (schedule) => {
  const duration = timeToMinutes(schedule.hora_fin) - timeToMinutes(schedule.hora_inicio);
  if (duration === 60) return 'Duración 1 hora';
  if (duration === 120) return 'Duración 2 horas';
  return `Duración ${Math.max(0, duration)} min`;
};

/**
 * Gestiona esta acción de la vista.
 */
const slotsPercent = (schedule) => {
  const total = Number(schedule.cupos || 0);
  if (!total) return 0;

  const used = Math.min(total, Math.max(0, Number(schedule.cupos_usados || 0)));
  return Math.round((used / total) * 100);
};

const servicePalette = {
  fitness: { background: '#d9f99d', border: '#84cc16' },
  musculacion: { background: '#bfdbfe', border: '#38bdf8' },
  cardio: { background: '#fde68a', border: '#f59e0b' },
  baile: { background: '#fecdd3', border: '#fb7185' },
};

/**
 * Gestiona esta acción de la vista.
 */
const serviceStyle = (service) => {
  const colors = servicePalette[normalizeService(service)] || { background: '#e2e8f0', border: '#94a3b8' };
  return {
    '--schedule-service-bg': colors.background,
    '--schedule-service-border': colors.border,
  };
};

/**
 * Gestiona esta acción de la vista.
 */
const statusClass = (schedule) =>
  isScheduleActive(schedule)
    ? 'schedule-status-active'
    : 'schedule-status-paused';

/**
 * Normaliza el valor recibido.
 */
const normalizeText = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

/**
 * Gestiona esta acción de la vista.
 */
const searchableScheduleText = (schedule) =>
  normalizeText(
    [
      serviceLabel(schedule.servicio),
      routineName(schedule.id_rutina),
      routineZones(schedule.id_rutina),
      dayLabel(schedule.dia),
      schedule.codigo_dia,
      schedule.hora_inicio,
      schedule.hora_fin,
      schedule.cupos,
      isScheduleActive(schedule) ? 'activo' : 'pausado',
    ].join(' '),
  );

/**
 * Gestiona esta acción de la vista.
 */
const matchesStatus = (schedule) => {
  if (filters.estado === 'activos') return schedule.activo !== false;
  if (filters.estado === 'pausados') return schedule.activo === false;
  if (filters.estado === 'con-cupos') return availableSlots(schedule) > 0;
  if (filters.estado === 'llenos') return Number(schedule.cupos || 0) > 0 && availableSlots(schedule) <= 0;
  return true;
};

/**
 * Gestiona esta acción de la vista.
 */
const compareBase = (a, b) => {
  const serviceDiff = serviceOrder(a.servicio) - serviceOrder(b.servicio);
  if (serviceDiff) return serviceDiff;

  const dayDiff = dayOrder(a.dia) - dayOrder(b.dia);
  if (dayDiff) return dayDiff;

  return timeToMinutes(a.hora_inicio) - timeToMinutes(b.hora_inicio);
};

const filteredSchedules = computed(() => {
  const search = normalizeText(filters.search).trim();

  return [...schedules.value]
    .filter((schedule) => {
      const serviceMatch = filters.servicio === 'todos' || schedule.servicio === filters.servicio;
      const dayMatch = filters.dia === 'todos' || schedule.dia === filters.dia;
      const textMatch = !search || searchableScheduleText(schedule).includes(search);

      return serviceMatch && dayMatch && matchesStatus(schedule) && textMatch;
    })
    .sort((a, b) => {
      if (filters.sortBy === 'dia-hora') {
        const dayDiff = dayOrder(a.dia) - dayOrder(b.dia);
        if (dayDiff) return dayDiff;
        const timeDiff = timeToMinutes(a.hora_inicio) - timeToMinutes(b.hora_inicio);
        if (timeDiff) return timeDiff;
        return serviceOrder(a.servicio) - serviceOrder(b.servicio);
      }

      if (filters.sortBy === 'cupos-disponibles') {
        const slotsDiff = availableSlots(b) - availableSlots(a);
        return slotsDiff || compareBase(a, b);
      }

      if (filters.sortBy === 'estado') {
        const stateDiff = Number(b.activo !== false) - Number(a.activo !== false);
        return stateDiff || compareBase(a, b);
      }

      return compareBase(a, b);
    })
    .map((schedule) => ({
      ...schedule,
      rutina_nombre: routineName(schedule.id_rutina),
      zonas_musculares: routineZones(schedule.id_rutina),
    }));
});

/**
 * Valida los datos recibidos.
 */
const hasValidShortDuration = () => {
  const duration = timeToMinutes(form.hora_fin) - timeToMinutes(form.hora_inicio);
  return duration === 60 || duration === 120;
};

watch(
  () => form.dia,
  (day) => {
    if (!form.id_horario_servicio) {
      form.codigo_dia = days.find((entry) => entry.value === day)?.code || form.codigo_dia;
    }
  },
);

watch(
  () => form.servicio,
  () => {
    if (!routinesForSelectedService.value.some((routine) => Number(routine.id_rutina) === Number(form.id_rutina))) {
      form.id_rutina = 0;
    }
  },
);

/**
 * Gestiona esta acción de la vista.
 */
const resetForm = () => {
  Object.assign(form, defaultForm());
};

/**
 * Gestiona esta acción de la vista.
 */
const openNewSchedule = () => {
  resetForm();
  feedback.value = '';
  isEditorOpen.value = true;
};

/**
 * Gestiona esta acción de la vista.
 */
const closeEditor = () => {
  if (isSaving.value) return;
  isEditorOpen.value = false;
  resetForm();
};

/**
 * Gestiona esta acción de la vista.
 */
const resetFilters = () => {
  Object.assign(filters, {
    search: '',
    servicio: 'todos',
    dia: 'todos',
    estado: 'todos',
    sortBy: 'servicio-dia-hora',
  });
};

/**
 * Gestiona esta acción de la vista.
 */
const editSchedule = (schedule) => {
  Object.assign(form, {
    id_horario_servicio: schedule.id_horario_servicio,
    servicio: schedule.servicio || 'fitness',
    id_rutina: Number(schedule.id_rutina || 0),
    dia: schedule.dia || 'lunes',
    codigo_dia: schedule.codigo_dia || 'LUN',
    hora_inicio: String(schedule.hora_inicio || '06:00').slice(0, 5),
    hora_fin: String(schedule.hora_fin || '07:00').slice(0, 5),
    cupos: Number(schedule.cupos || 10),
    activo: schedule.activo !== false,
  });
  feedback.value = '';
  isEditorOpen.value = true;
};

/**
 * Actualiza los datos actuales.
 */
const refreshAll = async (notify = false) => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  try {
    const results = await Promise.allSettled([
      gymStore.refreshRoutinesFromBackend(),
      gymStore.refreshServiceSchedulesFromBackend(),
    ]);
    const failure = results.find((result) => result.status === 'rejected');
    if (failure) throw failure.reason;
    if (notify) showNotification({ tone: 'success', message: 'Los horarios y las rutinas están actualizados.' });
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error.message || 'No se pudieron cargar los horarios.';
  } finally { isRefreshing.value = false; }
};

/**
 * Gestiona esta acción de la vista.
 */
const saveSchedule = async () => {
  if (isSaving.value) return;
  isSaving.value = true;
  feedback.value = '';
  try {
    if (!form.hora_inicio || !form.hora_fin) throw new Error('Completa la hora de inicio y la hora de salida.');
    if (!hasValidShortDuration()) {
      throw new Error('El horario debe durar exactamente 1 o 2 horas.');
    }
    if (!Number(form.id_rutina || 0)) {
      throw new Error('Selecciona una rutina para este servicio.');
    }
    if (!Number.isInteger(form.cupos) || form.cupos < 1) throw new Error('Ingresa un número entero de cupos mayor que cero.');
    if (!form.codigo_dia.trim()) throw new Error('Ingresa el código del día.');
    await gymStore.upsertServiceSchedule({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Horario guardado.';
    isEditorOpen.value = false;
    resetForm();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar el horario.';
  } finally {
    isSaving.value = false;
  }
};

/**
 * Elimina el registro indicado.
 */
const removeSchedule = (schedule) => { pendingDelete.value = schedule; };
const confirmRemoveSchedule = async () => {
  if (isDeleting.value || !pendingDelete.value) return;
  const schedule = pendingDelete.value;
  isDeleting.value = true;
  try {
    await gymStore.deleteServiceSchedule(schedule.id_horario_servicio);
    feedbackTone.value = 'success';
    feedback.value = 'Horario eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar el horario.';
  } finally {
    isDeleting.value = false;
    pendingDelete.value = null;
  }
};

onMounted(() => refreshAll());
</script>

<style scoped>
.schedule-admin { color: var(--app-text); min-width: 0; }
.schedule-page-header { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 8px 0 12px; }
.schedule-eyebrow { margin: 0 0 8px; color: var(--app-accent-text); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; font-weight: 750; }
.schedule-page-header h1 { margin: 0; font-size: clamp(24px, 2.5vw, 32px); letter-spacing: -.035em; font-weight: 800; }
.schedule-description { margin: 8px 0 0; font-size: 13px; color: var(--app-text-muted); }
.schedule-page-actions, .schedule-search-actions, .schedule-toolbar { display: flex; align-items: center; gap: 10px; }
.schedule-primary, .schedule-secondary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 10px 15px; border-radius: 9px; font: inherit; font-size: 12px; font-weight: 650; cursor: pointer; white-space: nowrap; }
.schedule-primary { background: var(--app-accent); color: white; box-shadow: 0 4px 10px #dc262620; }
.schedule-primary:hover { background: var(--app-accent-hover); }
.schedule-secondary { border: 1px solid var(--app-border); background: var(--app-surface); color: var(--app-text-soft); }
.schedule-secondary:hover, .schedule-secondary[aria-expanded="true"] { border-color: var(--app-border-strong); color: var(--app-accent-text); }
.schedule-workspace { min-width: 0; }
.schedule-toolbar { justify-content: space-between; padding-bottom: 18px; gap: 20px; }
.schedule-metrics { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; font-size: 12px; color: var(--app-text-muted); }
.schedule-metrics > span { padding: 12px 16px; border: 1px solid var(--app-border); border-radius: 12px; background: var(--app-surface); }
.schedule-checkbox { accent-color: var(--app-accent); }
.schedule-metrics strong { color: var(--app-text); font-size: 14px; font-weight: 750; padding-right: 5px; }
.schedule-search { display: flex; align-items: center; gap: 9px; padding: 10px 12px; border: 1px solid var(--app-border); border-radius: 9px; background: var(--app-input); color: var(--app-text-muted); }
.schedule-search input { width: 175px; min-width: 0; outline: none; background: transparent; color: var(--app-text); font-size: 12px; }
.service-tabs { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 18px; scrollbar-width: thin; }
.service-tabs button { display: inline-flex; flex-shrink: 0; align-items: center; gap: 7px; min-height: 44px; padding: 8px 12px; border: 1px solid var(--app-border); border-radius: 8px; background: var(--app-surface); color: var(--app-text-muted); font-size: 12px; font-weight: 650; cursor: pointer; }
.service-tabs button[aria-pressed="true"] { border-color: var(--app-border-strong); background: var(--app-accent-soft); color: var(--app-accent-text); }
.service-tab-dot { height: 6px; width: 6px; border-radius: 50%; }
.service-tab-count { opacity: .6; font-size: 11px; }
.schedule-extra-filters { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; padding: 16px; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: 12px; }
.schedule-extra-filters label { display: flex; flex: 1; flex-direction: column; gap: 7px; min-width: 140px; font-size: 12px; color: var(--app-text-muted); }
.schedule-extra-filters select { border: 1px solid var(--app-border); border-radius: 8px; min-height: 44px; padding: 8px 10px; background: var(--app-input); color: var(--app-text); font-size: 12px; }
.filter-count { display: grid; place-items: center; width: 17px; height: 17px; border-radius: 50%; background: var(--app-accent); color: white; font-size: 11px; }
.schedule-list-section { border: 1px solid var(--app-border); border-radius: 12px; padding: 0 16px; background: var(--app-surface); }
.schedule-list-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; padding: 17px 0; color: var(--app-text-soft); cursor: pointer; }
.schedule-list-toggle > span { display: flex; align-items: center; gap: 10px; }
.schedule-list-toggle strong { font-size: 12px; font-weight: 650; }
.schedule-list-toggle span span { color: var(--app-text-muted); font-size: 12px; }
#schedule-list { padding-bottom: 16px; }
button:focus-visible, .schedule-search:focus-within { outline: 2px solid var(--app-accent); outline-offset: 3px; }
@media (max-width: 1000px) { .schedule-page-header { align-items: flex-start; flex-direction: column; gap: 16px; } .schedule-toolbar { flex-wrap: wrap; } }
@media (max-width: 720px) {
  .schedule-page-header { padding-top: 0; }
  .schedule-page-actions { width: 100%; }
  .schedule-page-actions > button { flex: 1; }
  .schedule-search-actions { width: 100%; }
  .schedule-search { flex: 1; min-width: 0; }
  .schedule-search input { width: 100%; }
  .schedule-metrics { gap: 16px; }
  .schedule-list-toggle > span { flex-wrap: wrap; }
  .schedule-list-toggle span span { display: none; }
}

.field-input {
  width: 100%;
  border: 1px solid var(--app-border);
  border-radius: 1rem;
  background: var(--app-input);
  padding: 0.75rem 1rem;
  color: var(--app-text);
  outline: none;
}

.field-input::placeholder {
  color: #64748b;
}

.schedule-service-accent,
.schedule-service-progress {
  background: var(--schedule-service-border);
}

.schedule-service-progress {
  box-shadow: 0 0 12px color-mix(in srgb, var(--schedule-service-border) 45%, transparent);
}

.schedule-service-badge {
  border: 1px solid var(--schedule-service-border);
  background: var(--schedule-service-bg);
  color: #17324d;
}
.schedule-text { color: var(--app-text); }
.schedule-soft { color: var(--app-text-soft); }
.schedule-muted { color: var(--app-text-muted); }
.schedule-danger { color: var(--app-accent-text); }
.schedule-surface { background: var(--app-surface); }
.schedule-inset { background: var(--app-input); }
.schedule-border, .schedule-dividers > * { border-color: var(--app-border); }
.schedule-track { background: var(--app-border); }
#schedule-list button { min-height: 44px; }
.schedule-row:hover { background: var(--app-surface-soft); }
.schedule-status-active { background: #dcfce7; color: #166534; }
.schedule-status-paused { background: var(--app-surface-strong); color: var(--app-text-soft); border: 1px solid var(--app-border); }
.editor-intro, .notice-detail { color: var(--app-text-muted); font-size: 14px; line-height: 1.6; }
.schedule-editor label { display: block; }
.schedule-editor label:has(input[type="checkbox"]) { display: flex; }
.schedule-editor .field-input { min-height: 46px; border-radius: 10px; }
.field-input:focus-visible { outline: 2px solid var(--app-accent); outline-offset: 2px; }
.editor-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--app-border); }
.notice-message { font-size: 15px; line-height: 1.7; overflow-wrap: anywhere; color: var(--app-text); }
.notice-icon { display: grid; place-items: center; width: 48px; height: 48px; margin-bottom: 16px; border-radius: 14px; background: #dcfce7; color: #166534; }
.notice-icon.is-danger { background: var(--app-accent-soft); color: var(--app-accent-text); }
button:disabled { opacity: .55; cursor: wait; }
@media (max-width: 480px) { .editor-actions > button { flex: 1; white-space: normal; } }
</style>
