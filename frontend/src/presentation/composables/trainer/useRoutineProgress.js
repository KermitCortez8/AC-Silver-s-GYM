import { reactive, ref } from 'vue';
import { isEnrollmentActive } from '../../utils/trainerRoutines.js';

/** Borradores por matrícula/rutina; solo se limpian tras confirmar el guardado. */
export const useRoutineProgress = ({
  routines,
  saveProgress,
  reloadClient,
  notify,
}) => {
  const markingId = ref(0);
  const isSavingProgress = ref(false);
  const showExercisesModal = ref(false);
  const selectedMatriculaItem = ref(null);
  const trackerMap = reactive({});
  const observationsMap = reactive({});
  const getRoutineExercises = (idRutina) => {
    const routine = routines.value.find(
      (r) => Number(r.id_rutina) === Number(idRutina),
    );
    return Array.isArray(routine?.ejercicios) ? routine.ejercicios : [];
  };
  const getTracker = (idMatricula, idRutina) => {
    const key = `${idMatricula}_${idRutina}`;
    if (!trackerMap[key]) {
      trackerMap[key] = getRoutineExercises(idRutina).map((ex, i) => ({
        id_ejercicio: ex.id_ejercicio || i + 1,
        nombre_ejercicio: ex.nombre_ejercicio || `Ejercicio #${i + 1}`,
        series_meta: Number(ex.series || 3),
        series_completadas: 0,
        repeticiones_logradas: ex.repeticiones || '10-12',
        peso_sugerido_kg: ex.peso_sugerido_kg ?? null,
        peso_utilizado_kg: ex.peso_sugerido_kg ?? null,
        descanso_segundos: Number(ex.descanso_segundos || 60),
        notas: ex.notas || '',
        completado: false,
        observaciones: '',
      }));
    }
    return trackerMap[key];
  };
  const markDone = async (item) => {
    if (!item.id_rutina || !isEnrollmentActive(item) || markingId.value) return;
    markingId.value = item.id_matricula;
    try {
      await saveProgress(item.id_matricula, {
        estado: 'REALIZADO',
        observacion: 'Rutina marcada como realizada por el entrenador.',
        ejercicios_detalle: [],
      });
      await reloadClient();
      notify(
        'Rutina marcada como realizada.',
        'success',
        'Rutina completada correctamente.',
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo registrar la rutina como realizada.';
      notify(message, 'error');
    } finally {
      markingId.value = 0;
    }
  };
  const openExercisesModal = (item) => {
    selectedMatriculaItem.value = item;
    getTracker(item.id_matricula, item.id_rutina);
    showExercisesModal.value = true;
  };
  const submitSaveProgress = async () => {
    const item = selectedMatriculaItem.value;
    if (!item || isSavingProgress.value) return;
    isSavingProgress.value = true;
    try {
      const trackerExs = getTracker(item.id_matricula, item.id_rutina);
      const ejercicios_detalle = trackerExs.map((ex) => ({
        id_ejercicio: ex.id_ejercicio,
        nombre_ejercicio: ex.nombre_ejercicio,
        completado: Boolean(ex.completado),
        series_completadas: Number(ex.series_completadas || 0),
        repeticiones_logradas: String(ex.repeticiones_logradas || ''),
        peso_utilizado_kg:
          ex.peso_utilizado_kg !== null && ex.peso_utilizado_kg !== ''
            ? Number(ex.peso_utilizado_kg)
            : null,
        observaciones: String(ex.observaciones || ''),
      }));
      const observacion =
        observationsMap[item.id_matricula] ||
        'Sesión de entrenamiento realizada';
      await saveProgress(item.id_matricula, {
        estado: 'REALIZADO',
        observacion,
        ejercicios_detalle,
      });
      await reloadClient();
      delete trackerMap[`${item.id_matricula}_${item.id_rutina}`];
      delete observationsMap[item.id_matricula];
      showExercisesModal.value = false;
      notify('Progreso de rutina registrado en el sistema.');
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo registrar el progreso.';
      notify(message, 'error');
    } finally {
      isSavingProgress.value = false;
    }
  };
  return {
    markingId,
    isSavingProgress,
    showExercisesModal,
    selectedMatriculaItem,
    observationsMap,
    getTracker,
    markDone,
    openExercisesModal,
    submitSaveProgress,
  };
};
