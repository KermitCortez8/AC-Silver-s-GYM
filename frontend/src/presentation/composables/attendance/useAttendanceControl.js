import { ref, onMounted, onScopeDispose } from 'vue';
import { useAttendanceLookup } from './useAttendanceLookup.js';

/** Coordina lecturas y escrituras sin borrar la última ficha durante un refresco. */
export const useAttendanceControl = ({
  attendanceGet,
  attendanceEntry,
  attendanceExit,
  generalAttendanceEntry,
  token,
}) => {
  const summary = ref(null);
  const error = ref('');
  const feedback = ref('');
  const generalRequests = new Map();
  const refreshing = ref(false);
  const busy = ref('');
  let summaryNumber = 0;
  let timer;
  const savedKey = ref('');
  const now = ref(Date.now());

  const lookup = useAttendanceLookup({ attendanceGet, token, error, feedback });
  const { clientData, lookupClient, searching } = lookup;
  const loadSummary = async () => {
    const request = ++summaryNumber;
    refreshing.value = true;
    try {
      const data = await attendanceGet('/resumen', {}, token.value);
      if (request === summaryNumber) summary.value = data;
    } catch (err) {
      // Se conserva el último resumen cargado; solo se avisa del error.
      if (request === summaryNumber) throw err;
    } finally {
      if (request === summaryNumber) refreshing.value = false;
    }
  };
  const refresh = async () => {
    error.value = '';
    const results = await Promise.allSettled([
      loadSummary(),
      ...(clientData.value ? [lookupClient({ silent: true })] : []),
    ]);
    results.forEach((result) => {
      if (result.status === 'rejected')
        error.value = result.reason?.message || 'No se pudo actualizar.';
    });
  };
  let feedbackTimer;
  const mutate = async (key, action, message) => {
    if (busy.value) return;
    busy.value = key;
    error.value = '';
    feedback.value = '';
    savedKey.value = '';
    clearTimeout(feedbackTimer);
    try {
      await action();
      feedback.value = message;
      savedKey.value = key;
      feedbackTimer = setTimeout(() => {
        feedback.value = '';
        savedKey.value = '';
      }, 4000);
      await refresh();
    } catch (err) {
      const message =
        err?.message ||
        'No se pudo guardar. Revisa tu conexión e inténtalo de nuevo.';
      // Relee resumen y ficha (p. ej. tras un conflicto 409) y conserva el mensaje del error.
      await refresh();
      error.value = message;
    } finally {
      busy.value = '';
    }
  };
  const enter = (item) =>
    mutate(
      `entry-${item.id_matricula}`,
      () => attendanceEntry(item.id_matricula, token.value),
      'Entrada registrada correctamente.',
    );
  const enterGeneral = () => {
    const clientDni = clientData.value?.cliente.dni;
    if (!clientDni || !clientData.value?.general?.puede_entrar) return;
    if (!generalRequests.has(clientDni))
      generalRequests.set(clientDni, crypto.randomUUID());
    return mutate(
      'general-entry',
      async () => {
        await generalAttendanceEntry(
          clientDni,
          generalRequests.get(clientDni),
          token.value,
        );
        generalRequests.delete(clientDni);
      },
      'Entrada general registrada correctamente. ¡Buen entrenamiento!',
    );
  };
  const exitRecord = (record) =>
    mutate(
      `exit-${record.id_asistencia}`,
      async () => {
        await attendanceExit(record.id_asistencia, token.value);
        // Una visita cerrada permite iniciar un nuevo intento de entrada.
        if (record.tipo === 'general')
          generalRequests.delete(record.cliente_dni);
      },
      'Salida registrada correctamente.',
    );
  onMounted(() => {
    refresh();
    timer = setInterval(() => {
      now.value = Date.now();
      if (
        !document.hidden &&
        !busy.value &&
        !searching.value &&
        !refreshing.value
      )
        refresh();
    }, 60000);
  });
  onScopeDispose(() => {
    clearInterval(timer);
    clearTimeout(feedbackTimer);
    summaryNumber++;
  });
  return {
    ...lookup,
    summary,
    refreshing,
    busy,
    error,
    feedback,
    savedKey,
    now,
    refresh,
    enter,
    enterGeneral,
    exitRecord,
  };
};
