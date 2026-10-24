import { createBackendGateway } from "./backendGateway.js";

export const usePublicCatalog = (gateway = createBackendGateway()) => ({
  loadPublicSchedules: () => gateway.apiGet("/gym/horarios-publicos"),
  loadMembershipPlans: () => gateway.apiGet("/planes-membresia"),
  loadCurrentPromotions: () => gateway.apiGet("/promociones/vigentes-publico"),
});
