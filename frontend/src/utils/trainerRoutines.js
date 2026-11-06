export const serviceLabel = (service) =>
  ({
    fitness: 'Fitness',
    musculacion: 'Musculación',
    cardio: 'Cardio',
    baile: 'Baile',
  })[service] ||
  service ||
  'Servicio';
export const dayLabel = (day) =>
  ({
    lunes: 'Lunes, Miércoles, Viernes',
    martes: 'Martes, Jueves',
    miercoles: 'Miércoles',
    jueves: 'Jueves',
    viernes: 'Viernes',
    sabado: 'Sábado',
    domingo: 'Domingo',
  })[day] ||
  day ||
  'Día';
export const sortedProgress = (list) =>
  [...(Array.isArray(list) ? list : [])].sort((a, b) => {
    const diff = new Date(b.fecha) - new Date(a.fecha);
    if (!Number.isNaN(diff) && diff !== 0) return diff;
    return Number(b.id_progreso || 0) - Number(a.id_progreso || 0);
  });
export const formatProgressDate = (value) => {
  if (!value) return 'Fecha no registrada';
  const text = String(value);
  const date = new Date(
    /^\d{4}-\d{2}-\d{2}$/.test(text) ? `${text}T00:00:00` : text,
  );
  return Number.isNaN(date.getTime())
    ? text
    : date.toLocaleDateString('es-PE', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
      });
};
export const isCompleted = (estado) =>
  String(estado || '').toUpperCase() === 'REALIZADO';
export const isEnrollmentActive = (item) => {
  const estado = String(item?.estado || '')
    .trim()
    .toUpperCase();
  return !estado || ['ACTIVA', 'ACTIVO', 'VIGENTE'].includes(estado);
};
