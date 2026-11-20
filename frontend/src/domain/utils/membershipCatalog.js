import { todayISO } from './gymRules.js';

export const normalizePlanName = (name) => String(name || '').trim().toUpperCase();

export const promotionStatus = (promotion, date = todayISO()) => {
  if (!promotion.active) return 'paused';
  const limit = Number(promotion.limite_cupos || 0);
  if ((promotion.validUntil && promotion.validUntil < date)
    || (limit > 0 && Number(promotion.usos_actuales || 0) >= limit)) return 'ended';
  if (promotion.startsAt && promotion.startsAt > date) return 'scheduled';
  return 'current';
};

export const promotionAvailableForPlan = (promotion, planId, date = todayISO()) =>
  promotionStatus(promotion, date) === 'current'
  && (!promotion.appliesTo?.length || promotion.appliesTo.includes(planId));
