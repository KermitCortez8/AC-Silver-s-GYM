import { apiGet } from './backendGateway.js';

export const loadPublicSchedules = () => apiGet('/gym/horarios-publicos');
export const loadMembershipPlans = () => apiGet('/planes-membresia');
export const loadCurrentPromotions = () => apiGet('/promociones/vigentes-publico');
