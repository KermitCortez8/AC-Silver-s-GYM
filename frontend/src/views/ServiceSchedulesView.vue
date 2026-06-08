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

      <div class="mt-5">
        <ExcelScheduleGrid
          title="Horario"
          subtitle="Para ver el detalle del servicio, presione sobre el bloque del horario"
          :items="schedules"
          file-name="horarios-servicio.xlsx"
        />
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Tabla</p>
          <h2 class="mt-2 text-2xl font-black text-white">Horarios disponibles</h2>
        </div>
        <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
          {{ feedback }}
        </p>
      </div>

      <div class="mt-5 overflow-x-auto">
        <table class="w-full min-w-[900px] border-separate border-spacing-y-3 text-left">
          <thead class="text-xs uppercase tracking-[0.25em] text-slate-500">
            <tr>
              <th class="px-4">Servicio</th>
              <th class="px-4">Dia</th>
              <th class="px-4">Codigo</th>
              <th class="px-4">Horario</th>
              <th class="px-4">Cupos</th>
              <th class="px-4">Estado</th>
              <th class="px-4 text-right">Accion</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="schedule in schedules" :key="schedule.id_horario_servicio" class="bg-slate-900/80">
              <td class="rounded-l-2xl px-4 py-4 font-bold text-white">{{ serviceLabel(schedule.servicio) }}</td>
              <td class="px-4 py-4 text-slate-300">{{ dayLabel(schedule.dia) }}</td>
              <td class="px-4 py-4 text-cyan-200">{{ schedule.codigo_dia }}</td>
              <td class="px-4 py-4 text-slate-300">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</td>
              <td class="px-4 py-4 text-slate-300">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</td>
              <td class="px-4 py-4">
                <span class="rounded-full px-3 py-1 text-xs font-bold" :class="schedule.activo ? 'bg-emerald-400/15 text-emerald-100' : 'bg-slate-700 text-slate-300'">
                  {{ schedule.activo ? 'Activo' : 'Pausado' }}
                </span>
              </td>
              <td class="rounded-r-2xl px-4 py-4 text-right">
                <button class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="editSchedule(schedule)">Editar</button>
                <button class="ml-2 rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 hover:bg-rose-400/10" @click="removeSchedule(schedule)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!schedules.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
        No hay horarios para mostrar.
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

const days = [
  { value: 'lunes', code: 'LUN', label: 'Lunes' },
  { value: 'martes', code: 'MAR', label: 'Martes' },
  { value: 'miercoles', code: 'MIE', label: 'Miercoles' },
  { value: 'jueves', code: 'JUE', label: 'Jueves' },
  { value: 'viernes', code: 'VIE', label: 'Viernes' },
  { value: 'sabado', code: 'SAB', label: 'Sabado' },
  { value: 'domingo', code: 'DOM', label: 'Domingo' },
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

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service;
const dayLabel = (day) => days.find((entry) => entry.value === day)?.label || day;
const activeSchedules = computed(() => schedules.value.filter((item) => item.activo !== false).length);
const totalSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos || 0), 0));
const usedSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos_usados || 0), 0));

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
</style>
