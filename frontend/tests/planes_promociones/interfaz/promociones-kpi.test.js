import assert from 'node:assert/strict';
import { test } from 'node:test';
import { addDays, limaDate } from '../../../src/domain/utils/dates.js';
import { setupView } from '../../soporte/entorno-formularios.js';

test('el contador y la tabla distinguen promociones vigentes, vencidas, agotadas, programadas y pausadas', async () => {
  const { setup, gym } = await setupView('PromotionsView', '/admin/promotions');
  const today = limaDate();
  gym.promotions = [
    { active: true, startsAt: today, validUntil: today },
    { active: true, validUntil: addDays(today, -1) },
    { active: true, limite_cupos: 2, usos_actuales: 2 },
    { active: true, startsAt: addDays(today, 1) },
    { active: false },
  ];

  assert.equal(setup.activePromotionsCount, 1);
  assert.deepEqual(setup.promotions.map(promo => setup.getPromoStatus(promo).label), [
    'Activa', 'Terminada', 'Terminada', 'Programada', 'Pausada',
  ]);
  gym.promotions[0].validUntil = addDays(today, -1);
  assert.equal(setup.activePromotionsCount, 0);
});

test('los KPI y el gráfico usan cobros confirmados del mes y la promoción registrada', async () => {
  const { setup, gym } = await setupView('PromotionsView', '/admin/promotions');
  const firstDay = `${limaDate().slice(0, 7)}-01`;
  const confirmed = { estado_pago: 'PAGADO', fecha_pago: firstDay };
  gym.membershipPayments = [
    { ...confirmed, id_promocion: 15, monto_pago: 60.12 },
    { ...confirmed, id_promocion: 16, monto_pago: 39.88 },
    { ...confirmed, id_promocion: null, monto_pago: 120 },
    { ...confirmed, id_promocion: null, monto_pago: 80 },
    { ...confirmed, id_promocion: 15, monto_pago: 30, estado_pago: 'PENDIENTE' },
    { ...confirmed, id_promocion: 15, monto_pago: 100, fecha_pago: addDays(firstDay, -1) },
  ];

  assert.deepEqual(setup.paymentMetrics, {
    collected: 100, share: 50, average: 50,
    withPromotion: [100, 0, 0, 0], withoutPromotion: [200, 0, 0, 0],
  });
  assert.deepEqual(setup.chartData.datasets.map(dataset => dataset.data), [
    [100, 0, 0, 0], [200, 0, 0, 0],
  ]);
});
