import { computed, onMounted, reactive, ref, watch } from 'vue';
import { limaDate } from '../../utils/attendance.js';
import { monthWeeks, scheduleOccurrences, weekStart } from '../../../domain/utils/scheduleCalendar.js';
import { useGymStore } from '../../../application/stores/gymStore';

/** Gestiona filtros, disponibilidad y edición de la programación semanal. */
export const useServiceSchedules = () => {
  const gymStore = useGymStore();
  const schedules = computed(() => gymStore.serviceSchedules);
  const routines = computed(() => gymStore.routines || []);
  const showFilters = ref(false);
  const showList = ref(false);
  const extraFilterCount = computed(() => Number(filters.dia !== 'todos') + Number(filters.estado !== 'todos') + Number(filters.sortBy !== 'servicio-dia-hora'));
  const isSaving = ref(false);
  const isRefreshing = ref(false);
  const today = limaDate();
  const visibleRange = ref({ ...monthWeeks(today.slice(0, 7)).find((week) => week.start === weekStart(today)), month: today.slice(0, 7) });
  const weeklySchedules = computed(() => {
    const occurrences = new Map(scheduleOccurrences(filteredSchedules.value, visibleRange.value.start, visibleRange.value.month).map((item) => [item.id_horario_servicio, item]));
    return filteredSchedules.value.flatMap((item) => occurrences.has(item.id_horario_servicio) ? [occurrences.get(item.id_horario_servicio)] : []);
  });
  const isEditorOpen = ref(false);
  const feedback = ref('');
  const pendingDelete = ref(null);
  const isDeleting = ref(false);
  const feedbackTone = ref('success');
  const showNotification = ({ tone, message }) => {
    feedbackTone.value = tone;
    feedback.value = message;
  };

  const filters = reactive({
    search: '',
    servicio: 'todos',
    dia: 'todos',
    estado: 'todos',
    sortBy: 'servicio-dia-hora',
  });

  const days = [
    { value: 'lunes', code: 'LUN', label: 'Lunes' },
    { value: 'martes', code: 'MAR', label: 'Martes' },
    { value: 'miercoles', code: 'MIE', label: 'Miércoles' },
    { value: 'jueves', code: 'JUE', label: 'Jueves' },
    { value: 'viernes', code: 'VIE', label: 'Viernes' },
    { value: 'sabado', code: 'SAB', label: 'Sábado' },
    { value: 'domingo', code: 'DOM', label: 'Domingo' },
  ];

  const serviceFilters = [
    { value: 'todos', label: 'Todos los servicios' },
    { value: 'fitness', label: 'Fitness' },
    { value: 'musculacion', label: 'Musculación' },
    { value: 'cardio', label: 'Cardio' },
    { value: 'baile', label: 'Baile' },
  ];

  const statusFilters = [
    { value: 'todos', label: 'Todos' },
    { value: 'activos', label: 'Activos' },
    { value: 'pausados', label: 'Pausados' },
    { value: 'con-cupos', label: 'Con cupos' },
    { value: 'llenos', label: 'Llenos' },
  ];

  const sortOptions = [
    { value: 'servicio-dia-hora', label: 'Servicio, día y hora' },
    { value: 'dia-hora', label: 'Día y hora' },
    { value: 'cupos-disponibles', label: 'Cupos disponibles' },
    { value: 'estado', label: 'Estado' },
  ];

  /**
   * Gestiona esta acción de la vista.
   */
  const defaultForm = () => ({
    id_horario_servicio: null,
    servicio: 'fitness',
    id_rutina: 0,
    dia: 'lunes',
    codigo_dia: 'LUN',
    hora_inicio: '06:00',
    hora_fin: '07:00',
    cupos: 10,
    activo: true,
  });

  const form = reactive(defaultForm());

  /**
   * Normaliza el valor recibido.
   */
  const normalizeService = (service) => String(service || '').trim().toLowerCase();
  /**
   * Gestiona esta acción de la vista.
   */
  const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[normalizeService(service)] || service;
  /**
   * Gestiona esta acción de la vista.
   */
  const dayLabel = (day) => days.find((entry) => entry.value === day)?.label || day;
  /**
   * Gestiona esta acción de la vista.
   */
  const dayOrder = (day) => days.findIndex((entry) => entry.value === day);
  /**
   * Gestiona esta acción de la vista.
   */
  const serviceOrder = (service) => Math.max(0, serviceFilters.findIndex((entry) => entry.value === service) - 1);
  const routineById = computed(() =>
    routines.value.reduce((result, routine) => {
      result[Number(routine.id_rutina)] = routine;
      return result;
    }, {}),
  );
  /**
   * Gestiona esta acción de la vista.
   */
  const routineName = (idRutina) => routineById.value[Number(idRutina)]?.nombre_rutina || 'Sin rutina';
  /**
   * Gestiona esta acción de la vista.
   */
  const routineZones = (idRutina) => routineById.value[Number(idRutina)]?.zonas_musculares || 'Rutina pendiente';
  const routinesForSelectedService = computed(() =>
    routines.value.filter((routine) => String(routine.servicio || '').toLowerCase() === String(form.servicio || '').toLowerCase()),
  );
  /**
   * Valida los datos recibidos.
   */
  const isScheduleActive = (schedule) => schedule.activo !== false;
  const activeSchedules = computed(() => schedules.value.filter((item) => item.activo !== false).length);
  const totalSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos || 0), 0));
  const usedSlots = computed(() => schedules.value.reduce((sum, item) => sum + Number(item.cupos_usados || 0), 0));

  /**
   * Gestiona esta acción de la vista.
   */
  const timeToMinutes = (value) => {
    const [hour = 0, minute = 0] = String(value || '').split(':').map(Number);
    return hour * 60 + minute;
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const availableSlots = (schedule) => Math.max(0, Number(schedule.cupos || 0) - Number(schedule.cupos_usados || 0));

  /**
   * Gestiona esta acción de la vista.
   */
  const durationLabel = (schedule) => {
    const duration = timeToMinutes(schedule.hora_fin) - timeToMinutes(schedule.hora_inicio);
    if (duration === 60) return 'Duración 1 hora';
    if (duration === 120) return 'Duración 2 horas';
    return `Duración ${Math.max(0, duration)} min`;
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const slotsPercent = (schedule) => {
    const total = Number(schedule.cupos || 0);
    if (!total) return 0;

    const used = Math.min(total, Math.max(0, Number(schedule.cupos_usados || 0)));
    return Math.round((used / total) * 100);
  };

  const servicePalette = {
    fitness: { background: '#d9f99d', border: '#84cc16' },
    musculacion: { background: '#bfdbfe', border: '#38bdf8' },
    cardio: { background: '#fde68a', border: '#f59e0b' },
    baile: { background: '#fecdd3', border: '#fb7185' },
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const serviceStyle = (service) => {
    const colors = servicePalette[normalizeService(service)] || { background: '#e2e8f0', border: '#94a3b8' };
    return {
      '--schedule-service-bg': colors.background,
      '--schedule-service-border': colors.border,
    };
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const statusClass = (schedule) =>
    isScheduleActive(schedule)
      ? 'schedule-status-active'
      : 'schedule-status-paused';

  /**
   * Normaliza el valor recibido.
   */
  const normalizeText = (value) =>
    String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();

  /**
   * Gestiona esta acción de la vista.
   */
  const searchableScheduleText = (schedule) =>
    normalizeText(
      [
        serviceLabel(schedule.servicio),
        routineName(schedule.id_rutina),
        routineZones(schedule.id_rutina),
        dayLabel(schedule.dia),
        schedule.codigo_dia,
        schedule.hora_inicio,
        schedule.hora_fin,
        schedule.cupos,
        isScheduleActive(schedule) ? 'activo' : 'pausado',
      ].join(' '),
    );

  /**
   * Gestiona esta acción de la vista.
   */
  const matchesStatus = (schedule) => {
    if (filters.estado === 'activos') return schedule.activo !== false;
    if (filters.estado === 'pausados') return schedule.activo === false;
    if (filters.estado === 'con-cupos') return availableSlots(schedule) > 0;
    if (filters.estado === 'llenos') return Number(schedule.cupos || 0) > 0 && availableSlots(schedule) <= 0;
    return true;
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const compareBase = (a, b) => {
    const serviceDiff = serviceOrder(a.servicio) - serviceOrder(b.servicio);
    if (serviceDiff) return serviceDiff;

    const dayDiff = dayOrder(a.dia) - dayOrder(b.dia);
    if (dayDiff) return dayDiff;

    return timeToMinutes(a.hora_inicio) - timeToMinutes(b.hora_inicio);
  };

  const filteredSchedules = computed(() => {
    const search = normalizeText(filters.search).trim();

    return [...schedules.value]
      .filter((schedule) => {
        const serviceMatch = filters.servicio === 'todos' || schedule.servicio === filters.servicio;
        const dayMatch = filters.dia === 'todos' || schedule.dia === filters.dia;
        const textMatch = !search || searchableScheduleText(schedule).includes(search);

        return serviceMatch && dayMatch && matchesStatus(schedule) && textMatch;
      })
      .sort((a, b) => {
        if (filters.sortBy === 'dia-hora') {
          const dayDiff = dayOrder(a.dia) - dayOrder(b.dia);
          if (dayDiff) return dayDiff;
          const timeDiff = timeToMinutes(a.hora_inicio) - timeToMinutes(b.hora_inicio);
          if (timeDiff) return timeDiff;
          return serviceOrder(a.servicio) - serviceOrder(b.servicio);
        }

        if (filters.sortBy === 'cupos-disponibles') {
          const slotsDiff = availableSlots(b) - availableSlots(a);
          return slotsDiff || compareBase(a, b);
        }

        if (filters.sortBy === 'estado') {
          const stateDiff = Number(b.activo !== false) - Number(a.activo !== false);
          return stateDiff || compareBase(a, b);
        }

        return compareBase(a, b);
      })
      .map((schedule) => ({
        ...schedule,
        rutina_nombre: routineName(schedule.id_rutina),
        zonas_musculares: routineZones(schedule.id_rutina),
      }));
  });

  /**
   * Valida los datos recibidos.
   */
  const hasValidShortDuration = () => {
    const duration = timeToMinutes(form.hora_fin) - timeToMinutes(form.hora_inicio);
    return duration === 60 || duration === 120;
  };

  watch(
    () => form.dia,
    (day) => {
      if (!form.id_horario_servicio) {
        form.codigo_dia = days.find((entry) => entry.value === day)?.code || form.codigo_dia;
      }
    },
  );

  watch(
    () => form.servicio,
    () => {
      if (!routinesForSelectedService.value.some((routine) => Number(routine.id_rutina) === Number(form.id_rutina))) {
        form.id_rutina = 0;
      }
    },
  );

  /**
   * Gestiona esta acción de la vista.
   */
  const resetForm = () => {
    Object.assign(form, defaultForm());
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const openNewSchedule = () => {
    resetForm();
    feedback.value = '';
    isEditorOpen.value = true;
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const closeEditor = () => {
    if (isSaving.value) return;
    isEditorOpen.value = false;
    resetForm();
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const resetFilters = () => {
    Object.assign(filters, {
      search: '',
      servicio: 'todos',
      dia: 'todos',
      estado: 'todos',
      sortBy: 'servicio-dia-hora',
    });
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const editSchedule = (schedule) => {
    Object.assign(form, {
      id_horario_servicio: schedule.id_horario_servicio,
      servicio: schedule.servicio || 'fitness',
      id_rutina: Number(schedule.id_rutina || 0),
      dia: schedule.dia || 'lunes',
      codigo_dia: schedule.codigo_dia || 'LUN',
      hora_inicio: String(schedule.hora_inicio || '06:00').slice(0, 5),
      hora_fin: String(schedule.hora_fin || '07:00').slice(0, 5),
      cupos: Number(schedule.cupos || 10),
      activo: schedule.activo !== false,
    });
    feedback.value = '';
    isEditorOpen.value = true;
  };

  /**
   * Actualiza los datos actuales.
   */
  const refreshAll = async (notify = false) => {
    if (isRefreshing.value) return;
    isRefreshing.value = true;
    try {
      await gymStore.fetchFromBackend({ section: 'schedules', force: notify });
      if (notify) showNotification({ tone: 'success', message: 'Los horarios y las rutinas están actualizados.' });
    } catch (error) {
      feedbackTone.value = 'error';
      feedback.value = error.message || 'No se pudieron cargar los horarios.';
    } finally { isRefreshing.value = false; }
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const saveSchedule = async () => {
    if (isSaving.value) return;
    isSaving.value = true;
    feedback.value = '';
    try {
      if (!form.hora_inicio || !form.hora_fin) throw new Error('Completa la hora de inicio y la hora de salida.');
      if (!hasValidShortDuration()) {
        throw new Error('El horario debe durar exactamente 1 o 2 horas.');
      }
      if (!Number(form.id_rutina || 0)) {
        throw new Error('Selecciona una rutina para este servicio.');
      }
      if (!Number.isInteger(form.cupos) || form.cupos < 1) throw new Error('Ingresa un número entero de cupos mayor que cero.');
      if (!form.codigo_dia.trim()) throw new Error('Ingresa el código del día.');
      await gymStore.upsertServiceSchedule({ ...form });
      feedbackTone.value = 'success';
      feedback.value = 'Horario guardado.';
      isEditorOpen.value = false;
      resetForm();
    } catch (error) {
      feedbackTone.value = 'error';
      feedback.value = error instanceof Error ? error.message : 'No se pudo guardar el horario.';
    } finally {
      isSaving.value = false;
    }
  };

  /**
   * Elimina el registro indicado.
   */
  const removeSchedule = (schedule) => { pendingDelete.value = schedule; };
  const confirmRemoveSchedule = async () => {
    if (isDeleting.value || !pendingDelete.value) return;
    const schedule = pendingDelete.value;
    isDeleting.value = true;
    try {
      await gymStore.deleteServiceSchedule(schedule.id_horario_servicio);
      feedbackTone.value = 'success';
      feedback.value = 'Horario eliminado.';
    } catch (error) {
      feedbackTone.value = 'error';
      feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar el horario.';
    } finally {
      isDeleting.value = false;
      pendingDelete.value = null;
    }
  };

  onMounted(() => refreshAll());

  return {
    gymStore, schedules, routines, showFilters, showList,
    extraFilterCount, isSaving, isRefreshing, today, visibleRange,
    weeklySchedules, isEditorOpen, feedback, pendingDelete, isDeleting,
    feedbackTone, showNotification, filters, days, serviceFilters,
    statusFilters, sortOptions, defaultForm, form, normalizeService,
    serviceLabel, dayLabel, dayOrder, serviceOrder, routineById,
    routineName, routineZones, routinesForSelectedService, isScheduleActive, activeSchedules,
    totalSlots, usedSlots, timeToMinutes, availableSlots, durationLabel,
    slotsPercent, servicePalette, serviceStyle, statusClass, normalizeText,
    searchableScheduleText, matchesStatus, compareBase, filteredSchedules, hasValidShortDuration,
    resetForm, openNewSchedule, closeEditor, resetFilters, editSchedule,
    refreshAll, saveSchedule, removeSchedule, confirmRemoveSchedule,
  };
};
