/** Estado y operaciones del módulo dashboard. */
import { todayISO } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';
import { clientMembershipGroup } from '../../domain/utils/clientDirectory.js';
import { backendRequest } from '../services/backendGateway.js';

export const createDashboardModule = (ctx) => {
  const stats = computed(() => {
    const today = todayISO();
    const lowStockItems = ctx.inventory.value.filter((item) => item.quantity <= item.minQuantity).length;

    return {
      totalMembers: ctx.members.value.length,
      activeMembers: ctx.members.value.filter((member) => clientMembershipGroup(member) === 'active').length,
      attendanceToday: ctx.attendance.value.filter((entry) => entry.date === today).length,
      inventoryItems: ctx.inventory.value.length,
      lowStockItems,
      attendanceRate: ctx.members.value.length
        ? Math.round(
          ctx.members.value.reduce((sum, member) => sum + Number(member.attendanceRate || 0), 0) /
          ctx.members.value.length,
        )
        : 0,
    };
  });

  const normalizeLookupEmail = (value) => String(value || '').trim().toLowerCase();

  const refreshGymSettingsFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const response = await backendRequest(`${ctx.apiBase}/gym/configuracion`, { headers: ctx._authHeaders() });
    if (!response.ok) throw new Error(await ctx.readBackendError(response, 'Error al cargar configuracion'));
    ctx.gymSettings.value = await response.json();
    ctx.persist();
    return ctx.gymSettings.value;
  };

  const updateGymSettings = async (payload = {}) => {
    const body = {
      capacidad_total: Number(payload.capacidad_total || payload.totalCapacity || 30),
      capacidad_por_hora: Number(payload.capacidad_por_hora || payload.hourCapacity || 10),
    };
    if (ctx.apiBase) {
      const response = await backendRequest(`${ctx.apiBase}/gym/configuracion`, {
        method: 'POST',
        headers: ctx._authHeaders(),
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(await ctx.readBackendError(response, 'No se pudo guardar configuracion'));
      ctx.gymSettings.value = await response.json();
    } else {
      ctx.gymSettings.value = body;
    }
    ctx.persist();
    return ctx.gymSettings.value;
  };

  return { stats, normalizeLookupEmail, refreshGymSettingsFromBackend, updateGymSettings };
};
