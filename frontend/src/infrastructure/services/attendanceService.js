import { apiGet, apiPost, apiPut } from "./apiClient";

export const createAttendanceService = (http = { apiGet, apiPost, apiPut }) => {
  const { apiGet, apiPost, apiPut } = http;
  const attendanceGet = (path, params, token) => {
    const query = new URLSearchParams(
      Object.entries(params || {}).filter(
        ([, value]) => value !== "" && value != null,
      ),
    );
    return apiGet(`/asistencia${path}${query.size ? `?${query}` : ""}`, token);
  };
  const attendanceEntry = (id, token) =>
    apiPost("/asistencia/entrada", { id_matricula: id }, token);
  const generalAttendanceEntry = (dni, requestId, token) =>
    apiPost(
      "/asistencia/general/entrada",
      { dni, request_id: requestId },
      token,
    );
  const attendanceExit = (id, token) =>
    apiPost("/asistencia/salida", { id_asistencia: id }, token);
  const attendanceCorrect = (id, payload, token) =>
    apiPut(`/asistencia/${id}`, payload, token);
  const attendanceAnnul = (id, payload, token) =>
    apiPost(`/asistencia/${id}/anular`, payload, token);

  return {
    attendanceGet,
    attendanceEntry,
    generalAttendanceEntry,
    attendanceExit,
    attendanceCorrect,
    attendanceAnnul,
  };
};

export const {
  attendanceGet,
  attendanceEntry,
  generalAttendanceEntry,
  attendanceExit,
  attendanceCorrect,
  attendanceAnnul,
} = createAttendanceService();
