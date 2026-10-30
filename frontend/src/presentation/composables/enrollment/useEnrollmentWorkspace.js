import { feedbackClass as noticeClassFor } from '../../utils/feedback.js';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { limaDate } from '../../utils/attendance.js';
import { calendarDate, scheduleOccurrences } from '../../../domain/utils/scheduleCalendar.js';
import { useAuth } from '../../../application/composables/useAuth';
import { useGymStore } from '../../../application/stores/gymStore';
import { useVisibleRefresh } from '../useVisibleRefresh.js';
import { buildClientIdentityFromUser, findClientForUser, normalizeDni, resolveClientIdForUser } from '../../../domain/utils/clientIdentity';
import { activeServiceSchedules, dayLabel, enrollmentsForClient, exerciseName, isScheduleFull, serviceLabel, sortServiceSchedules } from '../../../domain/utils/scheduleEnrollment';

/** Gestiona el cliente, la semana y las reservas de sesiones seleccionadas. */
export const useEnrollmentWorkspace = () => {
  const { user, isAdmin } = useAuth();
  const gymStore = useGymStore();
  const route = useRoute();
  const selectedDate = ref(calendarDate(route.query.fecha));
  const selectedOccurrenceDate = ref('');
  watch(() => route.query.fecha, (value) => { selectedDate.value = calendarDate(value); });
  const changeWeek = (range) => {
    selectedDate.value = range.from;
    selectedScheduleId.value = '';
    selectedOccurrenceDate.value = '';
  };

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
  const clientEnrollments = computed(() =>
    enrollmentsForClient(
      gymStore.enrollments || [],
      gymStore.serviceSchedules || [],
      currentClientId.value,
    ),
  );
  const visibleEnrollments = computed(() => scheduleOccurrences(clientEnrollments.value, selectedDate.value, selectedDate.value.slice(0, 7)));
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

  const enrolledIds = computed(() => new Set(visibleEnrollments.value.map((item) => Number(item.id_horario_servicio))));
  const isEnrolledIn = (scheduleId) => enrolledIds.value.has(Number(scheduleId));

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
      fechas_matriculadas: clientEnrollments.value.filter((item) => Number(item.id_horario_servicio) === Number(schedule.id_horario_servicio)).map((item) => item.fecha_clase),
    })),
  );

  const selectedSchedule = computed(() => {
    const schedule = manageableSchedules.value.find(
      (schedule) => Number(schedule.id_horario_servicio) === Number(selectedScheduleId.value),
    );
    return schedule ? { ...schedule, cupos_usados: schedule.ocupacion_por_fecha
      ? Number(schedule.ocupacion_por_fecha[selectedOccurrenceDate.value] || 0) : schedule.cupos_usados } : null;
  });
  const selectedIsEnrolled = computed(() =>
    Boolean(selectedSchedule.value && clientEnrollments.value.some((item) =>
      Number(item.id_horario_servicio) === Number(selectedSchedule.value.id_horario_servicio) && item.fecha_clase === selectedOccurrenceDate.value)),
  );
  const canEnrollSelected = computed(() =>
    Boolean(
      selectedSchedule.value &&
      currentClientId.value &&
      selectedOccurrenceDate.value && selectedOccurrenceDate.value >= limaDate() &&
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
    if (selectedOccurrenceDate.value && selectedOccurrenceDate.value < limaDate()) return 'La fecha de esta clase ya pasó';
    if (selectedSchedule.value && isScheduleFull(selectedSchedule.value)) return 'Sin cupos disponibles';
    return 'Agregar a mi horario';
  });
  const ownCalendarTitle = computed(() => {
    if (isAdminUser.value && !selectedClient.value) return 'Horario del cliente';
    return currentClient.value?.name ? `Horario de ${currentClient.value.name}` : 'Mi horario';
  });
  const feedbackClass = computed(() => noticeClassFor(feedbackTone.value));

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
    selectedOccurrenceDate.value = schedule?.fecha || '';
    feedback.value = '';
  };

  const refreshAll = async ({ announce = false } = {}) => {
    if (isRefreshing.value) return;
    isRefreshing.value = true;

    try {
      const tasks = [gymStore.refreshServiceSchedulesFromBackend(), gymStore.refreshScheduleClientsFromBackend()];
      if (!isAdminUser.value || currentClientId.value) {
        tasks.push(gymStore.refreshEnrollmentsFromBackend(currentClientId.value ? { id_cliente: currentClientId.value } : {}));
      }
      const results = await Promise.allSettled(tasks);
      const failure = results.find((result) => result.status === 'rejected');
      if (failure) throw failure.reason;
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
      await gymStore.refreshScheduleClientsFromBackend();
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
      const saved = await gymStore.enrollSchedule({
        id_cliente: currentClientId.value,
        id_horario_servicio: schedule.id_horario_servicio,
        fecha_clase: selectedOccurrenceDate.value,
      });
      const notification = saved?.email_notification?.message;
      setFeedback(`“${exerciseName(schedule)}” se agregó al horario.${notification ? ` ${notification}` : ''}`);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No se pudo agregar la clase.', 'error');
    } finally {
      actionBusy.value = '';
    }
  };

  const cancelSelected = async () => {
    const schedule = selectedSchedule.value;
    const enrollment = visibleEnrollments.value.find(
      (item) => Number(item.id_horario_servicio) === Number(schedule?.id_horario_servicio)
        && item.fecha_clase === selectedOccurrenceDate.value,
    );
    if (!enrollment?.id_matricula) {
      setFeedback('No se encontró la matrícula activa de esta clase.', 'error');
      return;
    }

    actionBusy.value = `cancel-${enrollment.id_matricula}`;
    try {
      await gymStore.deleteEnrollment(enrollment.id_matricula);
      setFeedback(`“${exerciseName(enrollment)}” se quitó del horario.`);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No se pudo quitar la clase.', 'error');
    } finally {
      actionBusy.value = '';
    }
  };

  const manageSelectedSchedule = async () => {
    if (actionBusy.value) return;
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
    if (isAdminUser.value) refreshAll();
  });

  useVisibleRefresh(refreshAll, {
    canRefresh: () => !isAdminUser.value && !actionBusy.value && !isSearchingClient.value && !isPickerOpen.value,
  });

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleEscape);
    if (typeof document !== 'undefined') document.body.style.overflow = previousBodyOverflow;
  });

  return {
    user, isAdmin, gymStore, route, selectedDate,
    selectedOccurrenceDate, changeWeek, dniSearch, selectedClient, selectedScheduleId,
    selectedDayFilter, selectedServiceFilter, searchQuery, feedback, feedbackTone,
    actionBusy, isRefreshing, isSearchingClient, isPickerOpen, previousBodyOverflow,
    dayFilterOptions, serviceFilterOptions, isAdminUser, authUser, authClient,
    authClientId, currentClient, currentClientId, schedules, clientEnrollments,
    visibleEnrollments, enrichedEnrollments, manageableSchedules, normalizeText, enrolledIds,
    isEnrolledIn, filteredSchedules, enrichedFilteredSchedules, selectedSchedule, selectedIsEnrolled,
    canEnrollSelected, selectedActionDisabled, selectedActionLabel, ownCalendarTitle, feedbackClass,
    setFeedback, resetFilters, openSchedulePicker, closeSchedulePicker, selectAvailableSchedule,
    refreshAll, loadAdminClient, enrollSelected, cancelSelected, manageSelectedSchedule,
    handleEscape,
  };
};
