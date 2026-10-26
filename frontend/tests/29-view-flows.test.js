import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, effectScope, h, reactive } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';

let server, installServices, useGymStore, useRestTimer;
before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('..', import.meta.url)),
    configFile: false,
    plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useGymStore } = await server.ssrLoadModule(
    '/src/application/stores/gymStore.js',
  ));
  ({ useRestTimer } = await server.ssrLoadModule(
    '/src/presentation/composables/trainer/useRestTimer.js',
  ));
});
after(async () => {
  await server?.close();
});

const view = async (filename, { attendance = {}, prepare } = {}) => {
  const { default: View } = await server.ssrLoadModule(
    `/src/presentation/views/${filename}.vue`,
  );
  const pinia = createPinia();
  installServices(pinia, { attendance });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: View }],
  });
  await router.push('/');
  const instances = [];
  let setup;
  const app = createSSRApp({ render: () => h(View) });
  app.use(pinia).use(router);
  app.mixin({
    created() {
      instances.push(this.$);
      if (this.$.type === View) {
        setup = this.$.setupState;
        prepare?.(setup, useGymStore(pinia));
      }
    },
  });
  const context = {};
  const html = await renderToString(app, context);
  return {
    setup,
    gym: useGymStore(pinia),
    html,
    dialogs: Object.values(context.teleports || {}).join(''),
    child: (name) =>
      instances.find((instance) => instance.type.__name === name)?.setupState,
    dispose: () => instances.forEach((instance) => instance.scope.stop()),
  };
};

const client = (dni) => ({
  fecha: '2026-10-24',
  cliente: { nombre: 'Ana', dni, estado: 'ACTIVO' },
  membresia: { fecha_fin: '2026-11-24' },
  horarios: [],
  general: { puede_entrar: true },
});
const summary = {
  fecha: '2026-10-24',
  entradas: 2,
  salidas: 1,
  dentro: 1,
  capacidad: 20,
  disponibles: 19,
  pendientes: [],
};
const enrollment = {
  id_matricula: 7,
  id_rutina: 1,
  servicio: 'fitness',
  estado: 'ACTIVA',
  dia: 'sabado',
  hora_inicio: '10:00',
  hora_fin: '11:00',
  rutina_nombre: 'Fuerza',
};
const routines = [
  {
    id_rutina: 1,
    servicio: 'fitness',
    nombre_rutina: 'Fuerza',
    ejercicios: [
      {
        id_ejercicio: 1,
        nombre_ejercicio: 'Sentadilla',
        series: 3,
        peso_sugerido_kg: 0,
      },
    ],
  },
  { id_rutina: 2, servicio: 'fitness', nombre_rutina: 'Resistencia' },
  { id_rutina: 3, servicio: 'baile', nombre_rutina: 'Salsa' },
];

test('attendance ignores replaced searches and responses received after disposal', async () => {
  const pending = new Map();
  const harness = await view('AttendanceView', {
    attendance: {
      attendanceGet: (_path, { dni }) =>
        new Promise((resolve) => pending.set(dni, resolve)),
    },
  });
  try {
    const s = harness.setup;
    s.dni = '12345678';
    const first = s.lookupClient();
    s.dni = '87654321';
    const second = s.lookupClient();
    pending.get('87654321')(client('87654321'));
    await second;
    pending.get('12345678')(client('12345678'));
    await first;
    assert.equal(s.clientData.cliente.dni, '87654321');
    s.dni = '11111111';
    const obsolete = s.lookupClient();
    harness.dispose();
    pending.get('11111111')(client('11111111'));
    await obsolete;
    assert.equal(s.clientData, null);
  } finally {
    harness.dispose();
  }
});

test('general attendance retains its request identity after failure and starts a new identity after success', async () => {
  const identities = [];
  const harness = await view('AttendanceView', {
    attendance: {
      attendanceGet: async (path) =>
        path === '/resumen' ? summary : client('12345678'),
      generalAttendanceEntry: async (dni, identity) => {
        assert.equal(dni, '12345678');
        identities.push(identity);
        if (identities.length === 1) throw new Error('Conexión interrumpida');
      },
    },
  });
  try {
    const s = harness.setup;
    s.dni = '12345678';
    await s.lookupClient();
    await s.enterGeneral();
    assert.equal(s.error, 'Conexión interrumpida');
    assert.equal(s.clientData.cliente.dni, '12345678');
    await s.enterGeneral();
    assert.equal(identities[0], identities[1]);
    assert.match(s.feedback, /Entrada general registrada/);
    await s.enterGeneral();
    assert.notEqual(identities[1], identities[2]);
  } finally {
    harness.dispose();
  }
});

test('attendance prevents duplicate writes and preserves the last summary when refresh fails', async () => {
  let complete,
    writes = 0;
  const harness = await view('AttendanceView', {
    attendance: {
      attendanceGet: async (path) => {
        if (path === '/resumen') throw new Error('Resumen no disponible');
        return client('12345678');
      },
      attendanceEntry: () => {
        writes++;
        return new Promise((resolve) => {
          complete = resolve;
        });
      },
    },
  });
  try {
    const s = harness.setup;
    s.clientData = client('12345678');
    s.summary = summary;
    const pending = s.enter(enrollment);
    await s.enter(enrollment);
    assert.equal(writes, 1);
    assert.equal(s.busy, 'entry-7');
    complete();
    await pending;
    assert.equal(s.summary.entradas, 2);
    assert.equal(s.error, 'Resumen no disponible');
    assert.equal(s.savedKey, 'entry-7');
    assert.equal(s.busy, '');
  } finally {
    harness.dispose();
  }
});

test('attendance renders its extracted schedule controls and overdue general visits', async () => {
  const harness = await view('AttendanceView', {
    prepare: (s) => {
      s.clientData = {
        ...client('12345678'),
        horarios: [{ ...enrollment, hoy: true, puede_entrar: true }],
      };
      s.summary = {
        ...summary,
        pendientes: [
          {
            id_asistencia: 9,
            cliente_nombre: 'Ana pendiente',
            cliente_dni: '87654321',
            tipo: 'horario',
            servicio: 'fitness',
            fecha: '2026-10-23',
            hora_entrada: '10:00',
          },
        ],
      };
    },
  });
  try {
    assert.match(harness.html, /Horarios de hoy/);
    assert.match(harness.html, /Registrar entrada/);
    assert.match(harness.html, /Ana pendiente/);
    assert.match(harness.html, /is-overdue/);
    const lookup = harness.child('AttendanceClientLookup');
    lookup.dni = '87654321';
    assert.equal(harness.setup.dni, '87654321');
  } finally {
    harness.dispose();
  }
});

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
