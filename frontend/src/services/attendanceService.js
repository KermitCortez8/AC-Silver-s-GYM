import { apiGet, apiPost, apiPut } from './apiClient';

export const attendanceGet = (path, params, token) => {
  const query = new URLSearchParams(
    Object.entries(params || {}).filter(
      ([, value]) => value !== '' && value != null,
    ),
  );
  return apiGet(`/asistencia${path}${query.size ? `?${query}` : ''}`, token);
};
export const attendanceEntry = (id, token) =>
  apiPost('/asistencia/entrada', { id_matricula: id }, token);
export const attendanceExit = (id, token) =>
  apiPost('/asistencia/salida', { id_asistencia: id }, token);
export const attendanceCorrect = (id, payload, token) =>
  apiPut(`/asistencia/${id}`, payload, token);
export const attendanceAnnul = (id, payload, token) =>
  apiPost(`/asistencia/${id}/anular`, payload, token);
