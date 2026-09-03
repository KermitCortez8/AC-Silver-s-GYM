import assert from 'node:assert/strict';
import {
  availableSlots,
  dayLabel,
  enrollmentsForClient,
  exerciseName,
  formatScheduleHours,
  isScheduleFull,
  serviceLabel,
  slotsBadgeInfo,
} from '../src/utils/scheduleEnrollment.js';

// 1. exerciseName resolution
assert.equal(
  exerciseName({ rutina_nombre: 'Sentadillas y Piernas' }),
  'Sentadillas y Piernas',
);
assert.equal(
  exerciseName({ nombre_ejercicio: 'Press de Pecho' }),
  'Press de Pecho',
);
assert.equal(
  exerciseName({ servicio: 'fitness' }),
  'Clase de Fitness',
);

// 2. formatScheduleHours
assert.equal(
  formatScheduleHours({ hora_inicio: '07:00:00', hora_fin: '08:00:00' }),
  '07:00 – 08:00',
);

// 3. slotsBadgeInfo and availableSlots
const freeSchedule = { cupos: 10, cupos_usados: 2 };
assert.equal(availableSlots(freeSchedule), 8);
assert.equal(isScheduleFull(freeSchedule), false);
const freeBadge = slotsBadgeInfo(freeSchedule);
assert.equal(freeBadge.available, 8);
assert.equal(freeBadge.tone, 'success');

const fewSlotsSchedule = { cupos: 10, cupos_usados: 9 };
assert.equal(availableSlots(fewSlotsSchedule), 1);
const fewBadge = slotsBadgeInfo(fewSlotsSchedule);
assert.equal(fewBadge.available, 1);
assert.equal(fewBadge.tone, 'warning');

const fullSchedule = { cupos: 10, cupos_usados: 10 };
assert.equal(availableSlots(fullSchedule), 0);
assert.equal(isScheduleFull(fullSchedule), true);
const fullBadge = slotsBadgeInfo(fullSchedule);
assert.equal(fullBadge.available, 0);
assert.equal(fullBadge.tone, 'danger');

// 4. labels
assert.equal(serviceLabel('musculacion'), 'Musculacion');
assert.equal(dayLabel('lunes'), 'Lunes');

// 5. enrollmentsForClient (Empty vs Populated)
const sampleSchedules = [
  {
    id_horario_servicio: 1,
    servicio: 'musculacion',
    rutina_nombre: 'Sentadillas y Piernas',
    dia: 'lunes',
    hora_inicio: '06:00',
    hora_fin: '07:00',
    cupos: 10,
  },
  {
    id_horario_servicio: 2,
    servicio: 'cardio',
    rutina_nombre: 'Cardio HIIT',
    dia: 'martes',
    hora_inicio: '07:00',
    hora_fin: '08:00',
    cupos: 12,
  },
];

// Initially empty schedule
const emptyEnrollments = enrollmentsForClient([], sampleSchedules, 5);
assert.deepEqual(emptyEnrollments, []);

// Populated schedule with enrollment for client 5
const activeEnrollments = [
  {
    id_matricula: 101,
    id_cliente: 5,
    id_horario_servicio: 1,
    estado: 'ACTIVA',
  },
  {
    id_matricula: 102,
    id_cliente: 9, // different client
    id_horario_servicio: 2,
    estado: 'ACTIVA',
  },
  {
    id_matricula: 103,
    id_cliente: 5,
    id_horario_servicio: 2,
    estado: 'CANCELADA', // should be excluded
  },
];

const clientEnrollments = enrollmentsForClient(activeEnrollments, sampleSchedules, 5);
assert.equal(clientEnrollments.length, 1);
assert.equal(clientEnrollments[0].id_matricula, 101);
assert.equal(clientEnrollments[0].rutina_nombre, 'Sentadillas y Piernas');
assert.equal(clientEnrollments[0].hora_inicio, '06:00');
assert.equal(clientEnrollments[0].servicio, 'musculacion');

console.log('✓ 11-schedule-enrollment tests passed successfully');

