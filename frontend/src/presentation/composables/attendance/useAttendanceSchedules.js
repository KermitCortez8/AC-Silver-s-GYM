import { computed, ref } from 'vue';
import { days, shortTime, limaDate } from '../../utils/attendance.js';

export const useAttendanceSchedules = (clientData) => {
  const todayName = () =>
    new Date(
      `${clientData.value?.fecha || limaDate()}T12:00:00`,
    ).toLocaleDateString('es-PE', { weekday: 'long' });
  const blockedText = (item) =>
    !item.hoy && item.motivo?.includes('no corresponde a hoy')
      ? `Esta clase es el ${String(days[item.dia] || item.dia).toLowerCase()} de ${shortTime(item.hora_inicio)} a ${shortTime(item.hora_fin)}. Hoy es ${todayName()}, así que todavía no se puede registrar la entrada.`
      : item.motivo;
  const showAllSchedules = ref(false);
  const todaySchedules = computed(() =>
    (clientData.value?.horarios || []).filter((item) => item.hoy),
  );
  const visibleSchedules = computed(() => {
    const all = clientData.value?.horarios || [];
    return showAllSchedules.value || !todaySchedules.value.length
      ? all
      : todaySchedules.value;
  });
  const hiddenSchedules = computed(
    () =>
      (clientData.value?.horarios.length || 0) - visibleSchedules.value.length,
  );
  const canToggleSchedules = computed(
    () =>
      todaySchedules.value.length > 0 &&
      (clientData.value?.horarios.length || 0) > todaySchedules.value.length,
  );
  return {
    blockedText,
    showAllSchedules,
    todaySchedules,
    visibleSchedules,
    hiddenSchedules,
    canToggleSchedules,
  };
};
