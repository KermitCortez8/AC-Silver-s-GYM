import test from 'node:test';
import assert from 'node:assert/strict';
import { calendarDate, monthWeeks, scheduleOccurrences, weekStart } from '../src/utils/scheduleCalendar.js';

test('month weeks include partial weeks, leap day and year boundaries', () => {
  const weeks = monthWeeks('2026-03');
  assert.equal(weeks.length, 6);
  assert.deepEqual(weeks[0], { start: '2026-02-23', end: '2026-03-01', from: '2026-03-01', to: '2026-03-01' });
  assert.equal(weeks.at(-1).to, '2026-03-31');
  assert.equal(monthWeeks('2024-02').at(-1).to, '2024-02-29');
  assert.equal(weekStart('2027-01-01'), '2026-12-28');
  assert.deepEqual(monthWeeks('2026-13'), []);
  assert.equal(calendarDate('2024-02-29'), '2024-02-29');
  assert.notEqual(calendarDate('2026-02-30'), '2026-02-30');
});

const monday = { id_horario_servicio: 10, dia: 'lunes', hora_inicio: '08:00', hora_fin: '09:00' };
test('recurring schedules have a different concrete date in each week', () => {
  assert.equal(scheduleOccurrences([monday], '2026-09-01', '2026-09').length, 0);
  assert.equal(scheduleOccurrences([monday], '2026-09-07', '2026-09')[0].fecha, '2026-09-07');
  assert.equal(scheduleOccurrences([monday], '2026-09-14', '2026-09')[0].fecha, '2026-09-14');
});

test('attendance belongs to the exact client, enrollment and session date', () => {
  const enrollment = { ...monday, id_cliente: 1, id_matricula: 20, fecha_matricula: '2026-09-01', asistencias: [
    { id_cliente: 2, id_matricula: 20, fecha: '2026-09-14', hora_entrada: '08:01' },
    { id_cliente: 1, id_matricula: 21, fecha: '2026-09-14', hora_entrada: '08:02' },
    { id_cliente: 1, id_matricula: 20, fecha: '2026-09-14', hora_entrada: '08:03', anulado: true },
    { id_cliente: 1, id_matricula: 20, fecha: '2026-09-07', hora_entrada: '08:04', hora_salida: '09:00' },
  ] };
  assert.equal(scheduleOccurrences([enrollment], '2026-09-07')[0].entryTime, '08:04');
  assert.equal(scheduleOccurrences([enrollment], '2026-09-14')[0].checkLabel, 'Sin registro');
  assert.equal(scheduleOccurrences([enrollment], '2026-08-31').length, 0);
  assert.equal(scheduleOccurrences([{ ...enrollment, estado: 'CANCELADA' }], '2026-09-14').length, 0);
});
