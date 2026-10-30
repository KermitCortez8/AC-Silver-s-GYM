import { ref, onScopeDispose, watch } from 'vue';
import { requireRecord, requireList } from '../../../application/services/responseValidation.js';

/** Conserva la selección y descarta respuestas de otro horario o sesión. */
export const useScheduleRoster = ({ attendanceGet, token }) => {
  const scheduleData = ref(null);
  const selectedSchedule = ref(null);
  const selectedSession = ref('');
  const roster = ref(null);
  const schedulesLoading = ref(false);
  const rosterLoading = ref(false);
  const schedulesError = ref('');
  const rosterError = ref('');
  let catalogRequest = 0;
  let rosterRequest = 0;
  const loadSchedules = async () => {
    const id = ++catalogRequest;
    schedulesLoading.value = true;
    schedulesError.value = '';
    try {
      const data = requireRecord(await attendanceGet('/horarios', {}, token.value));
      requireList(data.horarios);
      if (id === catalogRequest) {
        scheduleData.value = data;
        if (selectedSchedule.value && !data.horarios.some((s) => s.id_horario_servicio === selectedSchedule.value)) {
          selectedSchedule.value = null;
          selectedSession.value = '';
          roster.value = null;
          rosterRequest++;
          rosterLoading.value = false;
        }
      }
    } catch (err) {
      if (id === catalogRequest) schedulesError.value = err.message || 'No se pudieron cargar los horarios.';
    } finally {
      if (id === catalogRequest) schedulesLoading.value = false;
    }
  };
  const loadRoster = async () => {
    if (!selectedSchedule.value) return;
    const id = ++rosterRequest;
    const selected = selectedSchedule.value;
    rosterLoading.value = true;
    rosterError.value = '';
    try {
      const data = requireRecord(await attendanceGet(`/horarios/${selected}/clientes`,
        selectedSession.value ? { fecha: selectedSession.value } : {}, token.value));
      requireList(data.clientes);
      if (selectedSession.value && data.fecha !== selectedSession.value) {
        throw new Error('La respuesta no corresponde a la fecha seleccionada. Actualiza la asistencia.');
      }
      if (id === rosterRequest) roster.value = data;
    } catch (err) {
      if (id === rosterRequest) {
        roster.value = null;
        rosterError.value = err.message || 'No se pudieron cargar los matriculados.';
      }
    } finally {
      if (id === rosterRequest) rosterLoading.value = false;
    }
  };
  const selectSchedule = (id, fecha = '') => {
    selectedSchedule.value = id;
    selectedSession.value = fecha;
    roster.value = null;
    if (!id) {
      rosterRequest++;
      rosterLoading.value = false;
      rosterError.value = '';
      return;
    }
    return loadRoster();
  };
  const clear = () => {
    catalogRequest++;
    rosterRequest++;
    scheduleData.value = null;
    roster.value = null;
    selectedSchedule.value = null;
    selectedSession.value = '';
    schedulesLoading.value = false;
    rosterLoading.value = false;
    schedulesError.value = '';
    rosterError.value = '';
  };
  watch(token, clear);
  onScopeDispose(clear);
  return { scheduleData, selectedSchedule, selectedSession, roster, schedulesLoading, rosterLoading,
    schedulesError, rosterError, loadSchedules, loadRoster, selectSchedule };
};
