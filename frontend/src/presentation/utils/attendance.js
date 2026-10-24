export const services = {
  fitness: 'Fitness',
  musculacion: 'Musculación',
  cardio: 'Cardio',
  baile: 'Baile',
  gimnasio: 'Gimnasio general',
};
export const days = {
  lunes: 'Lunes',
  martes: 'Martes',
  miercoles: 'Miércoles',
  jueves: 'Jueves',
  viernes: 'Viernes',
  sabado: 'Sábado',
  domingo: 'Domingo',
};
export const states = {
  dentro: 'Dentro del gimnasio',
  completada: 'Visita completada',
  anulada: 'Anulada',
};
export const shortTime = (value) => (value ? value.slice(0, 5) : '—');
export const dateLabel = (value, options = {}) =>
  value
    ? new Intl.DateTimeFormat('es-PE', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        timeZone: 'UTC',
        ...options,
      }).format(new Date(`${value.slice(0, 10)}T12:00:00Z`))
    : '—';
export { limaDate, addDays } from '../../domain/utils/dates.js';
export const initials = (name) =>
  String(name || 'Cliente')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0])
    .join('')
    .toUpperCase();
