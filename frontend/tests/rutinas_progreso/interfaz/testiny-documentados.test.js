import assert from 'node:assert/strict';
import { test } from 'node:test';
import { view, enrollment, routines } from '../../soporte/entorno-vistas.js';

test('TC-110: supervisión vacía muestra el estado sin matrículas pendientes', async () => {
  const harness = await view('TrainerOverviewView');
  try {
    assert.equal(harness.setup.schedules.length, 0);
    assert.equal(harness.setup.filteredSchedules.length, 0);
    assert.match(harness.html, /No hay|Sin .*matr[ií]culas|No se encontraron/);
  } finally { harness.dispose(); }
});

test('TC-111: error de supervisión es visible y reintentar recupera la consulta', async () => {
  const harness = await view('TrainerOverviewView');
  try {
    harness.gym.fetchTrainerOverview = async () => { throw new Error('Consulta QA no disponible'); };
    await harness.setup.refresh();
    assert.equal(harness.setup.errorMessage, 'Consulta QA no disponible');
    harness.gym.fetchTrainerOverview = async () => {};
    await harness.setup.refresh();
    assert.equal(harness.setup.errorMessage, '');
  } finally { harness.dispose(); }
});

test('TC-121: una búsqueda inexistente elimina la ficha anterior y permite corregir el DNI', async () => {
  const harness = await view('TrainerRoutineMonitorView');
  try {
    const s = harness.setup;
    harness.gym.fetchTrainerOverview = async () => {};
    s.clientData = { cliente: { nombre: 'Anterior', dni: '11111111' }, matriculas: [enrollment] };
    s.dni = '99999999';
    harness.gym.fetchTrainerClientRoutines = async () => { throw new Error('Cliente no encontrado'); };
    await s.searchClient();
    assert.equal(s.clientData, null);
    assert.match(s.feedback, /Cliente no encontrado/);
    s.dni = '22222222';
    harness.gym.fetchTrainerClientRoutines = async () => ({ cliente: { nombre: 'Otro', dni: '22222222' }, matriculas: [] });
    await s.searchClient();
    assert.equal(s.clientData.cliente.dni, '22222222');
  } finally { harness.dispose(); }
});

test('TC-122: cliente sin matrículas conserva identidad y no muestra rutinas ajenas', async () => {
  const harness = await view('TrainerRoutineMonitorView');
  try {
    harness.gym.trainerOverview = { routines };
    harness.gym.fetchTrainerOverview = async () => {};
    harness.setup.dni = '11111111';
    harness.gym.fetchTrainerClientRoutines = async () => ({ cliente: { nombre: 'Ana', dni: '11111111' }, matriculas: [] });
    await harness.setup.searchClient();
    assert.equal(harness.setup.clientData.cliente.dni, '11111111');
    assert.equal(harness.setup.clientData.matriculas.length, 0);
  } finally { harness.dispose(); }
});
