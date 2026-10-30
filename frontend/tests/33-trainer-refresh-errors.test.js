import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ref } from 'vue';
import { useRoutineAssignments } from '../src/presentation/composables/trainer/useRoutineAssignments.js';
import { useRoutineProgress } from '../src/presentation/composables/trainer/useRoutineProgress.js';

const enrollment = { id_matricula: 1, id_rutina: 2, estado: 'ACTIVA', servicio: 'fitness', dia: 'lunes' };
const routines = () => ref([{ id_rutina: 2, servicio: 'fitness', nombre_rutina: 'Fuerza', ejercicios: [{ id_ejercicio: 1, series: 3 }] }]);
const unavailable = async () => { throw new Error('Ficha no disponible'); };

test('a confirmed assignment closes its dialog and reports a subsequent refresh failure separately', async () => {
  const notices = [];
  let saves = 0;
  const assignments = useRoutineAssignments({ clientData: ref({ matriculas: [enrollment] }), routines: routines(),
    assign: async () => { saves++; }, reloadClient: unavailable, notify: (...args) => notices.push(args), setFeedback: () => {} });
  assignments.openAssignModal();
  assignments.assignForm.id_rutina = 2;
  await assignments.submitAssignRoutine();
  assert.equal(saves, 1);
  assert.equal(assignments.showAssignModal.value, false);
  assert.equal(assignments.assigningId.value, 0);
  assert.equal(notices[0][1], 'info');
  assert.match(notices[0][0], /asignada.*No se pudo actualizar/);
});

test('a confirmed unassignment closes its confirmation even when reloading fails', async () => {
  const notices = [];
  let saves = 0;
  const assignments = useRoutineAssignments({ clientData: ref({ matriculas: [enrollment] }), routines: routines(),
    assign: async () => { saves++; }, reloadClient: unavailable, notify: (...args) => notices.push(args), setFeedback: () => {} });
  assignments.confirmUnassign(enrollment);
  await assignments.submitUnassign();
  assert.equal(saves, 1);
  assert.equal(assignments.showConfirmModal.value, false);
  assert.equal(notices[0][1], 'info');
});

test('confirmed progress clears its saved draft and reports refresh failure without offering a duplicate save', async () => {
  const notices = [];
  let saves = 0;
  const progress = useRoutineProgress({ routines: routines(), saveProgress: async () => { saves++; },
    reloadClient: unavailable, notify: (...args) => notices.push(args) });
  progress.openExercisesModal(enrollment);
  progress.getTracker(1, 2)[0].series_completadas = 3;
  progress.observationsMap[1] = 'Buena técnica';
  await progress.submitSaveProgress();
  assert.equal(saves, 1);
  assert.equal(progress.showExercisesModal.value, false);
  assert.equal(progress.observationsMap[1], undefined);
  assert.equal(progress.getTracker(1, 2)[0].series_completadas, 0);
  assert.equal(progress.isSavingProgress.value, false);
  assert.equal(notices[0][1], 'info');
  assert.match(notices[0][0], /registrado.*No se pudo actualizar/);
});
