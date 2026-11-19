import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setupView } from '../../soporte/entorno-formularios.js';

const date = '2099-10-05';
const nextDate = '2099-10-12';
const routines = [
  { id_rutina: 7, servicio: 'fitness', nombre_rutina: 'Circuito QA' },
  { id_rutina: 8, servicio: 'baile', nombre_rutina: 'Salsa QA' },
];
const schedule = { id_horario_servicio: 1, id_rutina: 7, servicio: 'fitness', rutina_nombre: 'Circuito QA',
  codigo_dia: 'LUN', dia: 'lunes', hora_inicio: '10:00', hora_fin: '11:00', cupos: 1,
  activo: true, cupos_usados: 1, ocupacion_por_fecha: { [date]: 1 } };
const inactive = { ...schedule, id_horario_servicio: 2, id_rutina: 8, servicio: 'baile', rutina_nombre: 'Salsa QA',
  activo: false, cupos_usados: 0, ocupacion_por_fecha: {} };
const setupSchedules = prepare => setupView('ServiceSchedulesView', '/admin/service-schedules', (setup, gym) => {
  gym.serviceSchedules = [schedule, inactive];
  gym.routines = routines;
  prepare?.(setup, gym);
});

test('TC-054: el editor nuevo filtra rutinas por servicio y conserva el código del día', async () => {
  const { setup, dialogs } = await setupSchedules(setup => {
    setup.openNewSchedule();
    setup.form.servicio = 'fitness';
  });
  assert.match(dialogs, /Nuevo horario/);
  assert.deepEqual(setup.routinesForSelectedService.map(item => item.id_rutina), [7]);
  setup.form.servicio = 'baile';
  assert.deepEqual(setup.routinesForSelectedService.map(item => item.id_rutina), [8]);
  setup.editSchedule(schedule);
  assert.equal(setup.form.codigo_dia, 'LUN');
});

test('TC-055: los filtros y la semana cambian lo visible sin escribir cupos', async () => {
  const { setup, gym, html } = await setupSchedules(setup => {
    setup.showList = true;
    setup.visibleRange = { start: date, month: '2099-10' };
  });
  assert.match(html, /Circuito QA/);
  assert.match(html, /Salsa QA/);
  assert.match(html, /10:00/);
  setup.visibleRange = { start: date, month: '2099-10' };
  setup.filters.search = 'circuito';
  setup.filters.servicio = 'fitness';
  setup.filters.dia = 'lunes';
  assert.deepEqual(setup.filteredSchedules.map(item => item.id_horario_servicio), [1]);
  assert.equal(setup.weeklySchedules[0].fecha, date);
  assert.equal(setup.weeklySchedules[0].cupos_usados, 1);
  setup.filters.estado = 'con-cupos';
  assert.deepEqual(setup.filteredSchedules, []);
  setup.filters.estado = 'llenos';
  assert.deepEqual(setup.filteredSchedules.map(item => item.id_horario_servicio), [1]);
  setup.visibleRange = { start: nextDate, month: '2099-10' };
  assert.equal(setup.weeklySchedules[0].cupos_usados, 0);
  setup.resetFilters();
  assert.equal(setup.filteredSchedules.length, 2);
  assert.equal(gym.serviceSchedules[0].ocupacion_por_fecha[date], 1);
});

test('TC-057: cancelar la confirmación conserva el horario sin llamar al borrado', async () => {
  const { setup, gym, dialogs } = await setupSchedules(setup => setup.removeSchedule(inactive));
  assert.match(dialogs, /Eliminar este horario/);
  let deletions = 0;
  gym.deleteServiceSchedule = async () => { deletions++; };
  setup.pendingDelete = null;
  await setup.confirmRemoveSchedule();
  assert.equal(deletions, 0);
  assert.deepEqual(gym.serviceSchedules, [schedule, inactive]);
});

test('TC-062: una clase llena deshabilita la acción y otra semana tiene cupo propio', async () => {
  const { setup, gym, dialogs } = await setupView('EnrollmentView', '/user/schedule', (setup, gym) => {
    setup.user = { role: 'user', id_cliente: 1, dni: '12345678' };
    gym.members = [{ id_cliente: 1, name: 'Cliente QA' }];
    gym.serviceSchedules = [schedule];
    setup.openSchedulePicker();
    setup.selectAvailableSchedule({ ...schedule, fecha: date });
  });
  assert.equal(setup.currentClientId, 1);
  setup.selectAvailableSchedule({ ...schedule, fecha: date });
  assert.equal(setup.selectedActionDisabled, true);
  assert.equal(setup.selectedActionLabel, 'Sin cupos disponibles');
  assert.match(dialogs, /Elige una clase/);
  let writes = 0;
  gym.enrollSchedule = async () => { writes++; };
  await setup.enrollSelected();
  assert.equal(writes, 0);
  setup.selectAvailableSchedule({ ...schedule, fecha: nextDate });
  assert.equal(setup.selectedActionDisabled, false);
  assert.equal(setup.selectedActionLabel, 'Agregar a mi horario');
});
