import { ref, onScopeDispose } from 'vue';
import { requireRecord } from '../../../application/services/responseValidation.js';

/** Búsqueda por DNI; descarta respuestas reemplazadas o recibidas tras desmontar. */
export const useAttendanceLookup = ({
  attendanceGet,
  token,
  error,
  feedback,
}) => {
  const dni = ref('');
  const clientData = ref(null);
  const lookupError = ref('');
  const searching = ref(false);
  let searchNumber = 0;
  const clearClient = () => {
    searchNumber++;
    searching.value = false;
    clientData.value = null;
    lookupError.value = '';
    feedback.value = '';
  };
  const onDniInput = () => {
    dni.value = dni.value.replace(/\D/g, '').slice(0, 8);
    clearClient();
    if (dni.value.length === 8) lookupClient();
  };
  const backToSearch = () => {
    clearClient();
    dni.value = '';
  };
  const lookupClient = async ({ silent = false } = {}) => {
    const query = silent ? clientData.value?.cliente?.dni : dni.value;
    if (!/^\d{8}$/.test(query || '')) {
      if (!silent) lookupError.value = 'Ingresa un DNI de 8 dígitos.';
      return;
    }
    const request = silent ? searchNumber : ++searchNumber;
    if (!silent) {
      searching.value = true;
      lookupError.value = '';
      clientData.value = null;
    }
    try {
      const data = requireRecord(await attendanceGet('/cliente', { dni: query }, token.value));
      requireRecord(data.cliente);
      if (request === searchNumber) {
        clientData.value = data;
      }
    } catch (err) {
      if (request === searchNumber) {
        const text = err?.message || 'No se pudo consultar al cliente.';
        if (silent) error.value = `No se pudo actualizar la ficha. ${text}`;
        else lookupError.value = text;
      }
    } finally {
      if (request === searchNumber && !silent) searching.value = false;
    }
  };
  onScopeDispose(() => {
    searchNumber++;
  });
  return {
    dni,
    clientData,
    lookupError,
    searching,
    clearClient,
    onDniInput,
    backToSearch,
    lookupClient,
  };
};
