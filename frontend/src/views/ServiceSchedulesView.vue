<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Horarios</p>
          <h1 class="mt-2 text-3xl font-black text-white">Horarios por servicio</h1>
          <p class="mt-2 text-slate-300">Define dia, rango horario y cupos desde una vista superpuesta.</p>
        </div>
        <div class="flex flex-col gap-3 sm:flex-row">
          <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white" @click="refresh">
            Actualizar
          </button>
          <button class="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950" @click="openNewSchedule">
            Nuevo horario
          </button>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Calendario</p>
          <h2 class="mt-2 text-2xl font-black text-white">Tabla semanal</h2>
        </div>
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Horarios</p>
            <p class="text-xl font-black text-white">{{ schedules.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Activos</p>
            <p class="text-xl font-black text-white">{{ activeSchedules }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Cupos</p>
            <p class="text-xl font-black text-white">{{ usedSlots }} / {{ totalSlots }}</p>
          </div>
        </div>
      </div>

      <div class="mt-5 grid gap-3 lg:grid-cols-[1.2fr_0.9fr_0.9fr_1fr]">
        <label class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Buscar</span>
          <input v-model="filters.search" class="field-input" placeholder="Servicio, codigo u hora" />
        </label>

        <label class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Servicio</span>
          <select v-model="filters.servicio" class="field-input">
            <option v-for="service in serviceFilters" :key="service.value" :value="service.value">{{ service.label }}</option>
          </select>
        </label>

        <label class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Dia</span>
          <select v-model="filters.dia" class="field-input">
            <option value="todos">Todos los dias</option>
            <option v-for="day in days" :key="day.value" :value="day.value">{{ day.label }}</option>
          </select>
        </label>

        <label class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Ordenar</span>
          <select v-model="filters.sortBy" class="field-input">
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
      </div>

      <div class="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="status in statusFilters"
            :key="status.value"
            type="button"
            class="rounded-full border px-4 py-2 text-sm font-bold transition"
            :class="filters.estado === status.value ? 'border-amber-300 bg-amber-300 text-slate-950' : 'border-white/10 bg-slate-900/70 text-slate-200 hover:bg-white/10'"
            @click="filters.estado = status.value"
          >
            {{ status.label }}
          </button>
        </div>

        <button type="button" class="rounded-full border border-white/10 px-4 py-2 text-sm font-bold text-slate-200 hover:bg-white/10" @click="resetFilters">
          Limpiar filtros
        </button>
      </div>

      <div class="mt-5">
        <ExcelScheduleGrid
          title="Horario"
          subtitle="Para ver el detalle del servicio, presione sobre el bloque del horario"
          :items="filteredSchedules"
          file-name="horarios-servicio.xlsx"
        />
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Tabla</p>
          <h2 class="mt-2 text-2xl font-black text-white">Horarios disponibles</h2>
          <p class="mt-1 text-sm text-slate-400">{{ filteredSchedules.length }} de {{ schedules.length }} horarios visibles</p>
        </div>
        <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
          {{ feedback }}
        </p>
      </div>

      <div v-if="filteredSchedules.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-950/45 shadow-xl shadow-black/10">
        <div class="hidden overflow-x-auto lg:block">
          <table class="w-full min-w-[980px] text-left text-sm">
            <thead class="sticky top-0 z-10 bg-slate-950/95 text-[11px] uppercase tracking-[0.22em] text-slate-400">
              <tr>
                <th class="px-5 py-4">Servicio</th>
                <th class="px-5 py-4">Dia</th>
                <th class="px-5 py-4">Horario</th>
                <th class="px-5 py-4">Cupos</th>
                <th class="px-5 py-4">Estado</th>
                <th class="px-5 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr
                v-for="schedule in filteredSchedules"
                :key="schedule.id_horario_servicio"
                class="group bg-slate-900/45 transition hover:bg-slate-800/80"
                :style="serviceStyle(schedule.servicio)"
              >
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <span class="schedule-service-accent h-10 w-1.5 rounded-full"></span>
                    <div class="min-w-0">
                      <p class="truncate font-black text-white">{{ serviceLabel(schedule.servicio) }}</p>
                      <p class="mt-1 text-xs text-slate-500">Horario #{{ schedule.id_horario_servicio }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4">
                  <p class="font-bold text-slate-200">{{ dayLabel(schedule.dia) }}</p>
                  <span class="schedule-service-badge mt-1 inline-flex rounded-full px-2.5 py-1 text-xs font-black">
                    {{ schedule.codigo_dia }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <p class="font-black text-white">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ durationLabel(schedule) }}</p>
                </td>
                <td class="px-5 py-4">
                  <div class="max-w-[220px]">
                    <div class="flex items-center justify-between gap-3 text-xs">
                      <span class="font-bold text-slate-200">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</span>
                      <span class="text-slate-500">{{ availableSlots(schedule) }} libres</span>
                    </div>
                    <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
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
                    <button class="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/10" @click="editSchedule(schedule)">Editar</button>
                    <button class="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm font-bold text-rose-100 transition hover:bg-rose-400/10" @click="removeSchedule(schedule)">Eliminar</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="grid gap-3 p-3 lg:hidden">
          <article
            v-for="schedule in filteredSchedules"
            :key="`mobile-${schedule.id_horario_servicio}`"
            class="rounded-2xl border border-white/10 bg-slate-900/70 p-4"
            :style="serviceStyle(schedule.servicio)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 items-center gap-3">
                <span class="schedule-service-accent h-11 w-1.5 rounded-full"></span>
                <div class="min-w-0">
                  <p class="truncate text-base font-black text-white">{{ serviceLabel(schedule.servicio) }}</p>
                  <p class="mt-1 text-xs text-slate-500">
                    {{ dayLabel(schedule.dia) }}
                    <span class="schedule-service-badge ml-1 inline-flex rounded-full px-2 py-0.5 font-black">{{ schedule.codigo_dia }}</span>
                  </p>
                </div>
              </div>
              <span class="shrink-0 rounded-full px-3 py-1 text-xs font-black" :class="statusClass(schedule)">
                {{ isScheduleActive(schedule) ? 'Activo' : 'Pausado' }}
              </span>
            </div>

            <div class="mt-4 grid gap-3 rounded-2xl border border-white/10 bg-slate-950/40 p-3 text-sm sm:grid-cols-2">
              <div>
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Horario</p>
                <p class="mt-1 font-black text-white">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</p>
                <p class="text-xs text-slate-500">{{ durationLabel(schedule) }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Cupos</p>
                <p class="mt-1 font-black text-white">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</p>
                <p class="text-xs text-slate-500">{{ availableSlots(schedule) }} libres</p>
              </div>
            </div>

            <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
              <div class="schedule-service-progress h-full rounded-full" :style="{ width: `${slotsPercent(schedule)}%` }"></div>
            </div>

            <div class="mt-4 grid grid-cols-2 gap-2">
              <button class="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-bold text-white" @click="editSchedule(schedule)">Editar</button>
              <button class="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm font-bold text-rose-100" @click="removeSchedule(schedule)">Eliminar</button>
            </div>
          </article>
        </div>
      </div>

      <p v-if="!filteredSchedules.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
        No hay horarios para mostrar con los filtros actuales.
      </p>
    </section>

    <Teleport to="body">
      <div v-if="isEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <form class="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl" @submit.prevent="saveSchedule">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ form.id_horario_servicio ? 'Editar' : 'Nuevo' }}</p>
              <h2 class="mt-2 text-2xl font-black text-white">Horario</h2>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeEditor">
              Cerrar
            </button>
          </div>

          <div class="mt-6 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Servicio</span>
              <select v-model="form.servicio" class="field-input">
                <option value="fitness">Fitness</option>
                <option value="musculacion">Musculacion</option>
                <option value="cardio">Cardio</option>
                <option value="baile">Baile</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm text-slate-300">Dia</span>
              <select v-model="form.dia" class="field-input">
                <option v-for="day in days" :key="day.value" :value="day.value">{{ day.label }}</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm text-slate-300">Codigo dia</span>
              <input v-model="form.codigo_dia" class="field-input" placeholder="LUN" />
            </label>

            <label class="space-y-2">
              <span class="text-sm text-slate-300">Cupos</span>
              <input v-model.number="form.cupos" type="number" min="1" class="field-input" />
            </label>

            <label class="space-y-2">
              <span class="text-sm text-slate-300">Hora de inicio</span>
              <input v-model="form.hora_inicio" type="time" class="field-input" />
            </label>

            <label class="space-y-2">
              <span class="text-sm text-slate-300">Hora de salida</span>
              <input v-model="form.hora_fin" type="time" class="field-input" />
            </label>
          </div>

          <p class="mt-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-50">
            Los horarios disponibles deben durar exactamente 1 o 2 horas.
          </p>

          <label class="mt-5 flex items-center gap-3 text-sm font-bold text-slate-200">
            <input v-model="form.activo" type="checkbox" class="h-4 w-4 accent-cyan-400" />
            Activo para matricula
          </label>

          <button type="submit" class="mt-6 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60" :disabled="isSaving">
            {{ isSaving ? 'Guardando...' : 'Guardar horario' }}
          </button>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const schedules = computed(() => gymStore.serviceSchedules);
const isSaving = ref(false);
const isEditorOpen = ref(false);
const feedback = ref('');
const feedbackTone = ref('success');

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
  { value: 'miercoles', code: 'MIE', label: 'Miercoles' },
  { value: 'jueves', code: 'JUE', label: 'Jueves' },
  { value: 'viernes', code: 'VIE', label: 'Viernes' },
  { value: 'sabado', code: 'SAB', label: 'Sabado' },
  { value: 'domingo', code: 'DOM', label: 'Domingo' },
];

const serviceFilters = [
  { value: 'todos', label: 'Todos los servicios' },
  { value: 'fitness', label: 'Fitness' },
  { value: 'musculacion', label: 'Musculacion' },
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
  { value: 'servicio-dia-hora', label: 'Servicio, dia y hora' },
  { value: 'dia-hora', label: 'Dia y hora' },
  { value: 'cupos-disponibles', label: 'Cupos disponibles' },
  { value: 'estado', label: 'Estado' },
];

const defaultForm = () => ({
  id_horario_servicio: null,
  servicio: 'fitness',
  dia: 'lunes',
  codigo_dia: 'LUN',
  hora_inicio: '06:00',
  hora_fin: '07:00',
  cupos: 10,
  activo: true,
});

const form = reactive(defaultForm());

const normalizeService = (service) => String(service || '').trim().toLowerCase();
const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[normalizeService(service)] || service;
const dayLabel = (day) => days.find((entry) => entry.value === day)?.label || day;
const dayOrder = (day) => days.findIndex((entry) => entry.value === day);
const serviceOrder = (service) => Math.max(0, serviceFilters.findIndex((entry) => entry.value === service) - 1);
const isScheduleActive = (schedule) => schedule.activo !== false;
const activeSchedules = computed(() => schedules.value.filter((item) => item.activo !== false).length);
const totalSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos || 0), 0));
const usedSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos_usados || 0), 0));

const timeToMinutes = (value) => {
  const [hour = 0, minute = 0] = String(value || '').split(':').map(Number);
  return hour * 60 + minute;
};

const availableSlots = (schedule) => Math.max(0, Number(schedule.cupos || 0) - Number(schedule.cupos_usados || 0));

const durationLabel = (schedule) => {
  const duration = timeToMinutes(schedule.hora_fin) - timeToMinutes(schedule.hora_inicio);
  if (duration === 60) return 'Duracion 1 hora';
  if (duration === 120) return 'Duracion 2 horas';
  return `Duracion ${Math.max(0, duration)} min`;
};

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

const serviceStyle = (service) => {
  const colors = servicePalette[normalizeService(service)] || { background: '#e2e8f0', border: '#94a3b8' };
  return {
    '--schedule-service-bg': colors.background,
    '--schedule-service-border': colors.border,
  };
};

const statusClass = (schedule) =>
  isScheduleActive(schedule)
    ? 'bg-emerald-400/15 text-emerald-100 ring-1 ring-emerald-300/20'
    : 'bg-slate-700/80 text-slate-300 ring-1 ring-white/10';

const normalizeText = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

const searchableScheduleText = (schedule) =>
  normalizeText(
    [
      serviceLabel(schedule.servicio),
      dayLabel(schedule.dia),
      schedule.codigo_dia,
      schedule.hora_inicio,
      schedule.hora_fin,
      schedule.cupos,
      isScheduleActive(schedule) ? 'activo' : 'pausado',
    ].join(' '),
  );

const matchesStatus = (schedule) => {
  if (filters.estado === 'activos') return schedule.activo !== false;
  if (filters.estado === 'pausados') return schedule.activo === false;
  if (filters.estado === 'con-cupos') return availableSlots(schedule) > 0;
  if (filters.estado === 'llenos') return Number(schedule.cupos || 0) > 0 && availableSlots(schedule) <= 0;
  return true;
};

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
    });
});

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

const resetForm = () => {
  Object.assign(form, defaultForm());
};

const openNewSchedule = () => {
  resetForm();
  feedback.value = '';
  isEditorOpen.value = true;
};

const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

const resetFilters = () => {
  Object.assign(filters, {
    search: '',
    servicio: 'todos',
    dia: 'todos',
    estado: 'todos',
    sortBy: 'servicio-dia-hora',
  });
};

const editSchedule = (schedule) => {
  Object.assign(form, {
    id_horario_servicio: schedule.id_horario_servicio,
    servicio: schedule.servicio || 'fitness',
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

const refresh = () => gymStore.refreshServiceSchedulesFromBackend?.().catch(() => {});

const saveSchedule = async () => {
  isSaving.value = true;
  feedback.value = '';
  try {
    if (!hasValidShortDuration()) {
      throw new Error('El horario debe durar exactamente 1 o 2 horas.');
    }
    await gymStore.upsertServiceSchedule(form);
    feedbackTone.value = 'success';
    feedback.value = 'Horario guardado.';
    closeEditor();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar el horario.';
  } finally {
    isSaving.value = false;
  }
};

const removeSchedule = async (schedule) => {
  if (!window.confirm('Eliminar este horario?')) return;
  try {
    await gymStore.deleteServiceSchedule(schedule.id_horario_servicio);
    feedbackTone.value = 'success';
    feedback.value = 'Horario eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar el horario.';
  }
};

onMounted(refresh);
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  background: rgba(2, 6, 23, 0.72);
  padding: 0.75rem 1rem;
  color: white;
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
</style>
