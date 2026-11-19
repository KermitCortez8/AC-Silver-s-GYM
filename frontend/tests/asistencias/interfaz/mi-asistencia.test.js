import assert from 'node:assert/strict';
import { test } from 'node:test';
import { view } from '../../soporte/entorno-vistas.js';

const response = {
  inicio: '2026-11-16',
  hoy: '2026-11-19',
  horarios: [
    { id_matricula: 7, fecha: '2026-11-17', servicio: 'fitness', hora_inicio: '07:00', hora_fin: '08:00',
      cupos: 10, asistencia: { fecha: '2026-11-17', estado: 'completada', hora_entrada: '07:10', hora_salida: '08:00' } },
    { id_matricula: 8, fecha: '2026-11-19', servicio: 'cardio', hora_inicio: '06:00', hora_fin: '07:00' },
    { id_matricula: 9, fecha: '2026-11-21', servicio: 'baile', hora_inicio: '10:00', hora_fin: '11:00' },
  ],
  generales: [
    { id_asistencia: 7, fecha: '2026-11-18', estado: 'incompleta', hora_entrada: '22:10', hora_salida: '01:10',
      fecha_salida: '2026-11-19', cierre_automatico: true, auditoria: [{ actor_id: 'personal-qa' }] },
    { id_asistencia: 8, fecha: '2026-11-19', estado: 'dentro', hora_entrada: '08:30' },
  ],
};

test('el calendario personal conserva fechas, horas reales y estados de los dos tipos de asistencia', async () => {
  const harness = await view('UserAttendanceView', {
    prepare(setup) {
      setup.selectedDate = '2026-11-19';
      setup.week = response;
    },
  });
  try {
    assert.match(harness.html, /Calendario de asistencia/);
    assert.match(harness.html, /3 visitas registradas/);
    assert.doesNotMatch(harness.html, /Registrar entrada|Registrar salida|Cupos libres/);
    const calendar = harness.child('ExcelScheduleGrid');
    assert.equal(calendar.props.interactive, false);
    assert.deepEqual(calendar.occurrences.map((item) => item.statusLabel),
      ['Completada', 'Incompleta', 'Sin registro', 'En curso', 'Programado']);
    const identifiers = calendar.calendarEvents.map((event) => event.id);
    assert.equal(new Set(identifiers).size, 5);
    const overnight = calendar.calendarEvents.find((event) => event.id === 'general-7');
    assert.equal(overnight.start, '2026-11-18T22:10:00');
    assert.equal(overnight.end, '2026-11-18T24:00:00');
    assert.match(overnight.extendedProps.checkLabel, /Cierre automático 01:10/);
    assert.equal(overnight.extendedProps.auditoria, undefined);
    const current = calendar.calendarEvents.find((event) => event.id === 'general-8');
    assert.equal(current.extendedProps.hora_fin, undefined);
    assert.match(current.extendedProps.checkLabel, /Entrada 08:30 · Salida pendiente/);
    harness.setup.visitType = 'general';
    assert.equal(harness.setup.visibleVisits, 2);
    assert.deepEqual(harness.setup.calendarItems.map((item) => item.calendarId), ['general-7', 'general-8']);
    harness.setup.visitType = 'horario';
    assert.equal(harness.setup.visibleVisits, 1);
    assert.ok(harness.setup.calendarItems.every((item) => item.cupos === undefined));
  } finally {
    harness.dispose();
  }
});

test('cambiar de semana solo consulta la sesión propia y descarta la respuesta anterior', async () => {
  const requests = [];
  const harness = await view('UserAttendanceView', {
    attendance: {
      attendanceGet: (path, params, token) => new Promise((resolve) => {
        requests.push({ path, params, token, resolve });
      }),
    },
    prepare(setup) {
      setup.token = 'sesion-sintetica';
      setup.selectedDate = '2026-11-19';
    },
  });
  try {
    const first = harness.setup.load();
    harness.setup.selectedDate = '2026-11-26';
    const second = harness.setup.load();
    assert.deepEqual(requests.map(({ path, params, token }) => ({ path, params, token })), [
      { path: '/mi-semana', params: { inicio: '2026-11-16' }, token: 'sesion-sintetica' },
      { path: '/mi-semana', params: { inicio: '2026-11-23' }, token: 'sesion-sintetica' },
    ]);
    requests[1].resolve({ inicio: '2026-11-23', horarios: [], generales: [] });
    await second;
    requests[0].resolve(response);
    await first;
    assert.equal(harness.setup.week.inicio, '2026-11-23');
    assert.deepEqual(harness.setup.calendarItems, []);
  } finally {
    harness.dispose();
  }
});
