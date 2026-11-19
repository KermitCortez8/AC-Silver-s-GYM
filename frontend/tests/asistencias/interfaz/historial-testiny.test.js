import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { view } from '../../soporte/entorno-vistas.js';

test('TC-072: el historial vacío deshabilita exportar y limpiar restaura la primera página', async () => {
  const calls = [];
  const harness = await view('AttendanceView', {
    prepare: setup => { setup.tab = 'history'; },
    attendance: {
      attendanceGet: async (path, filters) => {
        calls.push([path, filters.dni, filters.page]);
        return { total: filters.dni ? 0 : 1, items: filters.dni ? [] : [{ id_asistencia: 1 }] };
      },
    },
  });
  try {
    assert.match(harness.html, /No hay visitas con estos filtros/);
    assert.match(harness.html, /<button[^>]*disabled[^>]*>.*?Exportar Excel/s);
    const history = harness.child('AttendanceHistory');
    history.page = 3;
    history.draft.dni = '99999999';
    history.apply();
    await setImmediate();
    assert.equal(history.total, 0);
    assert.deepEqual(history.records, []);
    history.reset();
    await setImmediate();
    assert.equal(history.page, 1);
    assert.deepEqual(history.records.map(item => item.id_asistencia), [1]);
    assert.deepEqual(calls, [['/historial', '99999999', 1], ['/historial', '', 1]]);
  } finally { harness.dispose(); }
});
