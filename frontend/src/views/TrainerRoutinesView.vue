<template>
  <div class="space-y-6">
    <!-- Header principal -->
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Catálogo de Rutinas</p>
          <h1 class="mt-1 text-3xl font-black text-white">Supervisión & Gestión de Rutinas</h1>
          <p class="mt-1 text-sm text-slate-300">Diseña, edita y organiza las rutinas personalizadas del catálogo para los servicios del gimnasio.</p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button class="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-3 text-sm font-extrabold text-white transition hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20" @click="openCreateModal">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Crear nueva rutina
          </button>
          <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white transition hover:bg-slate-800" @click="refresh">
            Actualizar
          </button>
        </div>
      </div>
    </section>

    <!-- Tarjetas KPI -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Total Rutinas</p>
          <span class="rounded-full bg-cyan-400/10 p-2 text-cyan-300 border border-cyan-400/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-white">{{ routines.length }}</p>
        <p class="mt-1 text-xs text-slate-400">Rutinas en el catálogo general</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Con Ejercicios</p>
          <span class="rounded-full bg-emerald-400/10 p-2 text-emerald-300 border border-emerald-400/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-emerald-300">{{ routinesWithExercisesCount }}</p>
        <p class="mt-1 text-xs text-slate-400">Listas para ser asignadas a clientes</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Promedio Ejercicios</p>
          <span class="rounded-full bg-blue-400/10 p-2 text-blue-300 border border-blue-400/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-blue-300">{{ averageExercisesPerRoutine }}</p>
        <p class="mt-1 text-xs text-slate-400">Ejercicios promedio por rutina</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Servicios Cubiertos</p>
          <span class="rounded-full bg-purple-400/10 p-2 text-purple-300 border border-purple-400/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-purple-300">{{ activeServicesCount }} / {{ serviceOptions.length }}</p>
        <p class="mt-1 text-xs text-slate-400">Categorías con rutinas creadas</p>
      </div>
    </section>

    <!-- Sección de Filtros y Tabla -->
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur space-y-4">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Catálogo Registrado</p>
          <h2 class="text-xl font-black text-white">Lista de Rutinas Registradas</h2>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Buscador con icono perfectamente alineado -->
          <div class="relative w-full sm:w-72">
            <svg class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input v-model="searchQuery" type="text" placeholder="Buscar por nombre o zonas..." class="field-input search-input text-xs pr-4 py-2.5" />
          </div>
        </div>
      </div>

      <!-- Filtros por servicio -->
      <div class="flex flex-wrap gap-2 border-b border-white/10 pb-4">
        <button class="rounded-xl px-3.5 py-2 text-xs font-bold transition" :class="selectedServiceFilter === 'todos' ? 'bg-cyan-400 text-slate-950 shadow-md shadow-cyan-400/20' : 'bg-slate-900/80 text-slate-300 border border-white/10 hover:bg-slate-800'" @click="selectedServiceFilter = 'todos'">
          Todos ({{ routines.length }})
        </button>
        <button v-for="service in serviceOptions" :key="service.value" class="rounded-xl px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5" :class="selectedServiceFilter === service.value ? 'bg-cyan-400 text-slate-950 shadow-md shadow-cyan-400/20' : 'bg-slate-900/80 text-slate-300 border border-white/10 hover:bg-slate-800'" @click="selectedServiceFilter = service.value">
          <span>{{ service.label }}</span>
          <span class="rounded-full px-2 py-0.5 text-[10px] font-extrabold" :class="selectedServiceFilter === service.value ? 'bg-slate-950/20 text-slate-950' : 'bg-white/10 text-slate-300'">
            {{ routinesForService(service.value).length }}
          </span>
        </button>
      </div>

      <!-- Tabla de Rutinas Registradas -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-300">
          <thead class="bg-slate-950/60 text-xs uppercase text-slate-400 tracking-wider">
            <tr>
              <th class="p-3.5 rounded-l-xl">Servicio</th>
              <th class="p-3.5">Nombre de la Rutina</th>
              <th class="p-3.5">Zonas Musculares</th>
              <th class="p-3.5 text-center">N° Ejercicios</th>
              <th class="p-3.5 text-right rounded-r-xl">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr v-for="routine in filteredRoutines" :key="routine.id_rutina" class="transition hover:bg-white/[0.03]">
              <td class="p-3.5">
                <span class="inline-block rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-bold text-cyan-300">
                  {{ serviceLabel(routine.servicio) }}
                </span>
              </td>
              <td class="p-3.5">
                <p class="font-bold text-white text-base">{{ routine.nombre_rutina || 'Sin nombre' }}</p>
              </td>
              <td class="p-3.5">
                <span class="text-xs text-slate-300 bg-slate-900/80 px-2.5 py-1 rounded-lg border border-white/5 inline-block">
                  {{ routine.zonas_musculares || 'General' }}
                </span>
              </td>
              <td class="p-3.5 text-center">
                <span class="rounded-full px-2.5 py-1 text-xs font-black" :class="(routine.ejercicios || []).length ? 'bg-emerald-400/20 text-emerald-300 border border-emerald-400/30' : 'bg-slate-800 text-slate-400'">
                  {{ (routine.ejercicios || []).length }} ej.
                </span>
              </td>
              <td class="p-3.5 text-right">
                <button class="rounded-xl border border-white/10 bg-cyan-400/10 px-4 py-2 text-xs font-extrabold text-cyan-200 transition hover:bg-cyan-400 hover:text-slate-950" @click="editRoutine(routine)">
                  Editar rutina
                </button>
              </td>
            </tr>

            <tr v-if="!filteredRoutines.length">
              <td colspan="5" class="py-8 text-center text-slate-400">
                <p class="text-sm">No se encontraron rutinas registradas en esta categoría o búsqueda.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- MODAL DE CREACIÓN / EDICIÓN DE RUTINA (TELEPORTED TO BODY FOR FULLSCREEN OVERLAY) -->
    <Teleport to="body">
      <div v-if="showRoutineModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md overflow-y-auto">
        <div class="relative w-full max-w-3xl rounded-3xl border border-white/15 bg-slate-900 p-6 shadow-2xl space-y-5 my-8 max-h-[90vh] overflow-y-auto">
          <!-- Encabezado Modal -->
          <div class="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <p class="text-xs uppercase tracking-widest text-cyan-300">Configuración de Catálogo</p>
              <h2 class="text-2xl font-black text-white">
                {{ routineForm.id_rutina ? 'Editar Rutina Registrada' : 'Crear Nueva Rutina' }}
              </h2>
            </div>
            <button class="rounded-full bg-white/10 p-2 text-slate-300 hover:bg-white/20 hover:text-white transition" @click="closeRoutineModal">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form class="space-y-5" @submit.prevent="saveRoutine">
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="space-y-1.5">
                <span class="text-xs font-bold text-slate-300">Servicio Asociado</span>
                <select v-model="routineForm.servicio" class="field-input text-sm">
                  <option v-for="service in serviceOptions" :key="service.value" :value="service.value">{{ service.label }}</option>
                </select>
              </label>
              <label class="space-y-1.5">
                <span class="text-xs font-bold text-slate-300">Nombre de la Rutina</span>
                <input v-model="routineForm.nombre_rutina" class="field-input text-sm" placeholder="Ej. Hipertrofia Tren Superior" required />
              </label>
            </div>

            <label class="block space-y-1.5">
              <span class="text-xs font-bold text-slate-300">Zonas Musculares Trabajadas</span>
              <input v-model="routineForm.zonas_musculares" class="field-input text-sm" placeholder="Ej. Pecho, Espalda, Hombros, Tríceps" />
            </label>

            <!-- CONSTRUCTOR DE EJERCICIOS CON SELECTOR CLARO DE MODO DE REPETICIÓN -->
            <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-4 space-y-4">
              <div class="flex items-center justify-between border-b border-white/10 pb-3">
                <div>
                  <h3 class="font-bold text-cyan-200 text-sm">Lista de Ejercicios</h3>
                  <p class="text-xs text-slate-400">Agrega los ejercicios detallando series, tipo de repeticiones, descanso y peso sugerido.</p>
                </div>
                <button type="button" class="rounded-xl bg-cyan-400/20 px-3.5 py-1.5 text-xs font-bold text-cyan-200 hover:bg-cyan-400 hover:text-slate-950 transition" @click="addExercise">
                  + Agregar Ejercicio
                </button>
              </div>

              <div v-if="routineForm.ejercicios.length" class="space-y-4">
                <div v-for="(ex, index) in routineForm.ejercicios" :key="index" class="rounded-2xl border border-white/10 bg-slate-900/90 p-4 space-y-3 shadow-inner">
                  <div class="flex items-center justify-between border-b border-white/5 pb-2">
                    <span class="text-xs font-black text-cyan-400">Ejercicio #{{ index + 1 }}</span>
                    <button type="button" class="text-xs font-bold text-rose-400 hover:text-rose-300 hover:underline" @click="removeExercise(index)">
                      Eliminar
                    </button>
                  </div>

                  <!-- Campos principales: Nombre y Músculo Objetivo -->
                  <div class="grid gap-3 sm:grid-cols-2">
                    <label class="space-y-1">
                      <span class="text-[11px] font-bold text-slate-300">Nombre del Ejercicio</span>
                      <input v-model="ex.nombre_ejercicio" class="field-input text-xs" placeholder="Ej. Press de Banca Plano" required />
                    </label>
                    <label class="space-y-1">
                      <span class="text-[11px] font-bold text-slate-300">Músculo Objetivo (opcional)</span>
                      <input v-model="ex.grupo_muscular" class="field-input text-xs" placeholder="Ej. Pectoral mayor / Tríceps" />
                    </label>
                  </div>

                  <!-- Configuración de Series, Tipo de Repeticiones y Descanso -->
                  <div class="grid grid-cols-1 gap-3 sm:grid-cols-4 items-start pt-1">
                    <!-- Series -->
                    <label class="space-y-1">
                      <span class="text-[11px] font-bold text-slate-300">Series</span>
                      <input v-model.number="ex.series" type="number" min="1" max="20" class="field-input text-xs" />
                    </label>

                    <!-- Selector de Modo de Repetición (Fijo / Rango / Al fallo) -->
                    <div class="space-y-1 sm:col-span-2">
                      <span class="text-[11px] font-bold text-slate-300">Repeticiones</span>
                      
                      <!-- Pestañas de modo -->
                      <div class="flex items-center gap-1 rounded-xl bg-slate-950/80 p-1 border border-white/10">
                        <button 
                          type="button" 
                          class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                          :class="ex.rep_modo === 'fijo' ? 'bg-cyan-400 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-white'"
                          @click="setRepMode(ex, 'fijo')"
                        >
                          Número Fijo
                        </button>
                        <button 
                          type="button" 
                          class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                          :class="ex.rep_modo === 'rango' ? 'bg-cyan-400 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-white'"
                          @click="setRepMode(ex, 'rango')"
                        >
                          Rango (ej. 10-12)
                        </button>
                        <button 
                          type="button" 
                          class="flex-1 rounded-lg py-1 text-[11px] font-bold transition"
                          :class="ex.rep_modo === 'fallo' ? 'bg-cyan-400 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-white'"
                          @click="setRepMode(ex, 'fallo')"
                        >
                          Al Fallo
                        </button>
                      </div>

                      <!-- Input dinámico según modo -->
                      <div v-if="ex.rep_modo === 'fijo'" class="pt-1">
                        <input 
                          v-model="ex.rep_fijo" 
                          type="number" 
                          min="1" 
                          placeholder="Ej. 10 o 12" 
                          class="field-input text-xs"
                          @input="syncRepString(ex)"
                        />
                      </div>

                      <div v-else-if="ex.rep_modo === 'rango'" class="flex items-center gap-2 pt-1">
                        <input 
                          v-model="ex.rep_min" 
                          type="number" 
                          min="1" 
                          placeholder="Mín (ej. 10)" 
                          class="field-input text-xs"
                          @input="syncRepString(ex)"
                        />
                        <span class="text-xs text-slate-400 font-bold">a</span>
                        <input 
                          v-model="ex.rep_max" 
                          type="number" 
                          min="1" 
                          placeholder="Máx (ej. 12)" 
                          class="field-input text-xs"
                          @input="syncRepString(ex)"
                        />
                      </div>

                      <div v-else-if="ex.rep_modo === 'fallo'" class="pt-1">
                        <div class="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-center text-xs font-bold text-rose-300">
                          🔥 Repeticiones hasta el fallo (AMRAP)
                        </div>
                      </div>
                    </div>

                    <!-- Descanso -->
                    <label class="space-y-1">
                      <span class="text-[11px] font-bold text-slate-300">Descanso</span>
                      <select v-model.number="ex.descanso_segundos" class="field-input text-xs">
                        <option :value="30">30 seg</option>
                        <option :value="45">45 seg</option>
                        <option :value="60">60 seg (1 min)</option>
                        <option :value="90">90 seg (1.5 min)</option>
                        <option :value="120">120 seg (2 min)</option>
                        <option :value="180">180 seg (3 min)</option>
                      </select>
                    </label>
                  </div>

                  <!-- Peso sugerido (kg) -->
                  <div class="pt-2 border-t border-white/5 flex items-center justify-between">
                    <label class="flex items-center gap-3 w-full sm:w-1/2">
                      <span class="text-[11px] font-bold text-slate-300 whitespace-nowrap">Peso sug. (kg):</span>
                      <input v-model.number="ex.peso_sugerido_kg" type="number" step="0.5" min="0" class="field-input text-xs" placeholder="Opcional (ej. 60)" />
                    </label>
                  </div>
                </div>
              </div>

              <p v-else class="text-center text-xs text-slate-400 py-4 border border-dashed border-white/10 rounded-xl">
                No has agregado ejercicios a esta rutina aún. Haz clic en "+ Agregar Ejercicio".
              </p>
            </div>

            <!-- Botones de Acción Modal -->
            <div class="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
              <button type="button" class="rounded-2xl border border-white/10 bg-slate-800 px-5 py-2.5 text-xs font-bold text-white transition hover:bg-slate-700" @click="closeRoutineModal">
                Cancelar
              </button>
              <button class="rounded-2xl bg-cyan-400 px-6 py-2.5 text-xs font-extrabold text-slate-950 transition hover:bg-cyan-300 shadow-lg shadow-cyan-400/20 disabled:opacity-60" :disabled="isSaving">
                {{ isSaving ? 'Guardando...' : (routineForm.id_rutina ? 'Actualizar Rutina' : 'Guardar Rutina') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- TOAST DE NOTIFICACIÓN FLOTANTE (TELEPORTED TO BODY) -->
    <Teleport to="body">
      <div v-if="toastMessage" class="fixed bottom-6 right-6 z-50 max-w-sm animate-bounce-short">
        <div class="flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-md" :class="toastType === 'error' ? 'border-rose-400/30 bg-rose-950/90 text-rose-100' : 'border-emerald-400/30 bg-emerald-950/90 text-emerald-100'">
          <span class="rounded-full p-1" :class="toastType === 'error' ? 'bg-rose-400/20 text-rose-300' : 'bg-emerald-400/20 text-emerald-300'">
            <svg v-if="toastType === 'error'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </span>
          <p class="text-xs font-bold">{{ toastMessage }}</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const isSaving = ref(false);
const showRoutineModal = ref(false);
const searchQuery = ref('');
const selectedServiceFilter = ref('todos');

// Toasts flotantes
const toastMessage = ref('');
const toastType = ref('success');
let toastTimer = null;

const showToast = (message, type = 'success') => {
  toastMessage.value = message;
  toastType.value = type;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = '';
  }, 4000);
};

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

// Métricas KPI
const routinesWithExercisesCount = computed(() => routines.value.filter((r) => Array.isArray(r.ejercicios) && r.ejercicios.length > 0).length);

const averageExercisesPerRoutine = computed(() => {
  if (!routines.value.length) return 0;
  const totalEx = routines.value.reduce((acc, r) => acc + (Array.isArray(r.ejercicios) ? r.ejercicios.length : 0), 0);
  return (totalEx / routines.value.length).toFixed(1);
});

const activeServicesCount = computed(() => {
  const serviceSet = new Set(routines.value.map((r) => String(r.servicio || '').toLowerCase()));
  return serviceSet.size;
});

// Filtros y búsqueda
const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';

const routinesForService = (service) => routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(service || '').toLowerCase());

const filteredRoutines = computed(() => {
  return routines.value.filter((r) => {
    const matchesService = selectedServiceFilter.value === 'todos' || String(r.servicio || '').toLowerCase() === String(selectedServiceFilter.value).toLowerCase();
    const query = searchQuery.value.toLowerCase().trim();
    const matchesSearch = !query || String(r.nombre_rutina || '').toLowerCase().includes(query) || String(r.zonas_musculares || '').toLowerCase().includes(query);
    return matchesService && matchesSearch;
  });
});

// Ayudantes de parsing y sincronización de modos de repetición
const parseRepeticiones = (repStr) => {
  const str = String(repStr || '').trim();
  if (str.toLowerCase().includes('fallo')) {
    return { rep_modo: 'fallo', rep_fijo: '', rep_min: '', rep_max: '', repeticiones: 'Al fallo' };
  }
  if (str.includes('-')) {
    const parts = str.split('-');
    return {
      rep_modo: 'rango',
      rep_fijo: '',
      rep_min: (parts[0] || '10').trim(),
      rep_max: (parts[1] || '12').trim(),
      repeticiones: str,
    };
  }
  return {
    rep_modo: 'fijo',
    rep_fijo: str || '10',
    rep_min: '',
    rep_max: '',
    repeticiones: str || '10',
  };
};

const setRepMode = (ex, mode) => {
  ex.rep_modo = mode;
  if (mode === 'fijo' && !ex.rep_fijo) ex.rep_fijo = '10';
  if (mode === 'rango') {
    if (!ex.rep_min) ex.rep_min = '10';
    if (!ex.rep_max) ex.rep_max = '12';
  }
  syncRepString(ex);
};

const syncRepString = (ex) => {
  if (ex.rep_modo === 'fijo') {
    ex.repeticiones = String(ex.rep_fijo || '10');
  } else if (ex.rep_modo === 'rango') {
    const minVal = ex.rep_min || '10';
    const maxVal = ex.rep_max || '12';
    ex.repeticiones = `${minVal}-${maxVal}`;
  } else if (ex.rep_modo === 'fallo') {
    ex.repeticiones = 'Al fallo';
  }
};

// Métodos Modal & Ejercicios
const openCreateModal = () => {
  resetRoutineForm();
  showRoutineModal.value = true;
};

const closeRoutineModal = () => {
  showRoutineModal.value = false;
  resetRoutineForm();
};

const addExercise = () => {
  const newEx = {
    nombre_ejercicio: '',
    series: 3,
    rep_modo: 'rango',
    rep_fijo: '10',
    rep_min: '10',
    rep_max: '12',
    repeticiones: '10-12',
    descanso_segundos: 60,
    peso_sugerido_kg: null,
    grupo_muscular: '',
    notas: '',
  };
  routineForm.ejercicios.push(newEx);
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
  routineForm.ejercicios = Array.isArray(routine.ejercicios)
    ? routine.ejercicios.map((ex) => ({
        ...ex,
        ...parseRepeticiones(ex.repeticiones),
      }))
    : [];
  showRoutineModal.value = true;
};

const saveRoutine = async () => {
  try {
    isSaving.value = true;
    // Asegurar que cada ejercicio tenga la cadena repeticiones formateada
    const cleanEjercicios = routineForm.ejercicios.map((ex) => {
      syncRepString(ex);
      return {
        nombre_ejercicio: ex.nombre_ejercicio,
        grupo_muscular: ex.grupo_muscular || '',
        series: Number(ex.series || 3),
        repeticiones: String(ex.repeticiones || '10-12'),
        descanso_segundos: Number(ex.descanso_segundos || 60),
        peso_sugerido_kg: ex.peso_sugerido_kg !== null && ex.peso_sugerido_kg !== '' ? Number(ex.peso_sugerido_kg) : null,
        notas: ex.notas || '',
      };
    });

    await gymStore.upsertTrainerRoutine({
      ...routineForm,
      ejercicios: cleanEjercicios,
    });
    showToast(routineForm.id_rutina ? 'Rutina actualizada exitosamente.' : 'Nueva rutina creada exitosamente.', 'success');
    closeRoutineModal();
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo guardar la rutina.', 'error');
  } finally {
    isSaving.value = false;
  }
};

const refresh = async () => {
  try {
    await gymStore.fetchTrainerOverview();
    showToast('Datos del catálogo actualizados.', 'success');
  } catch (error) {
    showToast(error instanceof Error ? error.message : 'No se pudo cargar rutinas.', 'error');
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

.search-input {
  padding-left: 2.75rem !important;
}

@keyframes bounceShort {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.animate-bounce-short {
  animation: bounceShort 0.3s ease-in-out;
}
</style>
