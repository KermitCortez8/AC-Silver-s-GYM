import { parseQuantity } from './quantities.js';

export const INITIAL_SCHEDULE_SETTINGS = Object.freeze({
  hora_inicio: '06:00',
  duracion_minutos: 60,
  cupos: 10,
});

export const SCHEDULE_DURATIONS = Object.freeze([60, 120]);
export const SALAS_HORARIO = Object.freeze(['Sala de Fuerza 1', 'Sala de Fuerza 2', 'Sala de cardio']);
export const HORARIO_ATENCION = Object.freeze([
  { dias: 'Lunes a viernes', apertura: '06:00', cierre: '22:00' },
  { dias: 'Sábado y domingo', apertura: '07:00', cierre: '18:00' },
]);

const [diasLaborables, finDeSemana] = HORARIO_ATENCION;
export const franjaDeAtencion = (dia) => dia === 'sabado' || dia === 'domingo' ? finDeSemana : diasLaborables;

export const timeToMinutes = (value) => {
  const [hour = 0, minute = 0] = String(value || '').split(':').map(Number);
  return hour * 60 + minute;
};

const formatTime = (minutes) =>
  [Math.floor(minutes / 60), minutes % 60].map((value) => String(value).padStart(2, '0')).join(':');

export const dentroDeAtencion = (dia, inicio, fin) => {
  const { apertura, cierre } = franjaDeAtencion(dia);
  return !!inicio && !!fin && apertura <= inicio && inicio < fin && fin <= cierre;
};

export const horasParaDia = (dia, { hora_inicio, duracion_minutos }) => {
  const { apertura, cierre } = franjaDeAtencion(dia);
  const inicio = Math.min(
    Math.max(timeToMinutes(hora_inicio), timeToMinutes(apertura)),
    timeToMinutes(cierre) - duracion_minutos,
  );
  return { hora_inicio: formatTime(inicio), hora_fin: formatTime(inicio + duracion_minutos) };
};

export const validateScheduleSettings = ({ hora_inicio, duracion_minutos, cupos }) => {
  if (typeof hora_inicio !== 'string' || !/^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(hora_inicio)) {
    throw new Error('Ingresa una hora de inicio válida.');
  }
  if (!SCHEDULE_DURATIONS.includes(duracion_minutos)) {
    throw new Error('Selecciona una duración de 1 o 2 horas.');
  }
  if (timeToMinutes(hora_inicio) + duracion_minutos >= 24 * 60) {
    throw new Error('La clase debe terminar antes de medianoche.');
  }
  return { hora_inicio, duracion_minutos, cupos: parseQuantity(cupos, { min: 1, label: 'Los cupos' }) };
};
