import { computed, reactive, ref } from 'vue';
import {
  dayLabel,
  serviceLabel,
  isEnrollmentActive,
} from '../../utils/trainerRoutines.js';

export const useRoutineAssignments = ({
  clientData,
  routines,
  assign,
  reloadClient,
  notify,
  setFeedback,
}) => {
  const assigningId = ref(0);
  const isUnassigning = ref(false);
  const selection = reactive({});
  const showAssignModal = ref(false);
  const showConfirmModal = ref(false);
  const assignForm = reactive({ id_matricula: null, id_rutina: 0 });
  const hasActiveMembership = computed(() =>
    (clientData.value?.matriculas || []).some(isEnrollmentActive),
  );
  const membershipLabel = computed(() =>
    hasActiveMembership.value ? 'Vigente' : 'Sin matrícula activa',
  );
  const routinesForService = (service) =>
    routines.value.filter(
      (routine) =>
        String(routine.servicio || '').toLowerCase() ===
        String(service || '').toLowerCase(),
    );
  const hasCompatibleRoutines = (item) =>
    routinesForService(item.servicio).length > 0;
  const canAssign = (item) =>
    isEnrollmentActive(item) && hasCompatibleRoutines(item);
  const selectedRoutine = (item) =>
    selection[item.id_matricula] ?? (item.id_rutina || 0);
  const hasChange = (item) => {
    const chosen = Number(selection[item.id_matricula] || 0);
    return chosen > 0 && chosen !== Number(item.id_rutina || 0);
  };
  const selectedAssignMatricula = computed(() =>
    (clientData.value?.matriculas || []).find(
      (m) => Number(m.id_matricula) === Number(assignForm.id_matricula),
    ),
  );
  const availableRoutinesForSelectedMatricula = computed(() =>
    selectedAssignMatricula.value
      ? routinesForService(selectedAssignMatricula.value.servicio)
      : [],
  );
  const canSubmitAssign = computed(() => {
    const mat = selectedAssignMatricula.value;
    return Boolean(
      mat &&
      isEnrollmentActive(mat) &&
      availableRoutinesForSelectedMatricula.value.some(
        (r) => Number(r.id_rutina) === Number(assignForm.id_rutina),
      ),
    );
  });
  const openAssignModal = () => {
    const first = (clientData.value?.matriculas || []).find(isEnrollmentActive);
    if (!first) {
      setFeedback(
        'El cliente debe tener una matrícula activa para asignar rutinas.',
        'error',
      );
      return;
    }
    assignForm.id_matricula = first.id_matricula;
    assignForm.id_rutina = 0;
    showAssignModal.value = true;
  };
  const unassignItem = ref(null);
  // La asignación directa y el diálogo comparten confirmación, recarga y errores.
  const saveAssignment = async (
    item,
    idRutina,
    message,
    toastMessage = message,
  ) => {
    if (assigningId.value) return;
    assigningId.value = item.id_matricula;
    try {
      await assign(item.id_matricula, idRutina);
      delete selection[item.id_matricula];
      await reloadClient();
      notify(message, 'success', toastMessage);
      return true;
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : 'No se pudo asignar la rutina.',
        'error',
      );
      await reloadClient().catch(() => {});
      return false;
    } finally {
      assigningId.value = 0;
    }
  };
  const assignRoutine = (item) => {
    const idRutina = Number(selection[item.id_matricula] || 0);
    if (!idRutina || assigningId.value) return;
    if (!isEnrollmentActive(item)) {
      setFeedback(
        'Solo se puede asignar una rutina a una matrícula activa.',
        'error',
      );
      return;
    }
    const routine = routinesForService(item.servicio).find(
      (r) => Number(r.id_rutina) === idRutina,
    );
    if (!routine) {
      setFeedback(
        `Esa rutina no corresponde al servicio ${serviceLabel(item.servicio)}.`,
        'error',
      );
      return;
    }
    return saveAssignment(
      item,
      idRutina,
      `Rutina «${routine.nombre_rutina}» asignada a ${serviceLabel(item.servicio)} (${dayLabel(item.dia)} ${item.hora_inicio} - ${item.hora_fin}).`,
      'Rutina asignada exitosamente.',
    );
  };
  const submitAssignRoutine = async () => {
    if (!canSubmitAssign.value) return;
    const saved = await saveAssignment(
      selectedAssignMatricula.value,
      Number(assignForm.id_rutina),
      'Rutina personalizada asignada exitosamente.',
    );
    if (saved) showAssignModal.value = false;
  };
  const confirmUnassign = (item) => {
    unassignItem.value = item;
    showConfirmModal.value = true;
  };
  const submitUnassign = async () => {
    const item = unassignItem.value;
    if (!item || isUnassigning.value) return;
    isUnassigning.value = true;
    try {
      await assign(item.id_matricula, 0);
      delete selection[item.id_matricula];
      await reloadClient();
      showConfirmModal.value = false;
      notify('Rutina desvinculada del servicio.');
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : 'No se pudo desvincular la rutina.',
        'error',
      );
    } finally {
      isUnassigning.value = false;
    }
  };
  const reset = () => {
    showAssignModal.value = false;
    showConfirmModal.value = false;
    Object.keys(selection).forEach((key) => {
      delete selection[key];
    });
  };
  return {
    assigningId,
    isUnassigning,
    selection,
    showAssignModal,
    showConfirmModal,
    unassignItem,
    assignForm,
    hasActiveMembership,
    membershipLabel,
    routinesForService,
    hasCompatibleRoutines,
    canAssign,
    selectedRoutine,
    hasChange,
    availableRoutinesForSelectedMatricula,
    canSubmitAssign,
    openAssignModal,
    assignRoutine,
    submitAssignRoutine,
    confirmUnassign,
    submitUnassign,
    reset,
  };
};
