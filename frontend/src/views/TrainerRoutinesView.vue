<template>
  <div class="space-y-6 text-white">
    <!-- Header principal -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-red-500 font-extrabold flex items-center gap-2">
            <i class="fa-solid fa-dumbbell"></i>
            Catálogo de Rutinas
          </p>
          <h1 class="mt-1 text-3xl font-black text-white">Supervisión & Gestión de Rutinas</h1>
          <p class="mt-1 text-sm text-slate-400">Diseña, edita y organiza las rutinas personalizadas del catálogo para los servicios del gimnasio.</p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button class="flex items-center gap-2 rounded-2xl bg-red-600 px-5 py-3 text-sm font-extrabold text-white transition hover:bg-red-500 shadow-lg shadow-red-600/20" @click="openCreateModal">
            <i class="fa-solid fa-plus"></i>
            Crear nueva rutina
          </button>
          <button class="flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-sm font-bold text-white transition hover:bg-slate-800 disabled:opacity-60" :disabled="isLoading" @click="refresh()">
            <i class="fa-solid fa-rotate-right" :class="{ 'fa-spin': isLoading }"></i>
            {{ isLoading ? 'Actualizando...' : 'Actualizar' }}
          </button>
        </div>
      </div>
    </section>

    <p v-if="errorMessage" class="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">{{ errorMessage }}</p>

    <!-- Tarjetas KPI -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Total Rutinas</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i class="fa-solid fa-list-check text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-white">{{ routines.length }}</p>
        <p class="mt-1 text-xs text-slate-400">Rutinas en el catálogo general</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Con Ejercicios</p>
          <span class="rounded-full bg-emerald-500/10 p-2.5 text-emerald-400 border border-emerald-500/20">
            <i class="fa-solid fa-circle-check text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-emerald-400">{{ routinesWithExercisesCount }}</p>
        <p class="mt-1 text-xs text-slate-400">Listas para ser asignadas a clientes</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Promedio Ejercicios</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i class="fa-solid fa-bolt text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-red-400">{{ averageExercisesPerRoutine }}</p>
        <p class="mt-1 text-xs text-slate-400">Ejercicios promedio por rutina</p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">Servicios Cubiertos</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i class="fa-solid fa-layer-group text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-white">{{ activeServicesCount }} / {{ serviceOptions.length }}</p>
        <p class="mt-1 text-xs text-slate-400">Categorías con rutinas creadas</p>
      </div>
    </section>

    <!-- Sección de Filtros y Tabla -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur space-y-4">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Catálogo Registrado</p>
          <h2 class="text-xl font-black text-white">Lista de Rutinas Registradas</h2>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Selector de cantidad de filas por página (5, 7, 10) -->
          <div class="flex items-center gap-2 text-xs font-bold text-slate-400">
            <span>Ver:</span>
            <div class="flex items-center gap-1 rounded-xl bg-slate-900 p-1 border border-white/10">
              <button
                v-for="size in [5, 7, 10]"
                :key="size"
                type="button"
                class="px-2.5 py-1 rounded-lg font-black text-xs transition"
                :class="itemsPerPage === size ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                @click="setItemsPerPage(size)"
              >
                {{ size }}
              </button>
            </div>
          </div>

          <!-- Orden -->
          <select v-model="sortBy" class="field-input !w-auto text-xs py-2.5" aria-label="Ordenar rutinas">
            <option value="nombre">A-Z</option>
            <option value="ejercicios">Más ejercicios</option>
            <option value="asignados">Más asignadas</option>
          </select>
          <!-- Buscador -->
          <div class="relative w-full sm:w-64">
            <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
            <SearchInput v-model="searchQuery" placeholder="Buscar por nombre, zona o ejercicio..." class="field-input search-input text-xs pr-4 py-2.5" />
          </div>
        </div>
      </div>

      <!-- Filtros por servicio -->
      <div class="flex flex-wrap gap-2 border-b border-white/10 pb-4">
        <button class="rounded-xl px-3.5 py-2 text-xs font-bold transition" :class="selectedServiceFilter === 'todos' ? 'bg-red-600 text-white shadow-md shadow-red-600/20' : 'bg-slate-900 text-slate-300 border border-white/10 hover:bg-slate-800'" @click="setServiceFilter('todos')">
          Todos ({{ routines.length }})
        </button>
        <button v-for="service in serviceOptions" :key="service.value" class="rounded-xl px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5" :class="selectedServiceFilter === service.value ? 'bg-red-600 text-white shadow-md shadow-red-600/20' : 'bg-slate-900 text-slate-300 border border-white/10 hover:bg-slate-800'" @click="setServiceFilter(service.value)">
          <span>{{ service.label }}</span>
          <span class="rounded-full px-2 py-0.5 text-[10px] font-extrabold" :class="selectedServiceFilter === service.value ? 'bg-black/40 text-white' : 'bg-white/10 text-slate-300'">
            {{ routinesForService(service.value).length }}
          </span>
        </button>
      </div>

      <!-- Tabla de Rutinas Registradas -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-300">
          <thead class="bg-black/60 text-xs uppercase text-slate-400 tracking-wider">
            <tr>
              <th class="p-3.5 rounded-l-xl">Servicio</th>
              <th class="p-3.5">Nombre de la Rutina</th>
              <th class="p-3.5">Zonas Musculares</th>
              <th class="p-3.5 text-center">N° Ejercicios</th>
              <th class="p-3.5 text-center">Clientes asignados</th>
              <th class="p-3.5 text-right rounded-r-xl">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr v-for="routine in paginatedRoutines" :key="routine.id_rutina" class="transition hover:bg-white/[0.03]">
              <td class="p-3.5">
                <span class="inline-block rounded-full border border-red-600/30 bg-red-600/10 px-3 py-1 text-xs font-bold text-red-400">
                  {{ serviceLabel(routine.servicio) }}
                </span>
              </td>
              <td class="p-3.5">
                <p class="font-bold text-white text-base">{{ routine.nombre_rutina || 'Sin nombre' }}</p>
                <p v-if="Number(routine.clientes_asignados || 0) > 0" class="mt-0.5 text-xs text-slate-400">
                  {{ routine.clientes_asignados }} {{ Number(routine.clientes_asignados) === 1 ? 'cliente asignado' : 'clientes asignados' }}
                </p>
              </td>
              <td class="p-3.5">
                <span class="text-xs text-slate-300 bg-slate-900 px-2.5 py-1 rounded-lg border border-white/5 inline-block">
                  {{ routine.zonas_musculares || 'General' }}
                </span>
              </td>
              <td class="p-3.5 text-center">
                <span class="rounded-full px-2.5 py-1 text-xs font-black" :class="(routine.ejercicios || []).length ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'">
                  {{ (routine.ejercicios || []).length }} ej.
                </span>
              </td>
              <td class="p-3.5 text-center">{{ routine.clientes_asignados || 0 }}</td>
              <td class="p-3.5 text-right">
                <button class="rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-xs font-extrabold text-white transition hover:bg-red-600 hover:border-red-600 flex items-center gap-1.5 ml-auto" @click="editRoutine(routine)">
                  <i class="fa-solid fa-pen-to-square text-xs text-red-400"></i>
                  <span>Editar rutina</span>
                </button>
              </td>
            </tr>

            <tr v-if="!filteredRoutines.length">
              <td colspan="6" class="py-8 text-center text-slate-400">
                <p v-if="!routines.length" class="text-sm">Aún no hay rutinas registradas.</p>
                <template v-else>
                  <p class="text-sm">Ninguna rutina coincide con los filtros.</p>
                  <button type="button" class="mt-3 text-xs font-bold text-red-400 underline hover:text-red-300" @click="clearFilters">Limpiar filtros</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginación Inferior de la Tabla -->
      <div v-if="filteredRoutines.length > 0" class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t border-white/10 pt-4 text-xs font-bold text-slate-400">
        <p>
          Mostrando <span class="text-white font-black">{{ showingStart }}</span> a <span class="text-white font-black">{{ showingEnd }}</span> de <span class="text-white font-black">{{ filteredRoutines.length }}</span> rutinas
        </p>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-xl border border-white/10 bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <i class="fa-solid fa-chevron-left text-[10px]"></i>
            <span>Anterior</span>
          </button>

          <div class="flex items-center gap-1">
            <button
              v-for="page in totalPages"
              :key="page"
              type="button"
              class="h-7 w-7 rounded-lg text-xs font-black transition flex items-center justify-center"
              :class="currentPage === page ? 'bg-red-600 text-white shadow-sm shadow-red-600/30' : 'bg-slate-900 text-slate-400 border border-white/10 hover:bg-slate-800 hover:text-white'"
              @click="currentPage = page"
            >
              {{ page }}
            </button>
          </div>

          <button
            type="button"
            class="rounded-xl border border-white/10 bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <span>Siguiente</span>
            <i class="fa-solid fa-chevron-right text-[10px]"></i>
          </button>
        </div>
      </div>
    </section>

    <!-- MODAL DE CREACIÓN / EDICIÓN DE RUTINA (TELEPORTED TO BODY FOR FULLSCREEN OVERLAY) -->
    <TrainerRoutineEditorDialog
      :max-nombre="MAX_NOMBRE" :max-zonas="MAX_ZONAS" :is-saving="isSaving" :show-routine-modal="showRoutineModal"
      :service-options="serviceOptions" :quick-zones="quickZones" :routine-form="routineForm" :touched="touched"
      :submitted="submitted" :editing-name="editingName" :has-changes="hasChanges" :editing-assigned-count="editingAssignedCount"
      :errors="errors" :field-error="fieldError" :ex-error="exError" :zone-active="zoneActive"
      @close="requestCloseModal" @save="saveRoutine" @toggle-zone="toggleZone" @add-exercise="addExercise"
      @remove-exercise="removeExercise" @rep-mode="setRepMode" @sync-reps="syncRepString" />

    <!-- TOAST DE NOTIFICACIÓN FLOTANTE (TELEPORTED TO BODY) -->
    <Teleport to="body">
      <div v-if="toastMessage" class="fixed bottom-6 right-6 z-50 max-w-sm animate-bounce-short">
        <div class="flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-md" :class="toastType === 'error' ? 'border-red-500/40 bg-slate-950 text-red-200 shadow-red-950/50' : 'border-emerald-500/40 bg-slate-950 text-emerald-200 shadow-emerald-950/50'">
          <span class="rounded-full p-1" :class="toastType === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'">
            <i v-if="toastType === 'error'" class="fa-solid fa-circle-exclamation text-base"></i>
            <i v-else class="fa-solid fa-circle-check text-base"></i>
          </span>
          <p class="text-xs font-bold">{{ toastMessage }}</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import TrainerRoutineEditorDialog from '../components/trainer/TrainerRoutineEditorDialog.vue';
import SearchInput from '../components/SearchInput.vue';
import { useTrainerRoutines } from '../composables/trainer/useTrainerRoutines.js';

const {
  gymStore, MAX_NOMBRE, MAX_ZONAS, MAX_EJERCICIO, isSaving,
  isLoading, errorMessage, showRoutineModal, searchQuery, selectedServiceFilter,
  sortBy, itemsPerPage, currentPage, setItemsPerPage, setServiceFilter,
  toastMessage, toastType, toastTimer, showToast, serviceOptions,
  quickZones, routineForm, touched, submitted, baselineSignature,
  editingName, overview, routines, norm, routinesWithExercisesCount,
  averageExercisesPerRoutine, activeServicesCount, serviceLabel, routinesForService, exerciseCount,
  filteredRoutines, clearFilters, totalPages, paginatedRoutines, showingStart,
  showingEnd, parseRepeticiones, buildRepString, syncRepString, setRepMode,
  buildExercise, buildPayload, buildSignature, hasChanges, editingAssignedCount,
  exerciseErrors, errors, fieldError, exError, zoneActive,
  toggleZone, addExercise, removeExercise, resetRoutineForm, openModal,
  openCreateModal, editRoutine, closeRoutineModal, requestCloseModal, saveRoutine,
  refresh,
} = useTrainerRoutines();
</script>

<style scoped src="../styles/trainer-routines.css"></style>
