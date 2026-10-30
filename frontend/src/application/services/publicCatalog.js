import { createBackendGateway } from "./backendGateway.js";
import { requireList } from './responseValidation.js';
import { normalizePlanFromBackend, normalizePromotionFromBackend } from '../../domain/utils/gymRules.js';

export const usePublicCatalog = (gateway = createBackendGateway()) => ({
  loadPublicSchedules: () => gateway.apiGet("/gym/horarios-publicos"),
  loadMembershipPlans: () => gateway.apiGet("/planes-membresia"),
  loadCurrentPromotions: () => gateway.apiGet("/promociones/vigentes-publico"),
  async loadClientMembershipCatalog({ includeHistorical = false } = {}) {
    const [plans, promotions] = await Promise.all([
      gateway.apiGet('/planes-membresia'),
      gateway.apiGet(includeHistorical ? '/promociones' : '/promociones/vigentes-publico'),
    ]);
    const normalizedPlans = requireList(plans, 'id_pm').map((plan) => {
      if (!String(plan.nombre_plan || plan.name || '').trim()
        || !Number.isFinite(Number(plan.precio ?? plan.price)) || Number(plan.precio ?? plan.price) < 0) {
        throw new Error('El catálogo de planes contiene datos incompletos.');
      }
      return normalizePlanFromBackend(plan);
    });
    return {
      plans: normalizedPlans,
      promotions: requireList(promotions, 'id_promocion').map((item) => {
        const promotion = normalizePromotionFromBackend(item);
        if (!Number.isFinite(promotion.discountValue) || promotion.discountValue < 0
          || (promotion.discountType === 'percent' && promotion.discountValue > 100)) {
          throw new Error('El catálogo de promociones contiene descuentos inválidos.');
        }
        return promotion;
      }),
    };
  },
});
