<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Rutina</p>
          <h1 class="mt-2 text-3xl font-black text-white">Supervision de rutinas</h1>
          <p class="mt-2 text-slate-300">Consulta rutinas asignadas y zonas musculares trabajadas por cliente.</p>
        </div>
        <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white" @click="refresh">
          Actualizar
        </button>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catalogo</p>
        <h2 class="mt-2 text-2xl font-black text-white">Implementar rutina</h2>

        <form class="mt-5 space-y-3" @submit.prevent="saveRoutine">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Servicio</span>
            <select v-model="routineForm.servicio" class="field-input">
              <option v-for="service in serviceOptions" :key="service.value" :value="service.value">{{ service.label }}</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="routineForm.nombre_rutina" class="field-input" placeholder="Rutina base de fuerza" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Zonas musculares</span>
            <textarea v-model="routineForm.zonas_musculares" class="field-input min-h-24" placeholder="Pierna, gluteos, core..." />
          </label>
          <button class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 disabled:opacity-60" :disabled="isSaving">
            {{ isSaving ? 'Guardando...' : 'Guardar rutina' }}
          </button>
        </form>

        <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
          {{ feedback }}
        </p>

        <h3 class="mt-8 text-lg font-black text-white">Rutinas disponibles</h3>

        <div class="mt-5 space-y-3">
          <article v-for="routine in routines" :key="routine.id_rutina" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="font-bold text-white">{{ routine.nombre_rutina || 'Rutina' }}</p>
                <p class="mt-1 text-xs uppercase tracking-[0.22em] text-cyan-200">{{ serviceLabel(routine.servicio) }}</p>
                <p class="mt-1 text-sm text-slate-400">{{ routine.zonas_musculares || 'Sin zonas registradas' }}</p>
              </div>
              <span class="rounded-full bg-cyan-400/10 px-3 py-1 text-sm font-bold text-cyan-100">
                {{ routine.clientes_asignados || 0 }}
              </span>
            </div>
          </article>
        </div>

        <p v-if="!routines.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
          No hay rutinas registradas.
        </p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Servicios</p>
        <h2 class="mt-2 text-2xl font-black text-white">4 servicios</h2>
        <div class="mt-5 grid gap-3">
          <article v-for="service in serviceOptions" :key="service.value" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex items-center justify-between gap-3">
              <p class="font-bold text-white">{{ service.label }}</p>
              <span class="rounded-full bg-cyan-400/10 px-3 py-1 text-sm font-bold text-cyan-100">{{ routinesForService(service.value).length }}</span>
            </div>
          </article>
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
  { value: 'musculacion', label: 'Musculacion' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'baile', label: 'Baile' },
];

const routineForm = reactive({
  servicio: 'fitness',
  nombre_rutina: '',
  zonas_musculares: '',
  color: 'Azul',
});

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());

const resetRoutineForm = () => {
  routineForm.nombre_rutina = '';
  routineForm.zonas_musculares = '';
  routineForm.color = 'Azul';
};

const saveRoutine = async () => {
  try {
    isSaving.value = true;
    feedback.value = '';
    await gymStore.upsertTrainerRoutine({ ...routineForm });
    feedbackTone.value = 'success';
    feedback.value = 'Rutina guardada.';
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
