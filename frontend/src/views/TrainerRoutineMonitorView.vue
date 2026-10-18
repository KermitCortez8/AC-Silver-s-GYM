<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Monitoreo</p>
          <h1 class="mt-2 text-3xl font-black text-white">Rutinas del cliente</h1>
          <p class="mt-2 text-slate-300">Busca por DNI, revisa servicios matriculados y marca el avance de la rutina.</p>
        </div>
        <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="searchClient()">
          <div class="relative sm:w-80">
            <input
              v-model="dni"
              class="field-input"
              type="text"
              inputmode="numeric"
              maxlength="8"
              autocomplete="off"
              placeholder="DNI del cliente"
              aria-label="DNI del cliente"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="dni-suggestions"
              :aria-expanded="showSuggestions"
              :aria-activedescendant="activeIndex >= 0 ? `dni-option-${activeIndex}` : undefined"
              @input="onDniInput"
              @focus="openSuggestions"
              @blur="open = false"
              @keydown.down.prevent="moveActive(1)"
              @keydown.up.prevent="moveActive(-1)"
              @keydown.enter="onEnter"
              @keydown.esc="open = false"
            />
            <ul
              v-if="showSuggestions"
              id="dni-suggestions"
              role="listbox"
              class="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-white/10 bg-slate-950 p-1 shadow-xl"
              @mousedown.prevent
            >
              <li
                v-for="(client, index) in suggestions"
                :id="`dni-option-${index}`"
                :key="client.dni"
                role="option"
                :aria-selected="index === activeIndex"
                class="cursor-pointer rounded-xl px-3 py-2 text-sm"
                :class="index === activeIndex ? 'bg-cyan-400/15 text-white' : 'text-slate-200 hover:bg-white/10'"
                @mousedown.prevent="pickClient(client.dni)"
                @mouseenter="activeIndex = index"
              >
                <span class="font-bold text-cyan-300">{{ client.dni.slice(0, dni.length) }}</span>{{ client.dni.slice(dni.length) }}
                <span class="ml-2 text-slate-400">· {{ client.nombre }}</span>
              </li>
              <li v-if="!suggestions.length" class="px-3 py-2 text-sm text-slate-400" role="option" aria-disabled="true" aria-selected="false">
                Ningún cliente con matrícula activa empieza con {{ dni }}. Pulsa Buscar para consultar ese DNI.
              </li>
            </ul>
          </div>
          <button class="rounded-2xl bg-cyan-400 px-5 py-3 font-bold text-slate-950 disabled:opacity-60" :disabled="searching">
            {{ searching ? 'Buscando…' : 'Buscar' }}
          </button>
        </form>
      </div>
    </section>

    <section v-if="clientData?.cliente" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-wrap items-center gap-2 text-sm text-slate-300">
        <span class="rounded-full bg-slate-950/70 px-3 py-1 font-bold text-white">{{ clientData.cliente.nombre }}</span>
        <span class="rounded-full bg-white/10 px-3 py-1">{{ clientData.cliente.id_usuario }}</span>
        <span class="rounded-full bg-white/10 px-3 py-1">DNI {{ clientData.cliente.dni }}</span>
      </div>

      <p
        v-if="!clientData.matriculas.length"
        class="mt-5 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100"
        role="alert"
      >
        {{ clientData.cliente.nombre }} no tiene una matrícula activa, así que no se puede asignar una rutina.
        Primero debe matricularse en un horario.
      </p>

      <div class="mt-5 grid gap-4 xl:grid-cols-2">
        <article v-for="item in clientData.matriculas" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-lg font-black text-white">{{ serviceLabel(item.servicio) }}</p>
              <p class="text-sm text-slate-400">{{ dayLabel(item.dia) }} {{ item.hora_inicio }} - {{ item.hora_fin }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <span class="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-bold text-emerald-200">Matrícula activa</span>
              <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-slate-200">
                {{ item.rutina_origen === 'cliente' ? 'Rutina del cliente' : 'Rutina del servicio' }}
              </span>
            </div>
          </div>

          <div class="mt-4 rounded-2xl bg-slate-950/60 p-4">
            <p class="font-black text-cyan-100">{{ item.rutina_nombre || 'Sin rutina asignada' }}</p>
            <p class="mt-1 text-sm text-slate-300">{{ item.zonas_musculares || 'Asigna una rutina compatible con este servicio.' }}</p>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
            <select
              class="field-input"
              :value="selectedRoutine(item)"
              :disabled="!canAssign(item) || assigningId === item.id_matricula"
              :aria-label="`Rutina de ${serviceLabel(item.servicio)}`"
              @change="selection[item.id_matricula] = Number($event.target.value)"
            >
              <option :value="0" disabled>Rutina de {{ serviceLabel(item.servicio) }}</option>
              <option v-for="routine in routinesForService(item.servicio)" :key="routine.id_rutina" :value="routine.id_rutina">
                {{ routine.nombre_rutina }}
              </option>
            </select>
            <button
              class="rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              :disabled="!canAssign(item) || !hasChange(item) || assigningId === item.id_matricula"
              @click="assignRoutine(item)"
            >
              {{ assigningId === item.id_matricula ? 'Asignando…' : 'Asignar' }}
            </button>
          </div>
          <button
            class="mt-3 w-full rounded-2xl bg-emerald-400 px-4 py-3 font-bold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            :disabled="!item.id_rutina"
            @click="markDone(item)"
          >
            Check realizado
          </button>

          <p
            v-if="isEnrollmentActive(item) && !hasCompatibleRoutines(item)"
            class="mt-3 rounded-xl border border-amber-400/20 bg-amber-400/10 px-3 py-2 text-sm text-amber-100"
            role="status"
          >
            No hay rutinas compatibles con el servicio {{ serviceLabel(item.servicio) }}. Crea una en la sección Rutinas para poder asignarla.
          </p>

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

    </section>

    <p v-if="feedback" role="status" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
      {{ feedback }}
    </p>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const dni = ref('');
const clientData = ref(null);
const feedback = ref('');
const feedbackTone = ref('success');
const searching = ref(false);
const assigningId = ref(0);
const open = ref(false);
const activeIndex = ref(-1);
// Rutina elegida (aún sin asignar) por cada matrícula.
const selection = reactive({});

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

/**
 * Gestiona esta acción de la vista.
 */
const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
/**
 * Gestiona esta acción de la vista.
 */
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miercoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sabado', domingo: 'Domingo' })[day] || day || 'Dia';
/**
 * Gestiona esta acción de la vista.
 */
const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());
const isEnrollmentActive = (item) => String(item.estado || '').trim().toUpperCase() === 'ACTIVA';
const hasCompatibleRoutines = (item) => routinesForService(item.servicio).length > 0;
const canAssign = (item) => isEnrollmentActive(item) && hasCompatibleRoutines(item);
const selectedRoutine = (item) => selection[item.id_matricula] ?? (item.id_rutina || 0);
const hasChange = (item) => {
  const chosen = Number(selection[item.id_matricula] || 0);
  return chosen > 0 && chosen !== Number(item.id_rutina || 0);
};

// Clientes con matrícula activa (para sugerirlos mientras se escribe el DNI).
const activeClients = computed(() => {
  const seen = new Map();
  for (const row of overview.value.schedule_monitor || []) {
    const clientDni = String(row.cliente_dni || '').trim();
    if (clientDni && !seen.has(clientDni)) seen.set(clientDni, { dni: clientDni, nombre: row.cliente_nombre || 'Cliente' });
  }
  return [...seen.values()].sort((a, b) => a.nombre.localeCompare(b.nombre));
});

// Sugerencias: DNI que empiezan con lo escrito. Con 8 dígitos queda una sola opción.
const suggestions = computed(() => {
  const prefix = dni.value.trim();
  return activeClients.value.filter((client) => client.dni.startsWith(prefix)).slice(0, 50);
});
const showSuggestions = computed(() => open.value && (suggestions.value.length > 0 || dni.value.length > 0));

/**
 * Gestiona esta acción de la vista.
 */
const searchClient = async () => {
  open.value = false;
  const query = dni.value.trim();
  if (!query) {
    feedbackTone.value = 'error';
    feedback.value = 'Escribe un DNI o selecciona un cliente.';
    return;
  }
  searching.value = true;
  try {
    feedback.value = '';
    await gymStore.fetchTrainerOverview();
    clientData.value = await gymStore.fetchTrainerClientRoutines(query);
    Object.keys(selection).forEach((key) => delete selection[key]);
  } catch (error) {
    clientData.value = null;
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo buscar el cliente.';
  } finally {
    searching.value = false;
  }
};

/** Solo dígitos en el DNI; las sugerencias se filtran a medida que escribes. */
const onDniInput = () => {
  dni.value = dni.value.replace(/\D/g, '').slice(0, 8);
  feedback.value = '';
  open.value = true;
  activeIndex.value = -1;
};

const openSuggestions = () => {
  open.value = true;
  activeIndex.value = -1;
};

/** Mueve la opción resaltada con las flechas del teclado. */
const moveActive = (step) => {
  open.value = true;
  const total = suggestions.value.length;
  if (!total) return;
  activeIndex.value = activeIndex.value < 0 ? (step > 0 ? 0 : total - 1) : (activeIndex.value + step + total) % total;
  nextTick(() => document.getElementById(`dni-option-${activeIndex.value}`)?.scrollIntoView({ block: 'nearest' }));
};

/** Enter elige la opción resaltada; si no hay ninguna, el formulario busca el DNI escrito. */
const onEnter = (event) => {
  if (showSuggestions.value && activeIndex.value >= 0 && suggestions.value[activeIndex.value]) {
    event.preventDefault();
    pickClient(suggestions.value[activeIndex.value].dni);
  }
};

/** Elige un cliente de las sugerencias: completa el DNI y lo busca. */
const pickClient = (value) => {
  dni.value = value;
  searchClient();
};

/**
 * Gestiona esta acción de la vista.
 */
const reloadClient = async () => {
  if (!dni.value.trim()) return;
  clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value);
};

/**
 * Gestiona esta acción de la vista.
 */
const assignRoutine = async (item) => {
  const idRutina = Number(selection[item.id_matricula] || 0);
  if (!idRutina) return;
  if (!isEnrollmentActive(item)) {
    feedbackTone.value = 'error';
    feedback.value = 'Solo se puede asignar una rutina a una matrícula activa.';
    return;
  }
  if (!hasCompatibleRoutines(item)) {
    feedbackTone.value = 'error';
    feedback.value = `No hay rutinas compatibles con el servicio ${serviceLabel(item.servicio)}.`;
    return;
  }
  const routine = routinesForService(item.servicio).find((entry) => Number(entry.id_rutina) === idRutina);
  if (!routine) {
    feedbackTone.value = 'error';
    feedback.value = `Esa rutina no corresponde al servicio ${serviceLabel(item.servicio)}.`;
    return;
  }
  assigningId.value = item.id_matricula;
  try {
    feedback.value = '';
    await gymStore.assignTrainerRoutine(item.id_matricula, idRutina);
    delete selection[item.id_matricula];
    await reloadClient();
    feedbackTone.value = 'success';
    feedback.value = `Rutina «${routine.nombre_rutina}» asignada a ${serviceLabel(item.servicio)} (${dayLabel(item.dia)} ${item.hora_inicio} - ${item.hora_fin}).`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo asignar la rutina.';
    // Vuelve a leer al cliente para mostrar el estado real.
    await reloadClient().catch(() => {});
  } finally {
    assigningId.value = 0;
  }
};

/**
 * Gestiona esta acción de la vista.
 */
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

// Carga la lista de clientes con matrícula activa y las rutinas del catálogo.
onMounted(() => {
  gymStore.fetchTrainerOverview().catch(() => {});
});
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
