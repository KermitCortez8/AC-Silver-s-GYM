import assert from 'node:assert/strict';
import { test } from 'node:test';
import { effectScope, reactive } from 'vue';
import { useRestTimer, view, enrollment, routines } from '../../soporte/entorno-vistas.js';

test('direct assignment and assignment dialog use the same validated save flow', async () => {
  const harness = await view('TrainerRoutineMonitorView');
  try {
    const { setup: s, gym } = harness;
    gym.trainerOverview = { routines };
    s.clientData = { cliente: { nombre: 'Ana' }, matriculas: [enrollment] };
    s.dni = '12345678';
    const calls = [];
    gym.assignTrainerRoutine = async (...args) => calls.push(args);
    gym.fetchTrainerClientRoutines = async () => ({
      cliente: { nombre: 'Ana' },
      matriculas: [enrollment],
    });
    s.selection[7] = 3;
    await s.assignRoutine(enrollment);
    assert.equal(calls.length, 0);
    assert.match(s.feedback, /no corresponde/);
    s.selection[7] = 2;
    await s.assignRoutine(enrollment);
    assert.deepEqual(calls, [[7, 2]]);
    assert.equal(s.selection[7], undefined);
    s.openAssignModal();
    s.assignForm.id_rutina = 2;
    gym.assignTrainerRoutine = async () => {
      throw new Error('No se pudo asignar');
    };
    await s.submitAssignRoutine();
    assert.equal(s.showAssignModal, true);
    assert.equal(s.assignForm.id_rutina, 2);
    assert.equal(s.assigningId, 0);
    assert.equal(s.feedback, 'No se pudo asignar');
    gym.assignTrainerRoutine = async (...args) => calls.push(args);
    await s.submitAssignRoutine();
    assert.deepEqual(calls, [
      [7, 2],
      [7, 2],
    ]);
    assert.equal(s.showAssignModal, false);
  } finally {
    harness.dispose();
  }
});

test('progress keeps its draft on failure and clears it only after a confirmed save', async () => {
  const harness = await view('TrainerRoutineMonitorView');
  try {
    const { setup: s, gym } = harness;
    gym.trainerOverview = { routines };
    s.dni = '12345678';
    gym.fetchTrainerClientRoutines = async () => ({
      cliente: { nombre: 'Ana' },
      matriculas: [enrollment],
    });
    s.openExercisesModal(enrollment);
    const draft = s.getTracker(7, 1);
    draft[0].series_completadas = 3;
    draft[0].completado = true;
    s.observationsMap[7] = 'Buena técnica';
    let payload;
    gym.markTrainerRoutineProgress = async (_id, value) => {
      payload = value;
      throw new Error('Guardado rechazado');
    };
    await s.submitSaveProgress();
    assert.equal(s.showExercisesModal, true);
    assert.equal(s.getTracker(7, 1)[0].series_completadas, 3);
    assert.equal(s.observationsMap[7], 'Buena técnica');
    assert.equal(payload.ejercicios_detalle[0].peso_utilizado_kg, 0);
    assert.equal(payload.observacion, 'Buena técnica');
    gym.markTrainerRoutineProgress = async () => {};
    await s.submitSaveProgress();
    assert.equal(s.showExercisesModal, false);
    assert.equal(s.observationsMap[7], undefined);
    assert.equal(s.getTracker(7, 1)[0].series_completadas, 0);
  } finally {
    harness.dispose();
  }
});

test('trainer renders extracted dialogs, exercises and progress history with working form models', async () => {
  const harness = await view('TrainerRoutineMonitorView', {
    prepare: (s, gym) => {
      gym.trainerOverview = { routines };
      s.clientData = {
        cliente: { nombre: 'Ana' },
        matriculas: [
          {
            ...enrollment,
            progreso: [
              {
                id_progreso: 1,
                fecha: '2026-10-24',
                estado: 'REALIZADO',
                observacion: 'Avance guardado',
              },
            ],
          },
        ],
      };
      s.openAssignModal();
      s.openExercisesModal(enrollment);
      s.timer.seconds = 15;
    },
  });
  try {
    assert.match(harness.html, /Avance guardado/);
    assert.match(harness.dialogs, /Sentadilla/);
    assert.match(harness.dialogs, /Guardar Progreso de Sesión/);
    assert.match(harness.dialogs, /Resistencia/);
    assert.match(harness.html, /00:15/);
    assert.match(harness.dialogs, /00:15/);
    harness.child('RoutineAssignmentDialog').routineId = 2;
    assert.equal(harness.setup.assignForm.id_rutina, 2);
    harness.child('RoutineProgressDialog').observation = 'Nueva observación';
    assert.equal(harness.setup.observationsMap[7], 'Nueva observación');
    const controls = harness.child('RoutineExerciseCard');
    controls.adjustSeries(controls.ex, 10);
    assert.equal(harness.setup.getTracker(7, 1)[0].series_completadas, 3);
    assert.equal(harness.setup.getTracker(7, 1)[0].completado, true);
    controls.adjustSeries(controls.ex, -10);
    assert.equal(controls.ex.series_completadas, 0);
    assert.equal(controls.ex.completado, false);
    controls.adjustWeight(controls.ex, -2.5);
    assert.equal(controls.ex.peso_utilizado_kg, 0);
  } finally {
    harness.dispose();
  }
});

test('unassigning another enrollment keeps the exercise draft and preserves confirmation on failure', async () => {
  const harness = await view('TrainerRoutineMonitorView');
  try {
    const { setup: s, gym } = harness;
    gym.trainerOverview = { routines };
    s.dni = '12345678';
    s.openExercisesModal(enrollment);
    s.getTracker(7, 1)[0].series_completadas = 2;
    s.confirmUnassign({ ...enrollment, id_matricula: 8 });
    assert.equal(s.selectedMatriculaItem.id_matricula, 7);
    const calls = [];
    gym.assignTrainerRoutine = async (...args) => {
      calls.push(args);
      throw new Error('No se pudo desvincular');
    };
    await s.submitUnassign();
    assert.deepEqual(calls, [[8, 0]]);
    assert.equal(s.showConfirmModal, true);
    assert.equal(s.isUnassigning, false);
    assert.equal(s.getTracker(7, 1)[0].series_completadas, 2);
    gym.assignTrainerRoutine = async () => {};
    gym.fetchTrainerClientRoutines = async () => ({
      cliente: { nombre: 'Ana' },
      matriculas: [enrollment],
    });
    await s.submitUnassign();
    assert.equal(s.showConfirmModal, false);
  } finally {
    harness.dispose();
  }
});

test('one rest timer supports pause, resume, completion and disposal without leaked intervals', (t) => {
  t.mock.timers.enable({ apis: ['setInterval'] });
  const scope = effectScope();
  const timer = scope.run(() => reactive(useRestTimer()));
  try {
    timer.start(3);
    t.mock.timers.tick(1000);
    assert.equal(timer.seconds, 2);
    timer.pause();
    t.mock.timers.tick(5000);
    assert.equal(timer.seconds, 2);
    timer.resume();
    t.mock.timers.tick(2000);
    assert.equal(timer.seconds, 0);
    assert.equal(timer.finished, true);
    assert.equal(timer.active, false);
    timer.resume();
    assert.equal(timer.seconds, 3);
    scope.stop();
    t.mock.timers.tick(5000);
    assert.equal(timer.seconds, 3);
    assert.equal(timer.active, false);
  } finally {
    scope.stop();
  }
});
