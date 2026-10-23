/** Operaciones de attendance: devuelve datos y mantiene HTTP en infraestructura. */
import { dataRequest } from './dataRequest.js';
export const createAttendanceRepository = (http, apiBase) => ({
  refreshAttendanceFromBackend: token => dataRequest(http, `${apiBase}/asistencia`, {}, token),
  checkinByDniServer: (payload, token) => dataRequest(http, `${apiBase}/asistencia/checkin-dni`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  checkinByIdServer: (payload, token) => dataRequest(http, `${apiBase}/asistencia/checkin`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  registerAttendanceEntry: (payload, token) => dataRequest(http, `${apiBase}/asistencia/entrada`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  registerAttendanceExit: (payload, token) => dataRequest(http, `${apiBase}/asistencia/salida`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token)
});
