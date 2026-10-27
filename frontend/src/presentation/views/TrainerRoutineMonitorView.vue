<template>
  <div class="space-y-6 relative text-white">
    <!-- TOAST NOTIFICATION CONTAINER (FLOTANTE EN ESQUINA INFERIOR DERECHA) -->
    <Teleport to="body">
      <div
        v-if="toast.show"
        class="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border px-5 py-4 shadow-2xl backdrop-blur-xl transition-all animate-bounce-short"
        :class="
          toast.type === 'error'
            ? 'border-red-500/40 bg-slate-950 text-red-200 shadow-red-950/50'
            : 'border-emerald-500/40 bg-slate-950 text-emerald-200 shadow-emerald-950/50'
        "
      >
        <div
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-bold"
          :class="
            toast.type === 'error'
              ? 'bg-red-500/20 text-red-400'
              : 'bg-emerald-500/20 text-emerald-400'
          "
        >
          <i
            v-if="toast.type === 'error'"
            class="fa-solid fa-circle-exclamation text-base"
          ></i>
          <i v-else class="fa-solid fa-circle-check text-base"></i>
        </div>
        <div>
          <p class="text-[11px] uppercase tracking-wider font-bold opacity-70">
            {{
              toast.type === 'error'
                ? 'Error u Operación Fallida'
                : 'Notificación del Sistema'
            }}
          </p>
          <p class="text-xs font-semibold text-white mt-0.5">
            {{ toast.message }}
          </p>
        </div>
        <button
          class="ml-4 text-slate-400 hover:text-white font-bold text-sm"
          @click="toast.show = false"
        >
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </Teleport>

    <!-- Header & Búsqueda (ROJO Y NEGRO) -->
    <section
      class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur"
    >
      <div
        class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div>
          <p
            class="text-xs uppercase tracking-[0.35em] text-red-500 font-extrabold flex items-center gap-2"
          >
            <i class="fa-solid fa-dumbbell"></i>
            Módulo Entrenador
          </p>
          <h1 class="mt-1 text-3xl font-black text-white">
            Supervisión y Seguimiento de Rutinas
          </h1>
          <p class="mt-1 text-sm text-slate-400">
            Consulta alumnos matriculados, asigna nuevas rutinas personalizadas
            y registra el progreso de ejercicios.
          </p>
        </div>
        <!-- Búsqueda de clientes con autocompletado. -->
        <form
          class="flex flex-col gap-3 sm:flex-row"
          @submit.prevent="searchClient"
        >
          <div class="relative min-w-64 sm:w-80">
            <i
              class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs"
            ></i>
            <input
              v-model="dni"
              class="field-input search-input text-xs"
              type="text"
              inputmode="numeric"
              maxlength="8"
              autocomplete="off"
              placeholder="Ingresa DNI del cliente"
              aria-label="DNI del cliente"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="dni-suggestions"
              :aria-expanded="showSuggestions"
              :aria-activedescendant="
                activeIndex >= 0 && showSuggestions
                  ? `dni-option-${activeIndex}`
                  : undefined
              "
              @input="onDniInput"
              @focus="openSuggestions"
              @blur="onDniBlur"
              @keydown.down.prevent="moveActive(1)"
              @keydown.up.prevent="moveActive(-1)"
              @keydown.enter="onEnter"
              @keydown.esc="open = false"
            />
            <ul
              v-if="showSuggestions"
              id="dni-suggestions"
              role="listbox"
              class="relative z-20 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-white/10 bg-slate-950 p-1 shadow-xl sm:absolute"
              @mousedown.prevent
            >
              <li
                v-for="(client, index) in suggestions"
                :id="`dni-option-${index}`"
                :key="client.dni"
                role="option"
                :aria-selected="index === activeIndex"
                class="cursor-pointer rounded-xl px-3 py-2 text-sm"
                :class="
                  index === activeIndex
                    ? 'bg-red-600/25 text-white'
                    : 'text-slate-200 hover:bg-white/10'
                "
                @mousedown.prevent="pickClient(client.dni)"
                @mouseenter="activeIndex = index"
              >
                <span class="font-bold text-red-400">{{
                  client.dni.slice(0, dni.length)
                }}</span
                >{{ client.dni.slice(dni.length) }}
                <span class="ml-2 text-slate-400">· {{ client.nombre }}</span>
              </li>
              <li
                v-if="!suggestions.length"
                class="px-3 py-2 text-sm text-slate-400"
                role="option"
                aria-disabled="true"
                aria-selected="false"
              >
                Ningún cliente con matrícula activa empieza con {{ dni }}.
                Puedes buscar ese DNI directamente.
              </li>
            </ul>
          </div>
          <button
            type="submit"
            class="flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-6 py-3 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/20 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="searching"
          >
            <i class="fa-solid fa-magnifying-glass"></i>
            <span>{{ searching ? 'Buscando…' : 'Buscar Cliente' }}</span>
          </button>
        </form>
      </div>
    </section>

    <p
      v-if="feedback"
      role="status"
      class="rounded-2xl border px-4 py-3 text-sm"
      :class="
        feedbackTone === 'error'
          ? 'border-rose-400/20 bg-rose-400/10 text-rose-50'
          : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'
      "
    >
      {{ feedback }}
    </p>

    <!-- Visual Rest Timer (Flotante en Vista Principal - ROJO Y NEGRO) -->
    <RoutineRestTimer :timer="timer" />

    <!-- Estado 1: ANIMACIÓN DE CARGA GIRATORIA CUANDO ESTÁ BUSCANDO -->
    <section
      v-if="isSearching"
      class="rounded-2xl border border-white/10 bg-slate-950 p-12 text-center backdrop-blur shadow-2xl space-y-4"
    >
      <div class="flex flex-col items-center justify-center gap-4">
        <div class="relative flex h-16 w-16 items-center justify-center">
          <div
            class="absolute h-16 w-16 animate-spin rounded-full border-4 border-red-600 border-t-transparent shadow-lg shadow-red-600/40"
          ></div>
          <i
            class="fa-solid fa-magnifying-glass text-xl text-red-500 animate-pulse"
          ></i>
        </div>
        <div class="space-y-1">
          <p class="text-base font-black text-white">
            Consultando información del cliente...
          </p>
          <p class="text-xs text-slate-400">
            Buscando DNI
            <span class="font-mono font-bold text-red-400">{{ dni }}</span> y
            cargando rutinas asignadas
          </p>
        </div>
      </div>
    </section>

    <!-- Estado 2: Panel de información del Cliente (ROJO Y NEGRO) -->
    <section v-else-if="clientData?.cliente" class="space-y-6">
      <!-- BARRA SUPERIOR DE DATOS DEL CLIENTE -->
      <div
        class="rounded-2xl border border-white/10 bg-slate-950 p-4 backdrop-blur shadow-lg"
      >
        <div
          class="flex flex-wrap items-center justify-between gap-4 text-xs font-semibold text-slate-200"
        >
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-user text-red-500"></i>
            <span class="text-slate-400">Cliente:</span>
            <span class="font-black text-white text-sm">{{
              clientData.cliente.nombre
            }}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-id-card text-red-400"></i>
            <span class="text-slate-400">DNI:</span>
            <span class="font-mono text-red-400 font-bold">{{
              clientData.cliente.dni
            }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Membresía:</span>
            <span
              class="rounded-full px-3 py-0.5 text-xs font-bold"
              :class="
                hasActiveMembership
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'bg-red-500/20 text-red-300 border border-red-500/30'
              "
            >
              {{ membershipLabel }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">Código ID:</span>
            <span class="text-slate-300 font-mono">{{
              clientData.cliente.id_usuario
            }}</span>
          </div>

          <!-- BOTÓN INTEGRADO DE ACCIÓN: + ASIGNAR RUTINA PERSONALIZADA (ROJO SÓLIDO) -->
          <button
            type="button"
            class="flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/20 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!hasActiveMembership"
            @click="openAssignModal"
          >
            <i class="fa-solid fa-plus text-xs"></i>
            <span>Asignar rutina personalizada</span>
          </button>
        </div>
      </div>

      <p
        v-if="!hasActiveMembership"
        class="rounded-2xl border border-orange-400/20 bg-orange-400/10 px-4 py-3 text-sm text-orange-100"
        role="alert"
      >
        {{ clientData.cliente.nombre }} no tiene una matrícula activa. Para
        asignar una rutina, primero debe matricularse en un horario.
      </p>

      <!-- LISTADO DE RUTINAS ASIGNADAS -->
      <div class="space-y-4">
        <TrainerEnrollmentCard
          v-for="item in clientData.matriculas"
          :key="item.id_matricula"
          :item="item"
          :routines="routinesForService(item.servicio)"
          :selected-routine="Number(selectedRoutine(item))"
          :can-assign="canAssign(item)"
          :has-change="hasChange(item)"
          :assigning-id="assigningId"
          :marking-id="markingId"
          @select="selection[item.id_matricula] = $event"
          @exercises="openExercisesModal(item)"
          @unassign="confirmUnassign(item)"
          @assign="assignRoutine(item)"
          @done="markDone(item)"
        />
      </div>
    </section>

    <!-- Estado 3: ESTADO VACÍO PREVIO A LA BÚSQUEDA -->
    <section
      v-else
      class="empty-state-card rounded-2xl border border-dashed border-white/10 bg-slate-900/60 p-12 text-center shadow-lg"
    >
      <div class="mx-auto max-w-sm space-y-3">
        <div
          class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-600/10 text-red-500 font-bold text-2xl border border-red-600/30 shadow-inner"
        >
          <i class="fa-solid fa-magnifying-glass"></i>
        </div>
        <h3 class="text-lg font-black text-white">
          Consulta y Asignación de Alumnos
        </h3>
        <p class="text-xs text-slate-400 leading-relaxed">
          Ingresa el número de DNI del alumno arriba y haz clic en "Buscar
          Cliente" para consultar sus rutinas y registrar progresos.
        </p>
      </div>
    </section>

    <!-- MODAL: Asignar Nueva Rutina Personalizada -->
    <RoutineAssignmentDialog
      v-model:open="showAssignModal"
      v-model:enrollment-id="assignForm.id_matricula"
      v-model:routine-id="assignForm.id_rutina"
      :enrollments="clientData?.matriculas || []"
      :routines="availableRoutinesForSelectedMatricula"
      :can-submit="canSubmitAssign"
      :busy="Boolean(assigningId)"
      @submit="submitAssignRoutine"
    />

    <!-- MODAL ANCHO Y COMPACTO DE EJERCICIOS Y SEGUIMIENTO (TEMA ROJO Y NEGRO - ANCHO MAX 6XL SIN SCROLL VERTICAL) -->
    <RoutineProgressDialog
      v-if="selectedMatriculaItem"
      v-model:open="showExercisesModal"
      v-model:observation="observationsMap[selectedMatriculaItem.id_matricula]"
      :exercises="
        getTracker(
          selectedMatriculaItem.id_matricula,
          selectedMatriculaItem.id_rutina,
        )
      "
      :item="selectedMatriculaItem"
      :timer="timer"
      :saving="isSavingProgress"
      @save="submitSaveProgress"
    />

    <!-- MODAL: Confirmar Desvinculación de Rutina -->
    <RoutineUnassignDialog
      v-model:open="showConfirmModal"
      :item="unassignItem"
      :busy="isUnassigning"
      @confirm="submitUnassign"
    />
  </div>
</template>
<script setup>
import { computed, onMounted, reactive } from 'vue';
import { useGymStore } from '../../application/stores/gymStore';
import { useTrainerFeedback } from '../composables/trainer/useTrainerFeedback.js';
import { useTrainerClientSearch } from '../composables/trainer/useTrainerClientSearch.js';
import { useRoutineAssignments } from '../composables/trainer/useRoutineAssignments.js';
import { useRoutineProgress } from '../composables/trainer/useRoutineProgress.js';
import { useRestTimer } from '../composables/trainer/useRestTimer.js';
import TrainerEnrollmentCard from '../components/trainer/TrainerEnrollmentCard.vue';
import RoutineAssignmentDialog from '../components/trainer/RoutineAssignmentDialog.vue';
import RoutineProgressDialog from '../components/trainer/RoutineProgressDialog.vue';
import RoutineUnassignDialog from '../components/trainer/RoutineUnassignDialog.vue';
import RoutineRestTimer from '../components/trainer/RoutineRestTimer.vue';
const gymStore = useGymStore();
const overview = computed(() => gymStore.trainerOverview || {});
const routines = computed(() => overview.value.routines || []);
const { feedback, feedbackTone, toast, notify, setFeedback, showToast } =
  useTrainerFeedback();
const timer = reactive(useRestTimer());
const {
  dni,
  clientData,
  searching,
  isSearching,
  open,
  activeIndex,
  suggestions,
  showSuggestions,
  onDniInput,
  onDniBlur,
  openSuggestions,
  moveActive,
  onEnter,
  pickClient,
  searchClient,
  reloadClient,
} = useTrainerClientSearch({
  overview,
  loadOverview: () => gymStore.fetchTrainerOverview(),
  loadClient: (dni) => gymStore.fetchTrainerClientRoutines(dni),
  feedback,
  setFeedback,
  showToast,
  onSearchStart: () => {
    assignments.reset();
    showExercisesModal.value = false;
  },
});
const assignments = useRoutineAssignments({
  clientData,
  routines,
  assign: (...args) => gymStore.assignTrainerRoutine(...args),
  reloadClient,
  notify,
  setFeedback,
});
const {
  assigningId,
  isUnassigning,
  selection,
  showAssignModal,
  showConfirmModal,
  unassignItem,
  assignForm,
  hasActiveMembership,
  membershipLabel,
  routinesForService,
  canAssign,
  selectedRoutine,
  hasChange,
  availableRoutinesForSelectedMatricula,
  canSubmitAssign,
  openAssignModal,
  assignRoutine,
  submitAssignRoutine,
  confirmUnassign,
  submitUnassign,
} = assignments;
const {
  markingId,
  isSavingProgress,
  showExercisesModal,
  selectedMatriculaItem,
  observationsMap,
  getTracker,
  markDone,
  openExercisesModal,
  submitSaveProgress,
} = useRoutineProgress({
  routines,
  saveProgress: (...args) => gymStore.markTrainerRoutineProgress(...args),
  reloadClient,
  notify,
});
onMounted(() => {
  gymStore.fetchTrainerOverview().catch(() => {});
});
</script>
<style scoped src="../styles/trainer-monitor.css"></style>
