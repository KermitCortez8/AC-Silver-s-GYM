import { todayISO } from './gymRules.js';

export const normalizePlanName = (name) => String(name || '').trim().toUpperCase();

export const promotionAvailableForPlan = (promotion, planId, date = todayISO()) => {
  if (!promotion.active || (promotion.startsAt && promotion.startsAt > date)
    || (promotion.validUntil && promotion.validUntil < date)) return false;
  const limit = Number(promotion.limite_cupos || 0);
  if (limit > 0 && Number(promotion.usos_actuales || 0) >= limit) return false;
  return !promotion.appliesTo?.length || promotion.appliesTo.includes(planId);
};
