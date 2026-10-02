<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Rutina</p>
          <h1 class="mt-2 text-3xl font-black text-white">Supervisión de rutinas</h1>
          <p class="mt-2 text-slate-300">Diseña rutinas con lista de ejercicios (series, repeticiones, descanso) y asigna zonas musculares.</p>
        </div>
        <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white transition hover:bg-slate-800" @click="refresh">
          Actualizar
        </button>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catálogo</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ routineForm.id_rutina ? 'Editar rutina' : 'Crear nueva rutina' }}</h2>

        <form class="mt-5 space-y-4" @submit.prevent="saveRoutine">
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Servicio</span>
              <select v-model="routineForm.servicio" class="field-input">
                <option v-for="service in serviceOptions" :key="service.value" :value="service.value">{{ service.label }}</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Nombre de la rutina</span>
              <input v-model="routineForm.nombre_rutina" class="field-input" placeholder="Ej. Rutina Fuerza Hipertrofia" required />
            </label>
          </div>

          <label class="block space-y-2">
            <span class="text-sm text-slate-300">Zonas musculares trabajadas</span>
            <input v-model="routineForm.zonas_musculares" class="field-input" placeholder="Pierna, glúteos, pectoral, core..." />
          </label>

          <!-- Constructor dinámico de ejercicios -->
          <div class="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <div class="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
              <div>
                <h3 class="font-bold text-cyan-200">Lista de ejercicios</h3>
                <p class="text-xs text-slate-400">Define series, repeticiones y descansos de la rutina.</p>
              </div>
              <button type="button" class="rounded-xl bg-cyan-400/10 px-3 py-1.5 text-xs font-bold text-cyan-200 hover:bg-cyan-400/20" @click="addExercise">
                + Agregar ejercicio
              </button>
            </div>

            <div v-if="routineForm.ejercicios.length" class="mt-3 space-y-3">
              <div v-for="(ex, index) in routineForm.ejercicios" :key="index" class="rounded-xl border border-white/10 bg-slate-900/90 p-3 space-y-2">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-bold text-cyan-400">#{{ index + 1 }}</span>
                  <button type="button" class="text-xs text-rose-400 hover:underline" @click="removeExercise(index)">
                    Eliminar
                  </button>
                </div>
                <div class="grid gap-2 sm:grid-cols-2">
                  <input v-model="ex.nombre_ejercicio" class="field-input text-sm" placeholder="Nombre del ejercicio (ej. Sentadilla)" required />
                  <input v-model="ex.grupo_muscular" class="field-input text-sm" placeholder="Músculo objetivo (opcional)" />
                </div>
                <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <label class="text-xs text-slate-300">
                    Series
                    <input v-model.number="ex.series" type="number" min="1" max="20" class="field-input mt-1 text-sm" />
                  </label>
                  <label class="text-xs text-slate-300">
                    Repeticiones
                    <input v-model="ex.repeticiones" class="field-input mt-1 text-sm" placeholder="10-12" />
                  </label>
                  <label class="text-xs text-slate-300">
                    Descanso
                    <select v-model.number="ex.descanso_segundos" class="field-input mt-1 text-sm">
                      <option :value="30">30 seg</option>
                      <option :value="45">45 seg</option>
                      <option :value="60">60 seg (1 min)</option>
                      <option :value="90">90 seg (1.5 min)</option>
                      <option :value="120">120 seg (2 min)</option>
                      <option :value="180">180 seg (3 min)</option>
                    </select>
                  </label>
                  <label class="text-xs text-slate-300">
                    Peso sug. (kg)
                    <input v-model.number="ex.peso_sugerido_kg" type="number" step="0.5" min="0" class="field-input mt-1 text-sm" placeholder="Opcional" />
                  </label>
                </div>
              </div>
            </div>

            <p v-else class="mt-3 text-center text-xs text-slate-400 py-3">
              No has agregado ejercicios a esta rutina aún. Haz clic en "+ Agregar ejercicio".
            </p>
          </div>

          <div class="flex gap-3">
            <button class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition disabled:opacity-60 hover:bg-cyan-300" :disabled="isSaving">
              {{ isSaving ? 'Guardando...' : (routineForm.id_rutina ? 'Actualizar rutina' : 'Guardar rutina') }}
            </button>
            <button v-if="routineForm.id_rutina" type="button" class="rounded-2xl border border-white/10 bg-slate-800 px-4 py-3 text-sm font-bold text-white hover:bg-slate-700" @click="resetRoutineForm">
              Cancelar
            </button>
          </div>
        </form>

        <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
          {{ feedback }}
        </p>
      </div>

      <div class="space-y-6">
        <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catálogo general</p>
          <h3 class="mt-1 text-xl font-black text-white">Rutinas registradas</h3>

          <div class="mt-4 space-y-3 max-h-[600px] overflow-y-auto pr-1">
            <article v-for="routine in routines" :key="routine.id_rutina" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4 space-y-3">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="font-bold text-white text-lg">{{ routine.nombre_rutina || 'Rutina sin nombre' }}</p>
                  <p class="mt-1 text-xs uppercase tracking-[0.22em] text-cyan-200">{{ serviceLabel(routine.servicio) }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ routine.zonas_musculares || 'Sin zonas registradas' }}</p>
                </div>
                <span class="rounded-full bg-cyan-400/10 px-3 py-1 text-xs font-bold text-cyan-100">
                  {{ (routine.ejercicios || []).length }} ejercicios
                </span>
              </div>

              <!-- Desglose de ejercicios -->
              <div v-if="(routine.ejercicios || []).length" class="space-y-1.5 border-t border-white/10 pt-2">
                <div v-for="(ex, idx) in routine.ejercicios" :key="idx" class="flex flex-wrap items-center justify-between text-xs text-slate-300 rounded bg-slate-950/60 px-2 py-1.5">
                  <span class="font-semibold text-cyan-100">{{ ex.nombre_ejercicio }}</span>
                  <span class="text-slate-400">{{ ex.series }} series × {{ ex.repeticiones }} (Descanso {{ ex.descanso_segundos || 60 }}s)</span>
                </div>
              </div>

              <button class="w-full rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/10 transition" @click="editRoutine(routine)">
                Editar rutina
              </button>
            </article>

            <p v-if="!routines.length" class="rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
              No hay rutinas registradas en el catálogo.
            </p>
          </div>
        </div>

        <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Distribución por Servicio</p>
          <div class="mt-4 grid gap-2 sm:grid-cols-2">
            <article v-for="service in serviceOptions" :key="service.value" class="rounded-xl border border-white/10 bg-slate-900/80 p-3">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-bold text-white">{{ service.label }}</p>
                <span class="rounded-full bg-cyan-400/10 px-2.5 py-0.5 text-xs font-bold text-cyan-100">
                  {{ routinesForService(service.value).length }}
                </span>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const errorMessage = ref('');
const feedback = ref('');
const feedbackTone = ref('success');
const isSaving = ref(false);

const serviceOptions = [
  { value: 'fitness', label: 'Fitness' },
  { value: 'musculacion', label: 'Musculación' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'baile', label: 'Baile' },
];

const routineForm = reactive({
  id_rutina: null,
  servicio: 'fitness',
  nombre_rutina: '',
  zonas_musculares: '',
  color: 'Azul',
  ejercicios: [],
});

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());

const addExercise = () => {
  routineForm.ejercicios.push({
    nombre_ejercicio: '',
    series: 3,
    repeticiones: '10-12',
    descanso_segundos: 60,
    peso_sugerido_kg: null,
    grupo_muscular: '',
    notas: '',
  });
};

const removeExercise = (index) => {
  routineForm.ejercicios.splice(index, 1);
};

const resetRoutineForm = () => {
  routineForm.id_rutina = null;
  routineForm.servicio = 'fitness';
  routineForm.nombre_rutina = '';
  routineForm.zonas_musculares = '';
  routineForm.color = 'Azul';
  routineForm.ejercicios = [];
};

const editRoutine = (routine) => {
  routineForm.id_rutina = routine.id_rutina;
  routineForm.servicio = routine.servicio || 'fitness';
  routineForm.nombre_rutina = routine.nombre_rutina || '';
  routineForm.zonas_musculares = routine.zonas_musculares || '';
  routineForm.color = routine.color || 'Azul';
  routineForm.ejercicios = Array.isArray(routine.ejercicios) ? routine.ejercicios.map((ex) => ({ ...ex })) : [];
};

const saveRoutine = async () => {
  try {
    isSaving.value = true;
    feedback.value = '';
    await gymStore.upsertTrainerRoutine({ ...routineForm });
    feedbackTone.value = 'success';
    feedback.value = 'Rutina guardada exitosamente.';
    resetRoutineForm();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la rutina.';
  } finally {
    isSaving.value = false;
  }
};

const refresh = async () => {
  try {
    errorMessage.value = '';
    await gymStore.fetchTrainerOverview();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'No se pudo cargar rutinas.';
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

