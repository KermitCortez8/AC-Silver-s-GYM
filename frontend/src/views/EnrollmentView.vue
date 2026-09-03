<template>
  <div class="space-y-5 pb-10">
    <header class="rounded-3xl border border-white/10 bg-slate-950/55 p-5 shadow-xl backdrop-blur-xl sm:p-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div class="min-w-0">
          <p class="text-xs font-black uppercase tracking-[0.28em] text-cyan-300">
            {{ isAdminUser ? 'Matrícula de cliente' : 'Mi horario' }}
          </p>
          <h1 class="mt-2 truncate text-2xl font-black text-white sm:text-3xl">{{ ownCalendarTitle }}</h1>
          <p class="mt-1 text-sm text-slate-400">
            {{ visibleEnrollments.length
              ? `${visibleEnrollments.length} clase${visibleEnrollments.length === 1 ? '' : 's'} en el horario actual.`
              : isAdminUser && !selectedClient
                ? 'Busca un cliente para consultar y gestionar su horario.'
                : 'Aún no hay clases agregadas a este horario.' }}
          </p>
        </div>

        <div class="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-bold text-slate-200 transition hover:bg-white/10 disabled:cursor-wait disabled:opacity-60"
            :disabled="isRefreshing"
            @click="refreshAll({ announce: true })"
          >
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': isRefreshing }" />
            {{ isRefreshing ? 'Actualizando…' : 'Actualizar' }}
          </button>
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-2.5 text-sm font-black text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!currentClientId"
            @click="openSchedulePicker"
          >
            <Calendar class="h-4 w-4" />
            {{ visibleEnrollments.length ? 'Cambiar horario' : 'Elegir horario' }}
          </button>
        </div>
      </div>
    </header>

    <section v-if="isAdminUser" class="rounded-2xl border border-amber-400/20 bg-amber-400/5 p-4">
      <form class="flex flex-col gap-3 sm:flex-row sm:items-end" @submit.prevent="loadAdminClient">
        <label class="flex-1 space-y-1.5">
          <span class="text-xs font-bold uppercase tracking-wider text-amber-200">Cliente por DNI</span>
          <input
            v-model="dniSearch"
            inputmode="numeric"
            autocomplete="off"
            class="field-input"
            placeholder="Ingresa el DNI del cliente"
          />
        </label>
        <button
          type="submit"
          class="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-amber-300 disabled:cursor-wait disabled:opacity-60"
          :disabled="isSearchingClient"
        >
          <Search class="h-4 w-4" />
          {{ isSearchingClient ? 'Buscando…' : 'Buscar' }}
        </button>
        <div v-if="selectedClient" class="rounded-xl border border-emerald-400/25 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
          <strong>{{ selectedClient.name }}</strong>
          <span class="ml-1 text-emerald-200/70">DNI {{ selectedClient.dni }}</span>
        </div>
      </form>
    </section>

    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="-translate-y-2 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="feedback && !isPickerOpen"
        class="flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm"
        :class="feedbackClass"
        role="status"
        aria-live="polite"
      >
        <div class="flex items-center gap-2">
          <CheckCircle2 v-if="feedbackTone === 'success'" class="h-4 w-4 shrink-0" />
          <AlertCircle v-else class="h-4 w-4 shrink-0" />
          <p>{{ feedback }}</p>
        </div>
        <button type="button" aria-label="Cerrar mensaje" @click="feedback = ''">
          <X class="h-4 w-4" />
        </button>
      </div>
    </Transition>

    <main aria-label="Horario actual">
      <ExcelScheduleGrid
        :title="ownCalendarTitle"
        subtitle="Este es el horario vigente. Usa “Cambiar horario” para agregar o quitar una clase."
        :items="enrichedEnrollments"
        file-name="mi-horario-personal.xlsx"
        :empty-message="currentClientId
          ? 'Este horario está vacío. Pulsa “Elegir horario” para agregar la primera clase.'
          : 'Selecciona un cliente para mostrar su horario.'"
      />
    </main>

    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isPickerOpen"
          class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/85 p-2 backdrop-blur-sm sm:p-4"
          @click.self="closeSchedulePicker"
        >
          <section
            class="flex max-h-[96vh] w-full max-w-[1500px] flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-950 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="schedule-picker-title"
          >
            <header class="flex shrink-0 items-start justify-between gap-4 border-b border-white/10 px-4 py-4 sm:px-6">
              <div>
                <p class="text-xs font-black uppercase tracking-[0.24em] text-cyan-300">Gestionar horario</p>
                <h2 id="schedule-picker-title" class="mt-1 text-xl font-black text-white sm:text-2xl">
                  Elige una clase
                </h2>
                <p class="mt-1 text-xs text-slate-400">
                  Selecciona un bloque del calendario para agregarlo o quitarlo.
                </p>
              </div>
              <button
                type="button"
                class="rounded-xl border border-white/10 bg-white/5 p-2.5 text-slate-300 transition hover:bg-white/10 hover:text-white"
                aria-label="Cerrar selector de horario"
                @click="closeSchedulePicker"
              >
                <X class="h-5 w-5" />
              </button>
            </header>

            <div class="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
              <div
                v-if="feedback"
                class="mb-4 flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm"
                :class="feedbackClass"
                role="status"
                aria-live="polite"
              >
                <div class="flex items-center gap-2">
                  <CheckCircle2 v-if="feedbackTone === 'success'" class="h-4 w-4 shrink-0" />
                  <AlertCircle v-else class="h-4 w-4 shrink-0" />
                  <p>{{ feedback }}</p>
                </div>
                <button type="button" aria-label="Cerrar mensaje" @click="feedback = ''">
                  <X class="h-4 w-4" />
                </button>
              </div>

              <div class="mb-4 grid gap-3 md:grid-cols-[minmax(220px,1fr)_180px_200px_auto]">
                <label class="space-y-1.5">
                  <span class="text-xs font-bold text-slate-400">Buscar</span>
                  <div class="relative">
                    <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                    <input v-model="searchQuery" class="field-input pl-9" placeholder="Ejercicio, servicio u hora" />
                  </div>
                </label>
                <label class="space-y-1.5">
                  <span class="text-xs font-bold text-slate-400">Día</span>
                  <select v-model="selectedDayFilter" class="field-input">
                    <option v-for="day in dayFilterOptions" :key="day.value" :value="day.value">{{ day.label }}</option>
                  </select>
                </label>
                <label class="space-y-1.5">
                  <span class="text-xs font-bold text-slate-400">Servicio</span>
                  <select v-model="selectedServiceFilter" class="field-input">
                    <option v-for="service in serviceFilterOptions" :key="service.value" :value="service.value">{{ service.label }}</option>
                  </select>
                </label>
                <button
                  type="button"
                  class="self-end rounded-xl border border-white/10 px-4 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                  @click="resetFilters"
                >
                  Limpiar
                </button>
              </div>

              <div class="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
                <ExcelScheduleGrid
                  title="Horarios disponibles"
                  :subtitle="`${filteredSchedules.length} clases visibles. Las que ya pertenecen al horario están marcadas.`"
                  :items="enrichedFilteredSchedules"
                  file-name="horarios-disponibles.xlsx"
                  empty-message="No hay clases que coincidan con los filtros."
                  interactive
                  :selected-item-id="selectedScheduleId"
                  @select="selectAvailableSchedule"
                />

                <aside class="rounded-2xl border border-white/10 bg-white/[0.04] p-4 xl:sticky xl:top-0">
                  <template v-if="selectedSchedule">
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0">
                        <p class="text-xs font-black uppercase tracking-wider text-cyan-300">Clase seleccionada</p>
                        <h3 class="mt-2 text-xl font-black text-white">{{ exerciseName(selectedSchedule) }}</h3>
                      </div>
                      <span
                        class="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-black"
                        :class="selectedIsEnrolled ? 'bg-emerald-400/15 text-emerald-200' : 'bg-white/10 text-slate-300'"
                      >
                        {{ selectedIsEnrolled ? 'En tu horario' : serviceLabel(selectedSchedule.servicio) }}
                      </span>
                    </div>

                    <dl class="mt-5 divide-y divide-white/10 rounded-xl border border-white/10 bg-slate-900/60 px-3">
                      <div class="flex items-center justify-between gap-3 py-3">
                        <dt class="text-xs text-slate-400">Día</dt>
                        <dd class="text-sm font-bold text-white">{{ dayLabel(selectedSchedule.dia) }}</dd>
                      </div>
                      <div class="flex items-center justify-between gap-3 py-3">
                        <dt class="text-xs text-slate-400">Hora</dt>
                        <dd class="text-sm font-bold text-white">{{ formatScheduleHours(selectedSchedule) }}</dd>
                      </div>
                      <div class="flex items-center justify-between gap-3 py-3">
                        <dt class="text-xs text-slate-400">Cupos libres</dt>
                        <dd class="text-sm font-bold" :class="isScheduleFull(selectedSchedule) ? 'text-rose-300' : 'text-emerald-300'">
                          {{ availableSlots(selectedSchedule) }} de {{ selectedSchedule.cupos || 0 }}
                        </dd>
                      </div>
                    </dl>

                    <button
                      type="button"
                      class="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-black transition disabled:cursor-not-allowed disabled:opacity-50"
                      :class="selectedIsEnrolled
                        ? 'border border-rose-400/30 bg-rose-400/10 text-rose-100 hover:bg-rose-400/20'
                        : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300'"
                      :disabled="selectedActionDisabled"
                      @click="manageSelectedSchedule"
                    >
                      <Trash2 v-if="selectedIsEnrolled" class="h-4 w-4" />
                      <CheckCircle2 v-else class="h-4 w-4" />
                      {{ selectedActionLabel }}
                    </button>
                  </template>

                  <div v-else class="flex min-h-56 flex-col items-center justify-center px-3 text-center">
                    <Clock class="h-8 w-8 text-slate-600" />
                    <h3 class="mt-3 font-black text-white">Selecciona una clase</h3>
                    <p class="mt-1 text-sm leading-6 text-slate-400">
                      Pulsa un bloque del calendario para ver su horario y disponibilidad.
                    </p>
                  </div>

                  <p class="mt-4 border-t border-white/10 pt-4 text-xs leading-5 text-slate-500">
                    El horario actual tiene {{ visibleEnrollments.length }} clase{{ visibleEnrollments.length === 1 ? '' : 's' }}.
                  </p>
                </aside>
              </div>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-vue-next';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import {
  buildClientIdentityFromUser,
  findClientForUser,
  normalizeDni,
  resolveClientIdForUser,
} from '../utils/clientIdentity';
import {
  activeServiceSchedules,
  availableSlots,
  dayLabel,
  enrollmentsForClient,
  exerciseName,
  formatScheduleHours,
  isScheduleFull,
  serviceLabel,
  sortServiceSchedules,
} from '../utils/scheduleEnrollment';

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();

const dniSearch = ref('');
const selectedClient = ref(null);
const selectedScheduleId = ref('');
const selectedDayFilter = ref('todos');
const selectedServiceFilter = ref('todos');
const searchQuery = ref('');
const feedback = ref('');
const feedbackTone = ref('success');
const actionBusy = ref('');
const isRefreshing = ref(false);
const isSearchingClient = ref(false);
const isPickerOpen = ref(false);
let previousBodyOverflow = '';

const dayFilterOptions = [
  { label: 'Todos los días', value: 'todos' },
  { label: 'Lunes', value: 'lunes' },
  { label: 'Martes', value: 'martes' },
  { label: 'Miércoles', value: 'miercoles' },
  { label: 'Jueves', value: 'jueves' },
  { label: 'Viernes', value: 'viernes' },
  { label: 'Sábado', value: 'sabado' },
  { label: 'Domingo', value: 'domingo' },
];

const serviceFilterOptions = [
  { label: 'Todos los servicios', value: 'todos' },
  { label: 'Musculación', value: 'musculacion' },
  { label: 'Cardio', value: 'cardio' },
  { label: 'Fitness', value: 'fitness' },
  { label: 'Baile', value: 'baile' },
];

const isAdminUser = computed(() => Boolean(isAdmin.value));
const authUser = computed(() => user.value || {});
const authClient = computed(() => findClientForUser(authUser.value, gymStore.members));
const authClientId = computed(() =>
  Number(authClient.value?.id_cliente || resolveClientIdForUser(authUser.value, gymStore.members) || 0),
);
const currentClient = computed(() =>
  isAdminUser.value
    ? selectedClient.value
    : authClient.value || buildClientIdentityFromUser(authUser.value, gymStore.members),
);
const currentClientId = computed(() =>
  Number(currentClient.value?.id_cliente || (isAdminUser.value ? 0 : authClientId.value) || 0),
);

const schedules = computed(() => activeServiceSchedules(gymStore.serviceSchedules || []));
const visibleEnrollments = computed(() =>
  enrollmentsForClient(
    gymStore.enrollments || [],
    gymStore.serviceSchedules || [],
    currentClientId.value,
  ),
);
const enrichedEnrollments = computed(() =>
  visibleEnrollments.value.map((item) => ({ ...item, is_enrolled: true })),
);
const manageableSchedules = computed(() => {
  const schedulesById = new Map(
    schedules.value.map((schedule) => [Number(schedule.id_horario_servicio), schedule]),
  );
  visibleEnrollments.value.forEach((enrollment) => {
    const scheduleId = Number(enrollment.id_horario_servicio || 0);
    if (scheduleId && !schedulesById.has(scheduleId)) schedulesById.set(scheduleId, enrollment);
  });
  return sortServiceSchedules([...schedulesById.values()]);
});

const normalizeText = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();

const isEnrolledIn = (scheduleId) =>
  visibleEnrollments.value.some(
    (item) => Number(item.id_horario_servicio) === Number(scheduleId),
  );

const filteredSchedules = computed(() => {
  const query = normalizeText(searchQuery.value);
  return manageableSchedules.value.filter((schedule) => {
    const matchesDay = selectedDayFilter.value === 'todos' || normalizeText(schedule.dia) === selectedDayFilter.value;
    const matchesService = selectedServiceFilter.value === 'todos' || normalizeText(schedule.servicio) === selectedServiceFilter.value;
    const searchableText = normalizeText([
      exerciseName(schedule),
      serviceLabel(schedule.servicio),
      dayLabel(schedule.dia),
      schedule.hora_inicio,
      schedule.hora_fin,
    ].join(' '));
    return matchesDay && matchesService && (!query || searchableText.includes(query));
  });
});

const enrichedFilteredSchedules = computed(() =>
  filteredSchedules.value.map((schedule) => ({
    ...schedule,
    is_enrolled: isEnrolledIn(schedule.id_horario_servicio),
  })),
);

const selectedSchedule = computed(() =>
  manageableSchedules.value.find(
    (schedule) => Number(schedule.id_horario_servicio) === Number(selectedScheduleId.value),
  ) || null,
);
const selectedIsEnrolled = computed(() =>
  Boolean(selectedSchedule.value && isEnrolledIn(selectedSchedule.value.id_horario_servicio)),
);
const canEnrollSelected = computed(() =>
  Boolean(
    selectedSchedule.value &&
    currentClientId.value &&
    !selectedIsEnrolled.value &&
    !isScheduleFull(selectedSchedule.value),
  ),
);
const selectedActionDisabled = computed(() =>
  Boolean(actionBusy.value) || (!selectedIsEnrolled.value && !canEnrollSelected.value),
);
const selectedActionLabel = computed(() => {
  if (selectedIsEnrolled.value) {
    return actionBusy.value ? 'Quitando…' : 'Quitar de mi horario';
  }
  if (actionBusy.value) return 'Agregando…';
  if (selectedSchedule.value && isScheduleFull(selectedSchedule.value)) return 'Sin cupos disponibles';
  return 'Agregar a mi horario';
});
const ownCalendarTitle = computed(() => {
  if (isAdminUser.value && !selectedClient.value) return 'Horario del cliente';
  return currentClient.value?.name ? `Horario de ${currentClient.value.name}` : 'Mi horario';
});
const feedbackClass = computed(() =>
  feedbackTone.value === 'error'
    ? 'border-rose-400/25 bg-rose-400/10 text-rose-100'
    : 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100',
);

const setFeedback = (message, tone = 'success') => {
  feedback.value = message;
  feedbackTone.value = tone;
};

const resetFilters = () => {
  selectedDayFilter.value = 'todos';
  selectedServiceFilter.value = 'todos';
  searchQuery.value = '';
};

const openSchedulePicker = () => {
  if (!currentClientId.value) {
    setFeedback('Busca primero un cliente por DNI.', 'error');
    return;
  }
  feedback.value = '';
  selectedScheduleId.value = '';
  isPickerOpen.value = true;
};

const closeSchedulePicker = () => {
  if (actionBusy.value) return;
  isPickerOpen.value = false;
  selectedScheduleId.value = '';
};

const selectAvailableSchedule = (schedule) => {
  selectedScheduleId.value = schedule?.id_horario_servicio || '';
  feedback.value = '';
};

const refreshAll = async ({ announce = false } = {}) => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;

  try {
    try {
      await gymStore.fetchFromBackend?.();
    } catch (primaryError) {
      const fallback = await Promise.allSettled([
        gymStore.refreshServiceSchedulesFromBackend?.(),
        gymStore.refreshEnrollmentsFromBackend?.(),
      ]);
      if (fallback.every((result) => result.status === 'rejected')) throw primaryError;
    }

    if (currentClientId.value) {
      await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value });
    }
    if (announce) setFeedback('Horario actualizado.');
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : 'No se pudo cargar el horario.', 'error');
  } finally {
    isRefreshing.value = false;
  }
};

const loadAdminClient = async () => {
  const dni = normalizeDni(dniSearch.value);
  if (!dni) {
    selectedClient.value = null;
    setFeedback('Ingresa el DNI del cliente.', 'error');
    return;
  }

  isSearchingClient.value = true;
  try {
    await gymStore.fetchFromBackend?.().catch(() => {});
    const client = gymStore.members.find((member) => normalizeDni(member.dni) === dni) || null;
    if (!client) {
      selectedClient.value = null;
      setFeedback('Cliente no encontrado por DNI.', 'error');
      return;
    }

    selectedClient.value = client;
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: client.id_cliente });
    setFeedback(`Horario de ${client.name} cargado.`);
  } catch (error) {
    selectedClient.value = null;
    setFeedback(error instanceof Error ? error.message : 'No se pudo buscar al cliente.', 'error');
  } finally {
    isSearchingClient.value = false;
  }
};

const enrollSelected = async () => {
  const schedule = selectedSchedule.value;
  if (!schedule || !canEnrollSelected.value) return;

  actionBusy.value = `enroll-${schedule.id_horario_servicio}`;
  try {
    await gymStore.enrollSchedule({
      id_cliente: currentClientId.value,
      id_horario_servicio: schedule.id_horario_servicio,
    });
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value });
    setFeedback(`“${exerciseName(schedule)}” se agregó al horario.`);
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : 'No se pudo agregar la clase.', 'error');
  } finally {
    actionBusy.value = '';
  }
};

const cancelSelected = async () => {
  const schedule = selectedSchedule.value;
  const enrollment = visibleEnrollments.value.find(
    (item) => Number(item.id_horario_servicio) === Number(schedule?.id_horario_servicio),
  );
  if (!enrollment?.id_matricula) {
    setFeedback('No se encontró la matrícula activa de esta clase.', 'error');
    return;
  }

  actionBusy.value = `cancel-${enrollment.id_matricula}`;
  try {
    await gymStore.deleteEnrollment(enrollment.id_matricula);
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: currentClientId.value });
    setFeedback(`“${exerciseName(enrollment)}” se quitó del horario.`);
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : 'No se pudo quitar la clase.', 'error');
  } finally {
    actionBusy.value = '';
  }
};

const manageSelectedSchedule = async () => {
  if (selectedIsEnrolled.value) {
    await cancelSelected();
    return;
  }
  await enrollSelected();
};

const handleEscape = (event) => {
  if (event.key === 'Escape' && isPickerOpen.value) closeSchedulePicker();
};

watch(currentClientId, () => {
  selectedScheduleId.value = '';
  if (isPickerOpen.value) closeSchedulePicker();
});

watch(filteredSchedules, (items) => {
  if (selectedScheduleId.value && !items.some(
    (schedule) => Number(schedule.id_horario_servicio) === Number(selectedScheduleId.value),
  )) {
    selectedScheduleId.value = '';
  }
});

watch(isPickerOpen, (isOpen) => {
  if (typeof document === 'undefined') return;
  if (isOpen) {
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = previousBodyOverflow;
  }
});

onMounted(() => {
  window.addEventListener('keydown', handleEscape);
  refreshAll();
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape);
  if (typeof document !== 'undefined') document.body.style.overflow = previousBodyOverflow;
});
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  background: rgba(2, 6, 23, 0.78);
  padding: 0.75rem 0.9rem;
  color: white;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.field-input:focus {
  border-color: rgb(34 211 238 / 0.75);
  box-shadow: 0 0 0 3px rgb(34 211 238 / 0.1);
}

.field-input::placeholder {
  color: #64748b;
}
</style>
