import assert from 'node:assert/strict';
import test from 'node:test';

const DAY_ORDER = {
  lunes: 1,
  martes: 2,
  miercoles: 3,
  jueves: 4,
  viernes: 5,
  sabado: 6,
  domingo: 7,
};

const normalizeService = (str) =>
  String(str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const capitalizeDay = (day) => {
  const str = String(day || '').trim();
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

const normalizeScheduleItem = (item) => {
  const hora = item.hora || (item.hora_inicio && item.hora_fin ? `${item.hora_inicio}–${item.hora_fin}` : item.hora_inicio || '');
  const dia = capitalizeDay(item.dia);
  const entrenador = item.entrenador || item.rutina_nombre || 'Instructor Silver Gym';
  return {
    ...item,
    dia,
    hora,
    entrenador,
    servicio: item.servicio || '',
  };
};

const sortSchedules = (items) =>
  [...items].map(normalizeScheduleItem).sort((a, b) => {
    const dayA = DAY_ORDER[normalizeService(a.dia)] || 99;
    const dayB = DAY_ORDER[normalizeService(b.dia)] || 99;
    if (dayA !== dayB) return dayA - dayB;
    return String(a.hora || '').localeCompare(String(b.hora || ''));
  });

test('normalizes public backend schedules with formatting and fallback values', () => {
  const raw = {
    id_horario_servicio: 12,
    servicio: 'fitness',
    dia: 'martes',
    hora_inicio: '08:00',
    hora_fin: '09:00',
    rutina_nombre: 'Funcional Avanzado',
    cupos: 15,
    cupos_disponibles: 10,
  };

  const normalized = normalizeScheduleItem(raw);
  assert.equal(normalized.dia, 'Martes');
  assert.equal(normalized.hora, '08:00–09:00');
  assert.equal(normalized.entrenador, 'Funcional Avanzado');
});

test('sorts schedules by day of week and start time chronologically', () => {
  const unsorted = [
    { dia: 'viernes', hora_inicio: '18:00', hora_fin: '19:00', servicio: 'fitness' },
    { dia: 'lunes', hora_inicio: '19:00', hora_fin: '20:00', servicio: 'fitness' },
    { dia: 'lunes', hora_inicio: '07:00', hora_fin: '08:00', servicio: 'fitness' },
    { dia: 'miércoles', hora_inicio: '08:00', hora_fin: '09:00', servicio: 'fitness' },
  ];

  const sorted = sortSchedules(unsorted);
  assert.deepEqual(
    sorted.map((s) => `${s.dia} ${s.hora}`),
    [
      'Lunes 07:00–08:00',
      'Lunes 19:00–20:00',
      'Miércoles 08:00–09:00',
      'Viernes 18:00–19:00',
    ],
  );
});

test('filters schedules matching card service ignoring accents and casing', () => {
  const items = [
    { servicio: 'musculacion', dia: 'Lunes', hora: '10:00' },
    { servicio: 'Fitness', dia: 'Lunes', hora: '11:00' },
    { servicio: 'Cardio', dia: 'Martes', hora: '12:00' },
  ].map(normalizeScheduleItem);

  const filterFor = (title) =>
    items.filter((s) => normalizeService(s.servicio) === normalizeService(title));

  assert.equal(filterFor('Musculación').length, 1);
  assert.equal(filterFor('musculacion')[0].hora, '10:00');
  assert.equal(filterFor('Baile').length, 0);
});

