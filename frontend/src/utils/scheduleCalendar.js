import { addDays, limaDate } from './attendance.js';
import { DAY_ORDER, normalizeScheduleDay } from './scheduleEnrollment.js';

export const weekStart = (date) => {
  const weekday = new Date(`${date}T12:00:00Z`).getUTCDay();
  return addDays(date, -((weekday + 6) % 7));
};

export const monthWeeks = (month) => {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return [];
  const first = `${month}-01`;
  const last = new Date(`${first}T12:00:00Z`);
  last.setUTCMonth(last.getUTCMonth() + 1, 0);
  const lastISO = last.toISOString().slice(0, 10);
  const weeks = [];
  for (let start = weekStart(first); start <= lastISO; start = addDays(start, 7)) {
    const end = addDays(start, 6);
    weeks.push({ start, end, from: start < first ? first : start, to: end > lastISO ? lastISO : end });
  }
  return weeks;
};

export const calendarDate = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return limaDate();
  const parsed = new Date(`${value}T12:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value ? value : limaDate();
};

// One occurrence per enrolled class and date; never reuse another week's attendance.
export const scheduleOccurrences = (items, start, month = '') => {
  const monday = weekStart(start);
  return items.flatMap((item) => {
    const index = DAY_ORDER.indexOf(normalizeScheduleDay(item.dia));
    if (index < 0) return [];
    const fecha = addDays(monday, index);
    if (month && !fecha.startsWith(month)) return [];
    if (item.id_matricula && (String(item.fecha_matricula || '').slice(0, 10) > fecha || item.estado === 'CANCELADA')) return [];
    const attendance = (item.asistencias || []).find((entry) =>
      !entry.anulado && (entry.fecha || entry.date) === fecha &&
      Number(entry.id_matricula) === Number(item.id_matricula) &&
      Number(entry.id_cliente_num || entry.id_cliente) === Number(item.id_cliente),
    );
    const entryTime = attendance?.hora_entrada || attendance?.hora || '';
    const exitTime = attendance?.hora_salida || '';
    return [{ ...item, fecha, entryTime, exitTime,
      checkLabel: item.id_matricula
        ? attendance ? `Entrada ${entryTime.slice(0, 5)} · Salida ${exitTime.slice(0, 5) || 'pendiente'}` : 'Sin registro'
        : '',
    }];
  }).sort((a, b) => a.fecha.localeCompare(b.fecha) || a.hora_inicio.localeCompare(b.hora_inicio));
};
