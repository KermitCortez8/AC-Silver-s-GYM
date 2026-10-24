import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ref } from 'vue';
import { toCents, discountedPrice, orderTotals } from '../src/domain/utils/money.js';
import { limaDate, limaTime } from '../src/domain/utils/dates.js';
import { createMembershipsModule } from '../src/application/modules/memberships.js';

for (const [price, discount, kind, expected] of [
  [79, 10, 'percent', 71.10], [0.05, 10, 'percent', 0.04],
  [10.05, 2.345, 'fixed', 7.70], [79, 90, 'fixed', 0],
]) {
  test(`money: ${price} minus ${discount} ${kind} preserves cents`, () => {
    assert.equal(discountedPrice(price, discount, kind), expected);
    assert.equal(toCents('1.005'), 101);
    assert.equal(toCents(1e-2), 1);
    assert.deepEqual(orderTotals([{ precio: 0.25, cantidad: 1 }]), { subtotal: 0.25, igv: 0.05, total: 0.30 });
  });
}

test('membership quote agrees with the backend rounding policy', () => {
  const ctx = { planCatalog: ref([{ id: 'pm-1', price: 79 }]),
    promotions: ref([{ id: 'promo-1', active: true, discountType: 'percent', discountValue: 10 }]) };
  const module = createMembershipsModule(ctx);
  assert.equal(module.calculatePlanCharge('pm-1', 'promo-1').finalPrice, 71.10);
  ctx.promotions.value[0].startsAt = '2099-01-01';
  assert.equal(module.calculatePlanCharge('pm-1', 'promo-1').finalPrice, 79);
  ctx.promotions.value[0].startsAt = '';
  Object.assign(ctx.promotions.value[0], { limite_cupos: 2, usos_actuales: 2 });
  assert.equal(module.calculatePlanCharge('pm-1', 'promo-1').finalPrice, 79);
});

test('gym date and time agree around midnight regardless of browser timezone', () => {
  const instant = new Date('2026-10-23T01:30:00Z');
  assert.equal(limaDate(instant), '2026-10-22');
  assert.equal(limaTime(instant), '20:30');
  assert.equal(limaDate(new Date('2026-10-23T05:00:00Z')), '2026-10-23');
  assert.equal(limaTime(new Date('2026-10-23T05:00:00Z')), '00:00');
});

test('membership duration is measured in configured days, including month crossings', async () => {
  const { normalizePlanFromBackend, planDurationDays } = await import('../src/domain/utils/gymRules.js');
  const { addDays } = await import('../src/domain/utils/dates.js');
  const plan = normalizePlanFromBackend({ id_pm: 1, nombre_plan: 'MENSUAL', duracion: '45 dias' });
  assert.equal(planDurationDays(plan), 45);
  assert.equal(addDays('2026-01-31', planDurationDays(plan)), '2026-03-17');
  assert.equal(planDurationDays({ duracion: '1 año' }), 365);
  assert.equal(planDurationDays({ duracion: '3 meses' }), 90);
});
