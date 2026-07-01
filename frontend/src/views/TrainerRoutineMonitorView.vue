<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Monitoreo</p>
          <h1 class="mt-2 text-3xl font-black text-white">Rutinas del cliente</h1>
          <p class="mt-2 text-slate-300">Busca por DNI, revisa servicios matriculados y marca el avance de la rutina.</p>
        </div>
        <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="searchClient">
          <input v-model="dni" class="field-input min-w-64" placeholder="DNI del cliente" />
          <button class="rounded-2xl bg-cyan-400 px-5 py-3 font-bold text-slate-950">Buscar</button>
        </form>
      </div>
    </section>

    <section v-if="clientData?.cliente" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-wrap items-center gap-2 text-sm text-slate-300">
        <span class="rounded-full bg-slate-950/70 px-3 py-1 font-bold text-white">{{ clientData.cliente.nombre }}</span>
        <span class="rounded-full bg-white/10 px-3 py-1">{{ clientData.cliente.id_usuario }}</span>
        <span class="rounded-full bg-white/10 px-3 py-1">DNI {{ clientData.cliente.dni }}</span>
      </div>

      <div class="mt-5 grid gap-4 xl:grid-cols-2">
        <article v-for="item in clientData.matriculas" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-lg font-black text-white">{{ serviceLabel(item.servicio) }}</p>
              <p class="text-sm text-slate-400">{{ dayLabel(item.dia) }} {{ item.hora_inicio }} - {{ item.hora_fin }}</p>
            </div>
            <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-slate-200">
              {{ item.rutina_origen === 'cliente' ? 'Rutina cliente' : 'Rutina servicio' }}
            </span>
          </div>

          <div class="mt-4 rounded-2xl bg-slate-950/60 p-4">
            <p class="font-black text-cyan-100">{{ item.rutina_nombre || 'Sin rutina asignada' }}</p>
            <p class="mt-1 text-sm text-slate-300">{{ item.zonas_musculares || 'Asigna una rutina compatible con este servicio.' }}</p>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
            <select class="field-input" :value="item.id_rutina || 0" @change="assignRoutine(item, $event.target.value)">
              <option :value="0" disabled>Rutina de {{ serviceLabel(item.servicio) }}</option>
              <option v-for="routine in routinesForService(item.servicio)" :key="routine.id_rutina" :value="routine.id_rutina">
                {{ routine.nombre_rutina }}
              </option>
            </select>
            <button
              class="rounded-2xl bg-emerald-400 px-4 py-3 font-bold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              :disabled="!item.id_rutina"
              @click="markDone(item)"
            >
              Check realizado
            </button>
          </div>

          <div class="mt-4">
            <p class="text-xs uppercase tracking-[0.24em] text-slate-500">Avance reciente</p>
            <div class="mt-2 space-y-2">
              <p v-for="progress in item.progreso || []" :key="progress.id_progreso" class="rounded-xl bg-slate-950/70 px-3 py-2 text-sm text-slate-300">
                {{ progress.fecha }} · {{ progress.estado }}<span v-if="progress.observacion"> · {{ progress.observacion }}</span>
              </p>
            </div>
            <p v-if="!(item.progreso || []).length" class="mt-2 text-sm text-slate-500">Sin checks registrados.</p>
          </div>
        </article>
      </div>

      <p v-if="!clientData.matriculas.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-slate-400">
        El cliente no tiene servicios matriculados activos.
      </p>
    </section>

    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
      {{ feedback }}
    </p>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const dni = ref('');
const clientData = ref(null);
const feedback = ref('');
const feedbackTone = ref('success');

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miercoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sabado', domingo: 'Domingo' })[day] || day || 'Dia';
const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());

const searchClient = async () => {
  try {
    feedback.value = '';
    await gymStore.fetchTrainerOverview();
    clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value);
  } catch (error) {
    clientData.value = null;
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo buscar el cliente.';
  }
};

const reloadClient = async () => {
  if (!dni.value.trim()) return;
  clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value);
};

const assignRoutine = async (item, idRutina) => {
  if (!Number(idRutina || 0)) return;
  try {
    feedback.value = '';
    await gymStore.assignTrainerRoutine(item.id_matricula, idRutina);
    await reloadClient();
    feedbackTone.value = 'success';
    feedback.value = 'Rutina asignada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo asignar la rutina.';
  }
};

const markDone = async (item) => {
  try {
    feedback.value = '';
    await gymStore.markTrainerRoutineProgress(item.id_matricula);
    await reloadClient();
    feedbackTone.value = 'success';
    feedback.value = 'Rutina marcada como realizada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo marcar la rutina.';
  }
};
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
