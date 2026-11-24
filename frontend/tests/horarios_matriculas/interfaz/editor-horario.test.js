import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createPinia } from 'pinia';
import { ref } from 'vue';
import { createSchedulesModule } from '../../../src/application/modules/schedules.js';
import { SALAS_HORARIO } from '../../../src/domain/utils/scheduleSettings.js';
import { setupView } from '../../soporte/entorno-formularios.js';

const prepararEditor = (prepare) => setupView('ServiceSchedulesView', '/admin/service-schedules', prepare);
const parametros = { hora_inicio: '08:00', duracion_minutos: 120, cupos: 16 };

test('el editor abre mientras carga sus datos y conserva las horas ajustadas por el usuario', async () => {
  const configuracion = Promise.withResolvers();
  const rutinas = Promise.withResolvers();
  let consultasParametros = 0;
  let consultasRutinas = 0;
  const { setup, dialogs } = await prepararEditor((editor, gym) => {
    gym.loadScheduleSettings = () => { consultasParametros++; return configuracion.promise; };
    gym.refreshRoutinesFromBackend = () => { consultasRutinas++; return rutinas.promise; };
    editor.openNewSchedule();
  });
  assert.match(dialogs, /Nuevo horario/);
  assert.match(dialogs, /Cargando rutinas/);
  assert.equal(setup.isEditorOpen, true);

  setup.closeEditor();
  setup.openNewSchedule();
  assert.equal(consultasParametros, 1);
  assert.equal(consultasRutinas, 1);
  setup.form.hora_inicio = '09:00';
  setup.form.hora_fin = '10:00';
  setup.markHoursEdited();
  configuracion.resolve(parametros);
  rutinas.resolve([]);
  await configuracion.promise;
  assert.equal(setup.form.hora_inicio, '09:00');
  assert.equal(setup.form.hora_fin, '10:00');
  assert.equal(setup.form.cupos, 16);
});

test('un horario fuera de la franja muestra el motivo dentro del editor y evita el guardado', async () => {
  let guardados = 0;
  const { setup, dialogs } = await prepararEditor((editor, gym) => {
    gym.loadScheduleSettings = async () => parametros;
    gym.refreshRoutinesFromBackend = async () => [];
    gym.upsertServiceSchedule = async () => { guardados++; };
    editor.openNewSchedule();
    Object.assign(editor.form, { dia: 'domingo', hora_inicio: '17:30', hora_fin: '18:15', cupos: 8 });
    editor.markHoursEdited();
    editor.markSlotsEdited();
    void editor.saveSchedule();
  });
  assert.equal(guardados, 0);
  assert.equal(setup.isEditorOpen, true);
  assert.equal(setup.form.hora_fin, '18:15');
  assert.equal(setup.form.cupos, 8);
  assert.match(dialogs, /role="alert"[^>]*>El gimnasio atiende el domingo de 07:00 a 18:00/);
  assert.match(dialogs, /El horario solicitado de 17:30 a 18:15 queda fuera de esa franja/);
  assert.doesNotMatch(dialogs, /No se pudo completar la acción|El horario debe durar/);
});

test('guardar mientras carga el calendario conserva el horario confirmado y recupera los demás', async () => {
  const anterior = Promise.withResolvers();
  const servicio = ref([]);
  const nuevo = { id_horario_servicio: 12, id_rutina: 2, sala: SALAS_HORARIO[0] };
  const existente = { id_horario_servicio: 3, id_rutina: 1 };
  const ctx = {
    apiBase: '/api', pinia: createPinia(), authStore: { token: 'prueba' },
    serviceSchedules: servicio, routines: ref([{ id_rutina: 2, nombre_rutina: 'Circuito' }]),
  };
  let lecturas = 0;
  const horarios = createSchedulesModule(ctx, {
    refreshServiceSchedulesFromBackend: () => ++lecturas === 1 ? anterior.promise : [existente, nuevo],
    upsertServiceSchedule: async (payload) => {
      assert.equal(payload.sala, SALAS_HORARIO[0]);
      return nuevo;
    },
  });
  const primeraCarga = horarios.refreshServiceSchedulesFromBackend();
  await horarios.upsertServiceSchedule({ id_rutina: 2, sala: SALAS_HORARIO[0] });
  assert.equal(servicio.value[0].rutina_nombre, 'Circuito');
  anterior.resolve([existente]);
  await primeraCarga;
  assert.deepEqual(servicio.value, [existente, nuevo]);
  assert.equal(lecturas, 2);
});

test('crear y editar una clase requiere una sala del selector fijo', async () => {
  const guardados = [];
  const { setup, dialogs } = await prepararEditor((editor, gym) => {
    gym.loadScheduleSettings = async () => parametros;
    gym.refreshRoutinesFromBackend = async () => [];
    gym.upsertServiceSchedule = async (payload) => { guardados.push(payload); };
    editor.openNewSchedule();
    editor.form.id_rutina = 2;
    void editor.saveSchedule();
  });
  assert.match(dialogs, /Selecciona una sala para el horario/);
  for (const sala of SALAS_HORARIO) assert.ok(dialogs.includes(sala));
  assert.equal(guardados.length, 0);
  setup.form.sala = SALAS_HORARIO[0];
  await setup.saveSchedule();
  assert.equal(guardados[0].sala, SALAS_HORARIO[0]);

  setup.editSchedule({ ...guardados[0], id_horario_servicio: 5 });
  assert.equal(setup.form.sala, SALAS_HORARIO[0]);
  setup.form.sala = SALAS_HORARIO[1];
  await setup.saveSchedule();
  assert.equal(guardados[1].id_horario_servicio, 5);
  assert.equal(guardados[1].sala, SALAS_HORARIO[1]);

  setup.editSchedule({ ...guardados[1], sala: 'Sala 1' });
  assert.equal(setup.form.sala, '');
});
