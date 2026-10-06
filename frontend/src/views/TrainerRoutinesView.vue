<template>
  <div class="catalog-root space-y-6">
    <!-- Cabecera -->
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Rutina</p>
          <h1 class="mt-2 text-3xl font-black text-white">Supervision de rutinas</h1>
          <p class="mt-2 text-slate-300">Consulta rutinas asignadas y zonas musculares trabajadas por cliente.</p>
        </div>
        <button
          class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white disabled:opacity-60"
          :disabled="isLoading"
          @click="refresh"
        >
          {{ isLoading ? 'Actualizando...' : 'Actualizar' }}
        </button>
      </div>
    </section>

    <!-- Error de carga (antes errorMessage nunca se mostraba) -->
    <p v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">
      {{ errorMessage }}
    </p>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <!-- ============ FORMULARIO ============ -->
        <div ref="formTop">
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catalogo</p>
          <h2 class="mt-2 text-2xl font-black text-white">
            {{ isEditing ? 'Editar rutina' : 'Implementar rutina' }}
          </h2>
        </div>

        <!-- Banner modo edicion -->
        <div
          v-if="isEditing"
          class="mt-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-50"
        >
          <p class="font-bold">Editando: {{ editSnapshot.nombre_rutina || 'Rutina' }}</p>
          <p v-if="editingAssignedCount > 0" class="mt-1 text-amber-100/80">
            Esta rutina esta asignada a {{ editingAssignedCount }}
            {{ editingAssignedCount === 1 ? 'cliente' : 'clientes' }}. Los cambios los afectaran.
          </p>
        </div>

        <form class="mt-5 space-y-3" novalidate @submit.prevent="saveRoutine">
          <label class="block space-y-2">
            <span class="text-sm text-slate-300">Servicio</span>
            <select v-model="routineForm.servicio" class="field-input" :class="{ 'field-error': fieldError('servicio') }">
              <option v-for="service in serviceOptions" :key="service.value" :value="service.value">{{ service.label }}</option>
            </select>
            <span v-if="fieldError('servicio')" class="block text-xs text-rose-300">{{ fieldError('servicio') }}</span>
          </label>

          <label class="block space-y-2">
            <span class="flex items-center justify-between text-sm text-slate-300">
              <span>Nombre</span>
              <span class="text-xs" :class="routineForm.nombre_rutina.length > MAX_NOMBRE ? 'text-rose-300' : 'text-slate-500'">
                {{ routineForm.nombre_rutina.length }}/{{ MAX_NOMBRE }}
              </span>
            </span>
            <input
              ref="nameInput"
              v-model="routineForm.nombre_rutina"
              class="field-input"
              :class="{ 'field-error': fieldError('nombre_rutina') }"
              placeholder="Rutina base de fuerza"
              @blur="touched.nombre_rutina = true"
            />
            <span v-if="fieldError('nombre_rutina')" class="block text-xs text-rose-300">{{ fieldError('nombre_rutina') }}</span>
          </label>

          <label class="block space-y-2">
            <span class="flex items-center justify-between text-sm text-slate-300">
              <span>Zonas musculares</span>
              <span class="text-xs" :class="routineForm.zonas_musculares.length > MAX_ZONAS ? 'text-rose-300' : 'text-slate-500'">
                {{ routineForm.zonas_musculares.length }}/{{ MAX_ZONAS }}
              </span>
            </span>
            <textarea
              v-model="routineForm.zonas_musculares"
              class="field-input min-h-24"
              :class="{ 'field-error': fieldError('zonas_musculares') }"
              placeholder="Pierna, gluteos, core..."
              @blur="touched.zonas_musculares = true"
            />
            <span v-if="fieldError('zonas_musculares')" class="block text-xs text-rose-300">{{ fieldError('zonas_musculares') }}</span>
          </label>

          <!-- Atajos para zonas comunes -->
          <div class="flex flex-wrap gap-2">
            <button
              v-for="zone in quickZones"
              :key="zone"
              type="button"
              class="chip"
              :class="zoneActive(zone) ? 'chip-active' : 'chip-idle'"
              @click="toggleZone(zone)"
            >
              {{ zone }}
            </button>
          </div>

          <div class="flex gap-3">
            <button
              class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="isSaving || (isEditing && !hasChanges)"
            >
              {{ isSaving ? 'Guardando...' : isEditing ? 'Actualizar rutina' : 'Guardar rutina' }}
            </button>
            <button
              v-if="isEditing"
              type="button"
              class="rounded-2xl border border-white/10 px-4 py-3 font-bold text-white hover:bg-white/10"
              :disabled="isSaving"
              @click="cancelEdit"
            >
              Cancelar
            </button>
          </div>
          <p v-if="isEditing && !hasChanges" class="text-xs text-slate-500">No hay cambios por guardar.</p>
        </form>

        <p
          v-if="feedback"
          class="mt-4 rounded-2xl border px-4 py-3 text-sm"
          :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'"
        >
          {{ feedback }}
        </p>

        <!-- ============ LISTADO ============ -->
        <div class="mt-8 flex items-center justify-between gap-3">
          <div class="flex items-baseline gap-3">
            <h3 class="text-lg font-black text-white">Rutinas disponibles</h3>
            <span class="text-xs text-slate-400">{{ filteredRoutines.length }} de {{ routines.length }}</span>
          </div>
          <button type="button" class="new-btn" @click="startNewRoutine">+ Nueva rutina</button>
        </div>

        <!-- Buscador + orden -->
        <div class="mt-4 flex gap-2">
          <input v-model="search" class="field-input" placeholder="Buscar por nombre o zona..." />
          <select v-model="sortBy" class="field-input !w-auto" aria-label="Ordenar rutinas">
            <option value="nombre">A-Z</option>
            <option value="asignados">Mas asignadas</option>
          </select>
        </div>

        <!-- Filtros por servicio -->
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            class="chip"
            :class="activeService === 'todos' ? 'chip-active' : 'chip-idle'"
            @click="activeService = 'todos'"
          >
            Todos ({{ routines.length }})
          </button>
          <button
            v-for="service in serviceOptions"
            :key="service.value"
            type="button"
            class="chip"
            :class="activeService === service.value ? 'chip-active' : 'chip-idle'"
            @click="activeService = service.value"
          >
            {{ service.label }} ({{ routinesForService(service.value).length }})
          </button>
        </div>

        <div class="mt-5 space-y-3">
          <article
            v-for="routine in filteredRoutines"
            :key="routine.id_rutina"
            class="rounded-2xl border bg-slate-900/80 p-4"
            :class="routine.id_rutina === routineForm.id_rutina ? 'border-amber-400/60' : 'border-white/10'"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="font-bold text-white">{{ routine.nombre_rutina || 'Rutina' }}</p>
                <p class="accent-text mt-1 text-xs uppercase tracking-[0.22em]">{{ serviceLabel(routine.servicio) }}</p>
                <p class="mt-1 text-sm text-slate-400">{{ routine.zonas_musculares || 'Sin zonas registradas' }}</p>
              </div>
              <span
                class="accent-badge shrink-0 rounded-full px-3 py-1 text-sm font-bold"
                :title="`${routine.clientes_asignados || 0} clientes asignados`"
              >
                {{ routine.clientes_asignados || 0 }}
                {{ Number(routine.clientes_asignados || 0) === 1 ? 'cliente' : 'clientes' }}
              </span>
            </div>
            <button
              class="mt-4 w-full rounded-xl border px-3 py-2 text-sm font-bold transition hover:opacity-90"
              :class="routine.id_rutina === routineForm.id_rutina ? 'bg-amber-400 text-slate-950 border-amber-400' : 'border-[var(--box-border)] bg-slate-900/80 text-white dark:bg-slate-900/80'"
              @click="editRoutine(routine)"
            >
              {{ routine.id_rutina === routineForm.id_rutina ? 'Editando...' : 'Editar rutina' }}
            </button>
          </article>
        </div>

        <!-- Estados vacios -->
        <p v-if="!routines.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
          No hay rutinas registradas.
        </p>
        <div
          v-else-if="!filteredRoutines.length"
          class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400"
        >
          <p>Ninguna rutina coincide con los filtros.</p>
          <button class="accent-text mt-3 font-bold underline" @click="clearFilters">Limpiar filtros</button>
        </div>
      </div>

      <!-- ============ PANEL SERVICIOS (ahora tambien filtra) ============ -->
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Servicios</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ serviceOptions.length }} servicios</h2>
        <div class="mt-5 grid gap-3">
          <button
            v-for="service in serviceOptions"
            :key="service.value"
            type="button"
            class="rounded-2xl border bg-slate-900/80 p-4 text-left hover:bg-slate-900"
            :class="activeService === service.value ? 'accent-border' : 'border-white/10'"
            @click="activeService = activeService === service.value ? 'todos' : service.value"
          >
            <div class="flex items-center justify-between gap-3">
              <p class="font-bold text-white">{{ service.label }}</p>
              <span class="accent-badge rounded-full px-3 py-1 text-sm font-bold">
                {{ routinesForService(service.value).length }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();

const MAX_NOMBRE = 60;
const MAX_ZONAS = 300;

const errorMessage = ref('');
const feedback = ref('');
const feedbackTone = ref('success');
const isSaving = ref(false);
const isLoading = ref(false);
const formTop = ref(null);
const nameInput = ref(null);

const serviceOptions = [
  { value: 'fitness', label: 'Fitness' },
  { value: 'musculacion', label: 'Musculacion' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'baile', label: 'Baile' },
];

const quickZones = ['Pierna', 'Gluteos', 'Core', 'Pecho', 'Espalda', 'Hombro', 'Brazos', 'Cardio'];

const routineForm = reactive({
  id_rutina: null,
  servicio: 'fitness',
  nombre_rutina: '',
  zonas_musculares: '',
  color: 'Azul',
});

// Copia de lo que se esta editando, para detectar cambios y mostrar el nombre original
const editSnapshot = ref(null);
const touched = reactive({ nombre_rutina: false, zonas_musculares: false });
const submitted = ref(false);

// Filtros del listado
const activeService = ref('todos');
const search = ref('');
const sortBy = ref('nombre');

const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);
const isEditing = computed(() => routineForm.id_rutina !== null);

/**
 * Normaliza texto para comparar (minusculas, sin tildes, sin espacios extra).
 */
const norm = (value) =>
  String(value || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

/**
 * Devuelve el nombre visible de un servicio.
 */
const serviceLabel = (service) =>
  ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';

/**
 * Devuelve las rutinas de un servicio.
 */
const routinesForService = (service) =>
  routines.value.filter((routine) => norm(routine.servicio) === norm(service));

/**
 * Rutinas despues de aplicar servicio, busqueda y orden.
 */
const filteredRoutines = computed(() => {
  const query = norm(search.value);
  const list = routines.value.filter((routine) => {
    const matchesService = activeService.value === 'todos' || norm(routine.servicio) === activeService.value;
    const matchesSearch =
      !query || norm(routine.nombre_rutina).includes(query) || norm(routine.zonas_musculares).includes(query);
    return matchesService && matchesSearch;
  });

  return [...list].sort((a, b) => {
    if (sortBy.value === 'asignados') {
      return Number(b.clientes_asignados || 0) - Number(a.clientes_asignados || 0);
    }
    return String(a.nombre_rutina || '').localeCompare(String(b.nombre_rutina || ''), 'es');
  });
});

/**
 * Clientes asignados a la rutina que se esta editando.
 */
const editingAssignedCount = computed(() => {
  const current = routines.value.find((routine) => routine.id_rutina === routineForm.id_rutina);
  return Number(current?.clientes_asignados || 0);
});

/**
 * Validaciones del formulario (se calculan en vivo).
 */
const errors = computed(() => {
  const result = {};
  const nombre = routineForm.nombre_rutina.trim();
  const zonas = routineForm.zonas_musculares.trim();

  if (!serviceOptions.some((service) => service.value === routineForm.servicio)) {
    result.servicio = 'Selecciona un servicio valido.';
  }

  if (!nombre) {
    result.nombre_rutina = 'El nombre es obligatorio.';
  } else if (nombre.length < 3) {
    result.nombre_rutina = 'Usa al menos 3 caracteres.';
  } else if (nombre.length > MAX_NOMBRE) {
    result.nombre_rutina = `Maximo ${MAX_NOMBRE} caracteres.`;
  } else if (
    routines.value.some(
      (routine) =>
        routine.id_rutina !== routineForm.id_rutina &&
        norm(routine.servicio) === routineForm.servicio &&
        norm(routine.nombre_rutina) === norm(nombre),
    )
  ) {
    result.nombre_rutina = 'Ya existe una rutina con ese nombre en este servicio.';
  }

  if (!zonas) {
    result.zonas_musculares = 'Indica al menos una zona muscular.';
  } else if (zonas.length < 3) {
    result.zonas_musculares = 'Describe las zonas con mas detalle.';
  } else if (zonas.length > MAX_ZONAS) {
    result.zonas_musculares = `Maximo ${MAX_ZONAS} caracteres.`;
  }

  return result;
});

/**
 * Muestra el error solo si el campo fue tocado o ya se intento guardar.
 */
const fieldError = (field) => (submitted.value || touched[field] ? errors.value[field] : '');

/**
 * En modo edicion, indica si hay algo distinto a lo original.
 */
const hasChanges = computed(() => {
  if (!editSnapshot.value) return true;
  return (
    routineForm.servicio !== editSnapshot.value.servicio ||
    routineForm.nombre_rutina.trim() !== editSnapshot.value.nombre_rutina.trim() ||
    routineForm.zonas_musculares.trim() !== editSnapshot.value.zonas_musculares.trim()
  );
});

/**
 * Indica si una zona rapida ya esta escrita en el textarea.
 */
const zoneActive = (zone) =>
  routineForm.zonas_musculares.split(',').some((part) => norm(part) === norm(zone));

/**
 * Agrega o quita una zona rapida del textarea.
 */
const toggleZone = (zone) => {
  const parts = routineForm.zonas_musculares.split(',').map((part) => part.trim()).filter(Boolean);
  const index = parts.findIndex((part) => norm(part) === norm(zone));
  if (index >= 0) parts.splice(index, 1);
  else parts.push(zone);
  routineForm.zonas_musculares = parts.join(', ');
  touched.zonas_musculares = true;
};

/**
 * Limpia el formulario y sale del modo edicion.
 */
const resetRoutineForm = () => {
  routineForm.id_rutina = null;
  routineForm.nombre_rutina = '';
  routineForm.zonas_musculares = '';
  routineForm.color = 'Azul';
  editSnapshot.value = null;
  submitted.value = false;
  touched.nombre_rutina = false;
  touched.zonas_musculares = false;
};

/**
 * Cancela la edicion actual.
 */
const cancelEdit = () => {
  resetRoutineForm();
  feedback.value = '';
};

/**
 * Indica si hay algo escrito que se perderia (cambios en edicion o borrador nuevo).
 */
const hasUnsavedWork = computed(() =>
  isEditing.value
    ? hasChanges.value
    : Boolean(routineForm.nombre_rutina.trim() || routineForm.zonas_musculares.trim()),
);

/**
 * Pide confirmacion solo si hay trabajo sin guardar.
 */
const confirmDiscard = () => !hasUnsavedWork.value || window.confirm('Tienes cambios sin guardar. ¿Descartarlos?');

/**
 * Prepara el formulario para crear una rutina nueva.
 */
const startNewRoutine = async () => {
  if (!confirmDiscard()) return;
  resetRoutineForm();
  feedback.value = '';
  if (activeService.value !== 'todos') routineForm.servicio = activeService.value;

  await nextTick();
  formTop.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  nameInput.value?.focus({ preventScroll: true });
};

/**
 * Limpia busqueda y filtro de servicio.
 */
const clearFilters = () => {
  search.value = '';
  activeService.value = 'todos';
};

/**
 * Carga una rutina en el formulario para editarla.
 */
const editRoutine = async (routine) => {
  if (routine.id_rutina !== routineForm.id_rutina && !confirmDiscard()) return;
  routineForm.id_rutina = routine.id_rutina;
  routineForm.servicio = routine.servicio || 'fitness';
  routineForm.nombre_rutina = routine.nombre_rutina || '';
  routineForm.zonas_musculares = routine.zonas_musculares || '';
  routineForm.color = routine.color || 'Azul';
  editSnapshot.value = {
    servicio: routineForm.servicio,
    nombre_rutina: routineForm.nombre_rutina,
    zonas_musculares: routineForm.zonas_musculares,
  };
  submitted.value = false;
  touched.nombre_rutina = false;
  touched.zonas_musculares = false;
  feedback.value = '';

  await nextTick();
  formTop.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

/**
 * Valida y guarda (crea o actualiza) la rutina.
 */
const saveRoutine = async () => {
  submitted.value = true;
  if (Object.keys(errors.value).length) {
    feedbackTone.value = 'error';
    feedback.value = 'Revisa los campos marcados antes de guardar.';
    return;
  }

  const wasEditing = isEditing.value;
  try {
    isSaving.value = true;
    feedback.value = '';
    await gymStore.upsertTrainerRoutine({
      ...routineForm,
      nombre_rutina: routineForm.nombre_rutina.trim(),
      zonas_musculares: routineForm.zonas_musculares.trim(),
    });
    feedbackTone.value = 'success';
    feedback.value = wasEditing ? 'Rutina actualizada.' : 'Rutina guardada.';
    resetRoutineForm();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la rutina.';
  } finally {
    isSaving.value = false;
  }
};

/**
 * Recarga las rutinas desde el servidor.
 */
const refresh = async () => {
  try {
    isLoading.value = true;
    errorMessage.value = '';
    await gymStore.fetchTrainerOverview();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'No se pudo cargar rutinas.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(refresh);
</script>

<style scoped>
/* ---------- Variables de tema (modo oscuro por defecto) ---------- */
.catalog-root {
  --box-border: rgba(255, 255, 255, 0.1);
  --accent: #dc2626;
  --accent-hover: #b91c1c;
  --accent-soft: rgba(220, 38, 38, 0.18);
  --accent-text: #fca5a5;
  --chip-text: #cbd5e1;
}

/* ---------- Modo claro ----------
   IMPORTANTE: ajusta estos selectores a como tu app activa el modo claro
   (mira el <html> en DevTools). Deja solo el que uses. */
:global(.light) .catalog-root,
:global([data-theme='light']) .catalog-root,
:global(.theme-light) .catalog-root {
  --box-border: rgba(15, 23, 42, 0.3);
  --accent-soft: rgba(220, 38, 38, 0.12);
  --accent-text: #b91c1c;
  --chip-text: #334155;
}

/* Todas las cajas de este componente usan border-white/10: las unifico aqui */
.catalog-root [class*='border-white/10'] {
  border-color: var(--box-border) !important;
}

.field-input {
  width: 100%;
  border: 1px solid var(--box-border);
  border-radius: 1rem;
  background: rgba(2, 6, 23, 0.72);
  padding: 0.75rem 1rem;
  color: white;
  outline: none;
}

.field-input::placeholder {
  color: #64748b;
}

.field-input:focus {
  border-color: var(--accent);
}

.field-error {
  border-color: rgba(251, 113, 133, 0.7);
}

/* ---------- Chips de filtro ---------- */
.chip {
  border-radius: 9999px;
  padding: 0.35rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 700;
  border: 1px solid var(--box-border);
  transition: background 0.15s, color 0.15s;
}

.chip-idle {
  color: var(--chip-text);
}

.chip-idle:hover {
  background: var(--accent-soft);
}

.chip-active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.chip-active:hover {
  background: var(--accent-hover);
}

/* ---------- Acentos rojos ---------- */
.accent-text {
  color: var(--accent-text);
}

.accent-badge {
  background: var(--accent-soft);
  color: var(--accent-text);
}

.accent-border {
  border-color: var(--accent);
}

/* ---------- Boton nueva rutina ---------- */
.new-btn {
  border-radius: 9999px;
  padding: 0.4rem 0.9rem;
  font-size: 0.8rem;
  font-weight: 800;
  color: #fff;
  background: var(--accent);
  white-space: nowrap;
}

.new-btn:hover {
  background: var(--accent-hover);
}
</style>