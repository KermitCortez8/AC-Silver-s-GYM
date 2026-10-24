/** Operaciones de schedules: devuelve datos y mantiene HTTP en infraestructura. */
import { dataRequest } from './dataRequest.js';
export const createSchedulesRepository = (http, apiBase) => ({
  loadClients: (isClient, token) => dataRequest(http, `${apiBase}${isClient ? '/clientes/me' : '/clientes'}`, {}, token),
  upsertRutina: (rutina, token) => dataRequest(http, `${apiBase}/gym/rutinas`, {
    method: 'POST',
    body: JSON.stringify(rutina)
  }, token),
  upsertHorario: (scheduleItem, token) => dataRequest(http, `${apiBase}/gym/horarios`, {
    method: 'POST',
    body: JSON.stringify(scheduleItem)
  }, token),
  refreshServiceSchedulesFromBackend: token => dataRequest(http, `${apiBase}/gym/horarios-servicio`, {}, token),
  refreshRoutinesFromBackend: token => dataRequest(http, `${apiBase}/gym/rutinas`, {}, token),
  upsertServiceSchedule: (body, token) => dataRequest(http, `${apiBase}/gym/horarios-servicio`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  deleteServiceSchedule: (idHorarioServicio, token) => dataRequest(http, `${apiBase}/gym/horarios-servicio/${idHorarioServicio}`, {
    method: 'DELETE'
  }, token),
  refreshEnrollmentsFromBackend: (filters, token) => {
    const params = new URLSearchParams();
    if (filters.id_cliente) params.set('id_cliente', filters.id_cliente);
    if (filters.dni) params.set('dni', filters.dni);
    const query = params.toString();
    return dataRequest(http, `${apiBase}/gym/matriculas${query ? `?${query}` : ''}`, {}, token);
  },
  fetchTrainerOverview: token => dataRequest(http, `${apiBase}/trainer/overview`, {}, token),
  upsertTrainerRoutine: (body, token) => dataRequest(http, `${apiBase}/trainer/rutinas`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  assignTrainerRoutine: (idMatricula, idRutina, token) => dataRequest(http, `${apiBase}/trainer/matriculas/${idMatricula}/rutina`, {
    method: 'POST',
    body: JSON.stringify({
      id_rutina: Number(idRutina)
    })
  }, token),
  fetchTrainerClientRoutines: (dni, token) => dataRequest(http, `${apiBase}/trainer/clientes-rutinas?${new URLSearchParams({
    dni
  })}`, {}, token),
  markTrainerRoutineProgress: (idMatricula, body, token) => dataRequest(http, `${apiBase}/trainer/matriculas/${idMatricula}/progreso`, {
    method: 'POST',
    body: JSON.stringify(body)
  }, token),
  enrollSchedule: (payload, token) => dataRequest(http, `${apiBase}/gym/matriculas`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }, token),
  deleteEnrollment: (idMatricula, token) => dataRequest(http, `${apiBase}/gym/matriculas/${idMatricula}`, {
    method: 'DELETE'
  }, token)
});
