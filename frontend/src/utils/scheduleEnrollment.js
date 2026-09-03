export const SERVICE_ORDER = ['fitness', 'musculacion', 'cardio', 'baile'];
export const DAY_ORDER = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];

export const normalizeScheduleDay = (value) =>
  String(value || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

export const normalizeScheduleTime = (value) => String(value || '00:00').slice(0, 5);

export const serviceLabel = (service) =>
  ({
    fitness: 'Fitness',
    musculacion: 'Musculacion',
    cardio: 'Cardio',
    baile: 'Baile',
  })[String(service || '').trim().toLowerCase()] || service || 'Servicio';

export const dayLabel = (day) =>
  ({
    lunes: 'Lunes',
    martes: 'Martes',
    miercoles: 'Miercoles',
    jueves: 'Jueves',
    viernes: 'Viernes',
    sabado: 'Sabado',
    domingo: 'Domingo',
  })[normalizeScheduleDay(day)] || day || 'Dia por definir';

export const availableSlots = (schedule = {}) =>
  Math.max(0, Number(schedule.cupos || 0) - Number(schedule.cupos_usados || 0));

export const isScheduleFull = (schedule = {}) => {
  const capacity = Number(schedule.cupos || 0);
  return capacity <= 0 || availableSlots(schedule) === 0;
};

export const sortServiceSchedules = (schedules = []) =>
  schedules.slice().sort((left, right) => {
    const leftService = SERVICE_ORDER.indexOf(String(left.servicio || '').toLowerCase());
    const rightService = SERVICE_ORDER.indexOf(String(right.servicio || '').toLowerCase());
    const serviceDiff = (leftService < 0 ? SERVICE_ORDER.length : leftService) - (rightService < 0 ? SERVICE_ORDER.length : rightService);
    if (serviceDiff) return serviceDiff;

    const leftDay = DAY_ORDER.indexOf(normalizeScheduleDay(left.dia));
    const rightDay = DAY_ORDER.indexOf(normalizeScheduleDay(right.dia));
    const dayDiff = (leftDay < 0 ? DAY_ORDER.length : leftDay) - (rightDay < 0 ? DAY_ORDER.length : rightDay);
    if (dayDiff) return dayDiff;

    return normalizeScheduleTime(left.hora_inicio).localeCompare(normalizeScheduleTime(right.hora_inicio));
  });

export const activeServiceSchedules = (schedules = []) =>
  sortServiceSchedules(schedules.filter((schedule) => schedule.activo !== false));

export const exerciseName = (schedule = {}) =>
  schedule.rutina_nombre ||
  schedule.nombre_ejercicio ||
  schedule.nombre_rutina ||
  (schedule.servicio ? `Clase de ${serviceLabel(schedule.servicio)}` : 'Clase de Gimnasio');

export const formatScheduleHours = (schedule = {}) =>
  `${String(schedule.hora_inicio || '--:--').slice(0, 5)} – ${String(schedule.hora_fin || '--:--').slice(0, 5)}`;

export const slotsBadgeInfo = (schedule = {}) => {
  const total = Number(schedule.cupos || 0);
  const used = Number(schedule.cupos_usados || 0);
  const free = Math.max(0, total - used);

  if (total <= 0 || free === 0) {
    return {
      available: 0,
      total,
      percent: 100,
      tone: 'danger',
      label: 'Sin cupos disponibles',
      shortLabel: 'Agotado',
    };
  }

  const percent = Math.min(100, Math.round((used / total) * 100));

  if (free <= 2) {
    return {
      available: free,
      total,
      percent,
      tone: 'warning',
      label: `¡Últimos ${free} cupos! (${free}/${total})`,
      shortLabel: `${free} libres`,
    };
  }

  return {
    available: free,
    total,
    percent,
    tone: 'success',
    label: `${free} cupos disponibles de ${total}`,
    shortLabel: `${free} libres`,
  };
};

export const enrollmentsForClient = (enrollments = [], schedules = [], clientId = 0) => {
  const numericClientId = Number(clientId || 0);
  if (!numericClientId) return [];

  const schedulesById = new Map(
    schedules.map((schedule) => [Number(schedule.id_horario_servicio || 0), schedule]),
  );

  return enrollments
    .filter(
      (enrollment) =>
        Number(enrollment.id_cliente || 0) === numericClientId &&
        String(enrollment.estado || 'ACTIVA').toUpperCase() !== 'CANCELADA',
    )
    .map((enrollment) => {
      const schedule = schedulesById.get(Number(enrollment.id_horario_servicio || 0)) || {};
      const routine = enrollment.rutina_nombre || schedule.rutina_nombre || enrollment.nombre_ejercicio || schedule.nombre_ejercicio || '';
      return {
        ...schedule,
        ...enrollment,
        rutina_nombre: routine,
        nombre_ejercicio: routine,
        dia: enrollment.dia || schedule.dia || '',
        hora_inicio: enrollment.hora_inicio || schedule.hora_inicio || '',
        hora_fin: enrollment.hora_fin || schedule.hora_fin || '',
        servicio: enrollment.servicio || schedule.servicio || '',
      };
    });
};
