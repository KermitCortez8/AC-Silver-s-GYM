import { getActivePinia } from 'pinia';
/** Estado y operaciones del módulo dashboard. */
import { todayISO } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';
import { inCurrentSession } from '../services/sessionBoundary.js';
import { clientMembershipGroup } from '../../domain/utils/clientDirectory.js';

/** settingsRepository: load(token) y save(settings, token) devuelven la configuración guardada. */
export const createDashboardModule = (ctx, settingsRepository) => {
  const pinia = ctx.pinia || getActivePinia();
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
    ctx.gymSettings.value = await inCurrentSession(() => settingsRepository.load(ctx.authStore.token), pinia);
    return ctx.gymSettings.value;
  };

  const updateGymSettings = async (payload = {}) => {
    const body = {
      capacidad_total: Number(payload.capacidad_total || payload.totalCapacity || 30),
      capacidad_por_hora: Number(payload.capacidad_por_hora || payload.hourCapacity || 10),
    };
    if (ctx.apiBase) {
      ctx.gymSettings.value = await inCurrentSession(() => settingsRepository.save(body, ctx.authStore.token), pinia);
    } else {
      ctx.gymSettings.value = body;
    }
    return ctx.gymSettings.value;
  };

  return { stats, normalizeLookupEmail, refreshGymSettingsFromBackend, updateGymSettings };
};
