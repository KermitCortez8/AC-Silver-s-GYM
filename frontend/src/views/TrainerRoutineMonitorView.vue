<template>
  <div class="space-y-6 relative">
    <!-- POP-UP / TOAST NOTIFICATION CONTAINER (FLOTANTE EN ESQUINA INFERIOR DERECHA) -->
    <Teleport to="body">
      <div v-if="toast.show" class="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border px-5 py-4 shadow-2xl backdrop-blur-xl transition-all animate-bounce-short" :class="toast.type === 'error' ? 'border-rose-500/40 bg-slate-900/95 text-rose-200 shadow-rose-950/50' : 'border-emerald-500/40 bg-slate-900/95 text-emerald-200 shadow-emerald-950/50'">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl font-black text-lg" :class="toast.type === 'error' ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'">
          {{ toast.type === 'error' ? '⚠️' : '✓' }}
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider font-bold opacity-80">{{ toast.type === 'error' ? 'Error u Operación Fallida' : 'Notificación del Sistema' }}</p>
          <p class="text-sm font-semibold text-white mt-0.5">{{ toast.message }}</p>
        </div>
        <button class="ml-4 text-slate-400 hover:text-white font-bold text-sm" @click="toast.show = false">✕</button>
      </div>
    </Teleport>

    <!-- Header & Búsqueda -->
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Módulo Entrenador</p>
          <h1 class="mt-2 text-3xl font-black text-white">Supervisión y Seguimiento de Rutinas</h1>
          <p class="mt-2 text-slate-300">Consulta alumnos matriculados, asigna nuevas rutinas personalizadas y registra el progreso de ejercicios.</p>
        </div>
        <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="searchClient">
          <input v-model="dni" class="field-input min-w-64" placeholder="Ingresa DNI del cliente" required />
          <button class="rounded-2xl bg-cyan-400 px-6 py-3 font-bold text-slate-950 hover:bg-cyan-300 transition shadow-lg shadow-cyan-400/20">
            Buscar Cliente
          </button>
        </form>
      </div>
    </section>

    <!-- Visual Rest Timer (Flotante) -->
    <section v-if="timerActive || timerSeconds > 0" class="rounded-2xl border border-cyan-400/30 bg-slate-900/90 p-4 shadow-xl transition-all">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300 font-black text-lg">
            ⏱️
          </div>
          <div>
            <p class="text-xs uppercase tracking-wider text-slate-400">Temporizador de descanso entre series</p>
            <p class="text-2xl font-black text-white" :class="{ 'text-emerald-400 font-extrabold animate-pulse': timerSeconds === 0 }">
              {{ formatTimer(timerSeconds) }}
              <span v-if="timerSeconds === 0" class="text-sm font-bold text-emerald-400 ml-2">¡Tiempo de descanso finalizado!</span>
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button v-if="!timerActive" class="rounded-xl bg-cyan-400 px-4 py-2 font-bold text-slate-950 text-sm hover:bg-cyan-300" @click="startTimer">
            {{ timerSeconds > 0 ? 'Reanudar' : 'Iniciar' }}
          </button>
          <button v-else class="rounded-xl bg-amber-400 px-4 py-2 font-bold text-slate-950 text-sm hover:bg-amber-300" @click="pauseTimer">
            Pausar
          </button>
          <button class="rounded-xl border border-white/10 bg-slate-800 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700" @click="resetTimer">
            Reiniciar
          </button>
        </div>
      </div>
    </section>

    <!-- Estado 1: ANIMACIÓN DE CARGA GIRATORIA CUANDO ESTÁ BUSCANDO -->
    <section v-if="isSearching" class="rounded-2xl border border-white/10 bg-slate-900/80 p-16 text-center backdrop-blur shadow-2xl space-y-4">
      <div class="flex flex-col items-center justify-center gap-4">
        <div class="relative flex h-20 w-20 items-center justify-center">
          <!-- Anillo exterior giratorio en cyan -->
          <div class="absolute h-20 w-20 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent shadow-lg shadow-cyan-400/40"></div>
          <!-- Icono interior de lupa -->
          <svg class="w-8 h-8 text-cyan-300 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div class="space-y-1">
          <p class="text-lg font-black text-white">Consultando información del cliente...</p>
          <p class="text-xs text-slate-400">Buscando DNI <span class="font-mono font-bold text-cyan-300">{{ dni }}</span> y cargando rutinas asignadas</p>
        </div>
      </div>
    </section>

    <!-- Estado 2: Panel de información del Cliente (Basado en la Plantilla de la foto) -->
    <section v-else-if="clientData?.cliente" class="space-y-6">
      <!-- BARRA SUPERIOR DE DATOS DEL CLIENTE (Plantilla) -->
      <div class="rounded-2xl border border-white/10 bg-slate-900/90 p-4 backdrop-blur shadow-lg">
        <div class="flex flex-wrap items-center justify-between gap-4 text-sm font-semibold text-slate-200">
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Cliente:</span>
            <span class="font-black text-white text-base">{{ clientData.cliente.nombre }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">DNI:</span>
            <span class="font-mono text-cyan-200">{{ clientData.cliente.dni }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Membresía:</span>
            <span class="rounded-full px-3 py-0.5 text-xs font-bold" :class="hasActiveMembership ? 'bg-emerald-400/20 text-emerald-300 border border-emerald-400/30' : 'bg-rose-400/20 text-rose-300 border border-rose-400/30'">
              {{ membershipLabel }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Código ID:</span>
            <span class="text-slate-300">{{ clientData.cliente.id_usuario }}</span>
          </div>

          <!-- BOTÓN INTEGRADO DE ACCIÓN: + ASIGNAR RUTINA PERSONALIZADA -->
          <button
            class="flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-2 text-xs font-extrabold text-white hover:from-purple-500 hover:to-indigo-500 transition shadow-lg shadow-purple-900/30"
            @click="openAssignModal"
          >
            <svg class="w-4 h-4 text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
            </svg>
            <span>Asignar rutina personalizada</span>
          </button>
        </div>
      </div>

      <!-- LISTADO DE RUTINAS ASIGNADAS (Estilo Tarjetas de Plantilla) -->
      <div class="space-y-4">
        <article v-for="item in clientData.matriculas" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-xl space-y-4">
          <!-- Cabecera de la rutina y Botones de Acción (Editar / Eliminar) -->
          <div class="flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-4">
            <div>
              <div class="flex items-center gap-3">
                <h3 class="text-xl font-black text-white">{{ item.rutina_nombre || ('Servicio de ' + serviceLabel(item.servicio)) }}</h3>
                <span class="rounded-full bg-cyan-400/10 px-3 py-1 text-xs font-bold text-cyan-200 border border-cyan-400/20">
                  {{ serviceLabel(item.servicio) }}
                </span>
              </div>
              <div class="mt-2 grid gap-1 text-sm text-slate-300 sm:grid-cols-2">
                <p><strong class="text-slate-400">Día:</strong> {{ dayLabel(item.dia) }}</p>
                <p><strong class="text-slate-400">Hora:</strong> {{ item.hora_inicio }} - {{ item.hora_fin }}</p>
                <p class="sm:col-span-2"><strong class="text-slate-400">Zonas musculares:</strong> {{ item.zonas_musculares || 'General / Fuerza' }}</p>
                <p class="sm:col-span-2"><strong class="text-slate-400">Estado:</strong> 
                  <span class="font-bold ml-1" :class="item.id_rutina ? 'text-emerald-400' : 'text-amber-400'">
                    {{ item.id_rutina ? 'En progreso' : 'Pendiente asignación' }}
                  </span>
                </p>
              </div>
            </div>

            <!-- Botones Editar / Eliminar (Plantilla) -->
            <div class="flex items-center gap-2">
              <button
                v-if="item.id_rutina"
                class="rounded-xl border border-white/10 bg-slate-800 px-4 py-2 text-xs font-bold text-white hover:bg-slate-700 transition"
                @click="openExercisesModal(item)"
              >
                Editar / Ejercicios
              </button>
              <button
                v-if="item.id_rutina"
                class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-2 text-xs font-bold text-rose-300 hover:bg-rose-500/20 transition"
                @click="confirmUnassign(item)"
              >
                Eliminar
              </button>
            </div>
          </div>

          <!-- Historial de avance reciente -->
          <div>
            <p class="text-xs uppercase tracking-wider font-bold text-slate-400">Avance reciente registrado</p>
            <div v-if="(item.progreso || []).length" class="mt-2 space-y-2 max-h-36 overflow-y-auto pr-1">
              <div v-for="progress in item.progreso || []" :key="progress.id_progreso" class="rounded-xl bg-slate-950/70 p-3 text-xs space-y-1">
                <div class="flex items-center justify-between text-slate-300">
                  <span class="font-bold text-cyan-200">{{ progress.fecha }}</span>
                  <span class="rounded bg-emerald-400/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">{{ progress.estado }}</span>
                </div>
                <p v-if="progress.observacion" class="text-slate-400">{{ progress.observacion }}</p>
                <div v-if="(progress.ejercicios_detalle || []).length" class="mt-1 space-y-1 border-t border-white/5 pt-1">
                  <div v-for="(exDet, detIdx) in progress.ejercicios_detalle" :key="detIdx" class="text-[11px] text-slate-300 flex justify-between">
                    <span>{{ exDet.completado ? '✓' : '✗' }} {{ exDet.nombre_ejercicio }}</span>
                    <span class="text-slate-400">{{ exDet.series_completadas }} series <template v-if="exDet.peso_utilizado_kg">· {{ exDet.peso_utilizado_kg }} kg</template></span>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="mt-2 text-xs text-slate-500">Sin checks de avance registrados aún.</p>
          </div>
        </article>
      </div>

      <p v-if="!clientData.matriculas.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-slate-400">
        El cliente no tiene matrículas activas.
      </p>
    </section>

    <!-- Estado 3: ESTADO VACÍO PREVIO A LA BÚSQUEDA -->
    <section v-else class="rounded-2xl border border-dashed border-white/10 bg-slate-950/40 p-12 text-center">
      <div class="mx-auto max-w-sm space-y-3">
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/10 text-cyan-300 font-bold text-2xl border border-cyan-400/20">
          🔍
        </div>
        <h3 class="text-lg font-bold text-white">Consulta y Asignación de Alumnos</h3>
        <p class="text-xs text-slate-400">Ingresa el número de DNI del alumno arriba y haz clic en "Buscar Cliente" para consultar sus rutinas y registrar progresos.</p>
      </div>
    </section>

    <!-- MODAL: Asignar Nueva Rutina Personalizada (Plantilla) -->
    <Teleport to="body">
      <div v-if="showAssignModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <div class="w-full max-w-xl rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl space-y-5 animate-scale-up">
          <div class="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 class="text-xl font-black text-white">Asignar rutina personalizada</h3>
            <button class="text-slate-400 hover:text-white font-bold" @click="showAssignModal = false">✕</button>
          </div>

          <div class="space-y-4">
            <label class="block space-y-2">
              <span class="text-xs uppercase tracking-wider font-bold text-slate-300">Seleccionar servicio matriculado del cliente</span>
              <select v-model="assignForm.id_matricula" class="field-input text-sm">
                <option v-for="mat in clientData?.matriculas || []" :key="mat.id_matricula" :value="mat.id_matricula">
                  {{ serviceLabel(mat.servicio) }} ({{ dayLabel(mat.dia) }} {{ mat.hora_inicio }} - {{ mat.hora_fin }})
                </option>
              </select>
            </label>

            <label class="block space-y-2">
              <span class="text-xs uppercase tracking-wider font-bold text-slate-300">Rutina del catálogo a vincular</span>
              <select v-model="assignForm.id_rutina" class="field-input text-sm">
                <option :value="0" disabled>Selecciona una rutina</option>
                <option v-for="routine in availableRoutinesForSelectedMatricula" :key="routine.id_rutina" :value="routine.id_rutina">
                  {{ routine.nombre_rutina }} ({{ (routine.ejercicios || []).length }} ej.)
                </option>
              </select>
            </label>
          </div>

          <div class="flex gap-3 pt-2">
            <button
              class="rounded-xl bg-emerald-500 px-6 py-3 font-bold text-slate-950 hover:bg-emerald-400 transition"
              :disabled="!assignForm.id_matricula || !assignForm.id_rutina"
              @click="submitAssignRoutine"
            >
              Guardar rutina
            </button>
            <button class="rounded-xl bg-slate-700 px-6 py-3 font-bold text-white hover:bg-slate-600 transition" @click="showAssignModal = false">
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- MODAL: Editar Ejercicios y Registrar Seguimiento -->
    <Teleport to="body">
      <div v-if="showExercisesModal && selectedMatriculaItem" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl space-y-5">
          <div class="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <h3 class="text-xl font-black text-white">{{ selectedMatriculaItem.rutina_nombre }}</h3>
              <p class="text-xs text-slate-400">{{ serviceLabel(selectedMatriculaItem.servicio) }} · {{ selectedMatriculaItem.zonas_musculares }}</p>
            </div>
            <button class="text-slate-400 hover:text-white font-bold" @click="showExercisesModal = false">✕</button>
          </div>

          <!-- Ejercicios interactivos -->
          <div class="space-y-3">
            <div
              v-for="(ex, exIdx) in getTracker(selectedMatriculaItem.id_matricula, selectedMatriculaItem.id_rutina)"
              :key="exIdx"
              class="rounded-xl border border-white/10 bg-slate-950/80 p-4 space-y-2"
              :class="{ 'border-emerald-400/40 bg-emerald-400/5': ex.completado }"
            >
              <div class="flex items-start justify-between gap-2">
                <label class="flex items-center gap-2 cursor-pointer font-bold text-white text-sm">
                  <input type="checkbox" v-model="ex.completado" class="h-4 w-4 rounded border-white/20 bg-slate-900 text-cyan-400 accent-cyan-400" />
                  <span :class="{ 'line-through text-slate-400': ex.completado }">{{ ex.nombre_ejercicio }}</span>
                </label>

                <button
                  type="button"
                  class="rounded-lg bg-cyan-400/10 px-2.5 py-1 text-xs font-bold text-cyan-200 hover:bg-cyan-400/20"
                  @click="setRestTimer(ex.descanso_segundos || 60)"
                >
                  ⏱️ {{ ex.descanso_segundos || 60 }}s descanso
                </button>
              </div>

              <p v-if="ex.notas" class="text-xs text-slate-400 italic">{{ ex.notas }}</p>

              <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 pt-1 text-xs">
                <div>
                  <span class="text-slate-400">Series completadas</span>
                  <div class="flex items-center gap-1 mt-1">
                    <input v-model.number="ex.series_completadas" type="number" min="0" max="20" class="field-input text-xs py-1 px-2 text-center w-16" />
                    <span class="text-slate-400">/ {{ ex.series_meta }}</span>
                  </div>
                </div>

                <div>
                  <span class="text-slate-400">Peso real (kg)</span>
                  <input v-model.number="ex.peso_utilizado_kg" type="number" step="0.5" min="0" class="field-input mt-1 text-xs py-1 px-2" :placeholder="ex.peso_sugerido_kg ? 'Sug: ' + ex.peso_sugerido_kg : 'Kg'" />
                </div>

                <div class="col-span-2 sm:col-span-1">
                  <span class="text-slate-400">Reps logradas</span>
                  <input v-model="ex.repeticiones_logradas" class="field-input mt-1 text-xs py-1 px-2" placeholder="10, 10, 8" />
                </div>
              </div>
            </div>
          </div>

          <div class="space-y-2 pt-2">
            <input v-model="observationsMap[selectedMatriculaItem.id_matricula]" class="field-input text-xs" placeholder="Observaciones generales de la sesión (opcional)" />
            <div class="flex gap-3 pt-2">
              <button class="w-full rounded-xl bg-emerald-500 px-6 py-3 font-bold text-slate-950 hover:bg-emerald-400 transition" @click="submitSaveProgress">
                Guardar Progreso de Sesión
              </button>
              <button class="rounded-xl bg-slate-700 px-5 py-3 font-bold text-white hover:bg-slate-600 transition" @click="showExercisesModal = false">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- MODAL: Confirmar Desvinculación de Rutina -->
    <Teleport to="body">
      <div v-if="showConfirmModal && selectedMatriculaItem" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <div class="w-full max-w-md rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl space-y-4">
          <h3 class="text-xl font-black text-white">¿Desvincular rutina?</h3>
          <p class="text-sm text-slate-300">
            Se quitará la rutina asignada para el servicio <strong>{{ serviceLabel(selectedMatriculaItem.servicio) }}</strong>.
          </p>
          <div class="flex justify-end gap-3 pt-3">
            <button class="rounded-xl bg-slate-700 px-4 py-2 text-sm font-bold text-white hover:bg-slate-600" @click="showConfirmModal = false">
              Cancelar
            </button>
            <button class="rounded-xl bg-rose-500 px-4 py-2 text-sm font-bold text-white hover:bg-rose-600" @click="submitUnassign">
              Sí, desvincular
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onUnmounted } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const dni = ref('');
const clientData = ref(null);

// POP-UP TOAST SYSTEM
const toast = reactive({
  show: false,
  message: '',
  type: 'success',
  timer: null,
});

const showToast = (message, type = 'success') => {
  toast.message = message;
  toast.type = type;
  toast.show = true;
  if (toast.timer) clearTimeout(toast.timer);
  toast.timer = setTimeout(() => {
    toast.show = false;
  }, 4000);
};

// Modales state
const showAssignModal = ref(false);
const showExercisesModal = ref(false);
const showConfirmModal = ref(false);
const selectedMatriculaItem = ref(null);

const assignForm = reactive({
  id_matricula: null,
  id_rutina: 0,
});

// Tracker maps
const trackerMap = reactive({});
const observationsMap = reactive({});

// Temporizador visual
const timerSeconds = ref(0);
const timerActive = ref(false);
let timerInterval = null;

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const dayLabel = (day) => ({ lunes: 'Lunes, Miércoles, Viernes', martes: 'Martes, Jueves', miercoles: 'Miércoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sábado', domingo: 'Domingo' })[day] || day || 'Día';

const hasActiveMembership = computed(() => {
  const m = clientData.value?.matriculas || [];
  return m.length > 0;
});

const membershipLabel = computed(() => {
  return hasActiveMembership.value ? 'Vigente' : 'Sin membresía activa';
});

const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());

const availableRoutinesForSelectedMatricula = computed(() => {
  if (!assignForm.id_matricula) return routines.value;
  const mat = clientData.value?.matriculas.find((m) => Number(m.id_matricula) === Number(assignForm.id_matricula));
  return mat ? routinesForService(mat.servicio) : routines.value;
});

const getRoutineExercises = (idRutina) => {
  const routine = routines.value.find((r) => Number(r.id_rutina) === Number(idRutina));
  return routine && Array.isArray(routine.ejercicios) ? routine.ejercicios : [];
};

const getTracker = (idMatricula, idRutina) => {
  const key = `${idMatricula}_${idRutina}`;
  if (!trackerMap[key]) {
    const rawExs = getRoutineExercises(idRutina);
    trackerMap[key] = rawExs.map((ex, i) => ({
      id_ejercicio: ex.id_ejercicio || i + 1,
      nombre_ejercicio: ex.nombre_ejercicio || `Ejercicio #${i + 1}`,
      series_meta: ex.series || 3,
      series_completadas: ex.series || 3,
      repeticiones_logradas: ex.repeticiones || '10-12',
      peso_sugerido_kg: ex.peso_sugerido_kg || null,
      peso_utilizado_kg: ex.peso_sugerido_kg || null,
      descanso_segundos: ex.descanso_segundos || 60,
      notas: ex.notas || '',
      completado: true,
      observaciones: '',
    }));
  }
  return trackerMap[key];
};

// Temporizador
const setRestTimer = (seconds) => {
  resetTimer();
  timerSeconds.value = seconds;
  startTimer();
};

const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval);
  if (timerSeconds.value <= 0) return;
  timerActive.value = true;
  timerInterval = setInterval(() => {
    if (timerSeconds.value > 0) {
      timerSeconds.value--;
    } else {
      pauseTimer();
    }
  }, 1000);
};

const pauseTimer = () => {
  timerActive.value = false;
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
};

const resetTimer = () => {
  pauseTimer();
  timerSeconds.value = 0;
};

const formatTimer = (totalSec) => {
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

onUnmounted(() => {
  pauseTimer();
});

const isSearching = ref(false);

const searchClient = async () => {
  if (!dni.value.trim()) return;
  try {
    isSearching.value = true;
    clientData.value = null;
    await gymStore.fetchTrainerOverview();
    clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value);
    showToast(`Cliente ${clientData.value.cliente.nombre} cargado exitosamente.`, 'success');
  } catch (error) {
    clientData.value = null;
    showToast(error instanceof Error ? error.message : 'No se pudo buscar el cliente.', 'error');
  } finally {
    isSearching.value = false;
  }
};

const reloadClient = async () => {
  if (!dni.value.trim()) return;
  clientData.value = await gymStore.fetchTrainerClientRoutines(dni.value);
};

const openAssignModal = () => {
  if (clientData.value?.matriculas?.length) {
    assignForm.id_matricula = clientData.value.matriculas[0].id_matricula;
  }
  assignForm.id_rutina = 0;
  showAssignModal.value = true;
};

const submitAssignRoutine = async () => {
  if (!assignForm.id_matricula || !assignForm.id_rutina) return;
  try {
    await gymStore.assignTrainerRoutine(assignForm.id_matricula, assignForm.id_rutina);
    await reloadClient();
    showAssignModal.value = false;
    showToast('Rutina personalizada asignada exitosamente.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo asignar la rutina.', 'error');
  }
};

const openExercisesModal = (item) => {
  selectedMatriculaItem.value = item;
  showExercisesModal.value = true;
};

const submitSaveProgress = async () => {
  if (!selectedMatriculaItem.value) return;
  const item = selectedMatriculaItem.value;
  try {
    const trackerExs = getTracker(item.id_matricula, item.id_rutina);
    const ejercicios_detalle = trackerExs.map((ex) => ({
      id_ejercicio: ex.id_ejercicio,
      nombre_ejercicio: ex.nombre_ejercicio,
      completado: Boolean(ex.completado),
      series_completadas: Number(ex.series_completadas || 0),
      repeticiones_logradas: String(ex.repeticiones_logradas || ''),
      peso_utilizado_kg: ex.peso_utilizado_kg !== null && ex.peso_utilizado_kg !== '' ? Number(ex.peso_utilizado_kg) : null,
      observaciones: String(ex.observaciones || ''),
    }));

    const observacion = observationsMap[item.id_matricula] || 'Sesión de entrenamiento realizada';

    await gymStore.markTrainerRoutineProgress(item.id_matricula, {
      estado: 'REALIZADO',
      observacion,
      ejercicios_detalle,
    });

    await reloadClient();
    showExercisesModal.value = false;
    showToast('Progreso de rutina registrado en el sistema.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo registrar el progreso.', 'error');
  }
};

const confirmUnassign = (item) => {
  selectedMatriculaItem.value = item;
  showConfirmModal.value = true;
};

const submitUnassign = async () => {
  if (!selectedMatriculaItem.value) return;
  try {
    await gymStore.assignTrainerRoutine(selectedMatriculaItem.value.id_matricula, 0);
    await reloadClient();
    showConfirmModal.value = false;
    showToast('Rutina desvinculada del servicio.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo desvincular la rutina.', 'error');
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

@keyframes bounceShort {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.animate-bounce-short {
  animation: bounceShort 0.3s ease-in-out;
}
</style>