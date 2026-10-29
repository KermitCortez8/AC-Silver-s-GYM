import { requireRecord } from '../services/responseValidation.js';
import { parseQuantity } from '../../domain/utils/quantities.js';
import { getActivePinia } from 'pinia';
/** Estado y operaciones del módulo dashboard. */
import { todayISO } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';
import { inCurrentSession } from '../services/sessionBoundary.js';
import { clientMembershipGroup } from '../../domain/utils/clientDirectory.js';

/** settingsRepository: load(token) y save(settings, token) devuelven la configuración guardada. */
export const createDashboardModule = (ctx, settingsRepository) => {
  const pinia = ctx.pinia || getActivePinia();
  const validSettings = (value) => {
    requireRecord(value);
    parseQuantity(value.capacidad_total, { min: 1, label: 'La capacidad total' });
    parseQuantity(value.capacidad_por_hora, { min: 1, label: 'La capacidad por hora' });
    return value;
  };
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
    ctx.gymSettings.value = validSettings(await inCurrentSession(() => settingsRepository.load(ctx.authStore.token), pinia));
    return ctx.gymSettings.value;
  };

  const updateGymSettings = async (payload = {}) => {
    const body = {
      capacidad_total: parseQuantity(payload.capacidad_total ?? payload.totalCapacity ?? 30, { min: 1, label: 'La capacidad total' }),
      capacidad_por_hora: parseQuantity(payload.capacidad_por_hora ?? payload.hourCapacity ?? 10, { min: 1, label: 'La capacidad por hora' }),
    };
    if (ctx.apiBase) {
      ctx.gymSettings.value = validSettings(await inCurrentSession(() => settingsRepository.save(body, ctx.authStore.token), pinia));
    } else {
      ctx.gymSettings.value = body;
    }
    return ctx.gymSettings.value;
  };

  return { stats, normalizeLookupEmail, refreshGymSettingsFromBackend, updateGymSettings };
};
