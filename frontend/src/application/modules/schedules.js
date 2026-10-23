/** Estado y operaciones del módulo schedules. */
import { nowISO, normalizeBackendClientToMember, todayISO, getCurrentRegistrarId } from '../../domain/utils/gymRules.js';
import { backendRequest, apiGet } from '../services/backendGateway.js';

export const createSchedulesModule = (ctx) => {
  const upsertRutina = async (payload) => {
    const rutina = {
      id_rutina: payload.id_rutina || payload.id || null,
      servicio: payload.servicio || 'fitness',
      nombre_rutina: payload.nombre_rutina?.trim() || 'Sin nombre',
      zonas_musculares: payload.zonas_musculares || '',
      color: payload.color || 'Azul',
    };

    if (ctx.apiBase) {
      const response = await backendRequest(`${ctx.apiBase}/gym/rutinas`, {
        method: 'POST',
        headers: ctx._authHeaders(),
        body: JSON.stringify(rutina),
      });

      if (!response.ok) {
        throw new Error('Error al guardar rutina en backend');
      }

      const saved = await response.json();
      const normalized = {
        id_rutina: saved.id_rutina,
        servicio: saved.servicio || rutina.servicio,
        nombre_rutina: saved.nombre_rutina || rutina.nombre_rutina,
        zonas_musculares: saved.zonas_musculares || rutina.zonas_musculares,
        color: saved.color || rutina.color,
      };

      const index = ctx.routines.value.findIndex((entry) => Number(entry.id_rutina) === Number(normalized.id_rutina));
      if (index >= 0) {
        ctx.routines.value[index] = normalized;
      } else {
        ctx.routines.value.unshift(normalized);
      }

      ctx.persist();
      return normalized;
    }

    const nextId = rutina.id_rutina || (ctx.routines.value.length ? Math.max(...ctx.routines.value.map((entry) => Number(entry.id_rutina) || 0)) + 1 : 1);
    const normalized = { ...rutina, id_rutina: nextId };
    const index = ctx.routines.value.findIndex((entry) => Number(entry.id_rutina) === Number(normalized.id_rutina));
    if (index >= 0) {
      ctx.routines.value[index] = normalized;
    } else {
      ctx.routines.value.unshift(normalized);
    }

    ctx.persist();
    return normalized;
  };

  const upsertHorario = async (payload) => {
    const scheduleItem = {
      id_horario: payload.id_horario || payload.id || null,
      id_cliente: Number(payload.id_cliente),
      id_rutina: Number(payload.id_rutina),
      dia_semana: payload.dia_semana || 'Lunes',
      hora_inicio: payload.hora_inicio || '06:00',
      hora_fin: payload.hora_fin || '07:00',
      capacidad_maxima: Number(payload.capacidad_maxima ?? payload.capacity ?? 1),
    };

    if (ctx.apiBase) {
      const response = await backendRequest(`${ctx.apiBase}/gym/horarios`, {
        method: 'POST',
        headers: ctx._authHeaders(),
        body: JSON.stringify(scheduleItem),
      });

      if (!response.ok) {
        throw new Error('Error al guardar horario en backend');
      }

      const saved = await response.json();
      const normalized = {
        id_horario: saved.id_horario,
        id_cliente: saved.id_cliente,
        id_rutina: saved.id_rutina,
        dia_semana: saved.dia_semana || scheduleItem.dia_semana,
        hora_inicio: saved.hora_inicio || scheduleItem.hora_inicio,
        hora_fin: saved.hora_fin || scheduleItem.hora_fin,
        capacidad_maxima: Number(saved.capacidad_maxima ?? scheduleItem.capacidad_maxima ?? 1),
        cupos_usados: Number(saved.cupos_usados ?? 1),
      };

      const index = ctx.schedule.value.findIndex((entry) => Number(entry.id_horario) === Number(normalized.id_horario));
      if (index >= 0) {
        ctx.schedule.value[index] = normalized;
      } else {
        ctx.schedule.value.unshift(normalized);
      }

      const memberIndex = ctx.members.value.findIndex((member) => Number(member.id_cliente) === Number(normalized.id_cliente));
      if (memberIndex >= 0) {
        const member = ctx.members.value[memberIndex];
        ctx.members.value[memberIndex] = {
          ...member,
          schedules: [
            {
              id_horario: normalized.id_horario,
              id_rutina: normalized.id_rutina,
              dia_semana: normalized.dia_semana,
              hora_inicio: normalized.hora_inicio,
              hora_fin: normalized.hora_fin,
            },
            ...(member.schedules || []),
          ].slice(0, 20),
        };
      }

      ctx.persist();
      return normalized;
    }

    const nextId = scheduleItem.id_horario || (ctx.schedule.value.length ? Math.max(...ctx.schedule.value.map((entry) => Number(entry.id_horario) || 0)) + 1 : 1);
    const normalized = { ...scheduleItem, id_horario: nextId };
    const index = ctx.schedule.value.findIndex((entry) => Number(entry.id_horario) === Number(normalized.id_horario));
    if (index >= 0) {
      ctx.schedule.value[index] = normalized;
    } else {
      ctx.schedule.value.unshift(normalized);
    }

    ctx.persist();
    return normalized;
  };

  const memberSchedules = (memberId) => {
    const member = ctx.memberById(memberId);
    if (!member) return [];

    if (ctx.apiBase && ctx.schedule.value.length) {
      const backendId = Number(member.id_cliente || String(member.id || '').match(/^(?:cliente-|SGCLI)(\d+)$/i)?.[1] || 0);
      if (backendId) {
        return ctx.schedule.value.filter((entry) => Number(entry.id_cliente) === backendId);
      }
    }

    return member.schedules || [];
  };

  const assignMemberSchedule = (memberId, payload) => {
    const index = ctx.members.value.findIndex((entry) => entry.id === memberId);
    if (index < 0) {
      throw new Error('Miembro no encontrado');
    }

    const slot = {
      id: `schedule-${Date.now()}`,
      day: payload.day || 'Lunes',
      startTime: payload.startTime || '06:00',
      endTime: payload.endTime || '07:00',
      note: payload.note || '',
      assignedAt: nowISO(),
    };

    const member = ctx.members.value[index];
    ctx.members.value[index] = {
      ...member,
      schedules: [slot, ...(member.schedules || [])].slice(0, 20),
    };

    ctx.logMemberEvent(memberId, {
      action: 'Horario asignado',
      fields: ['schedules'],
      note: `${slot.day} ${slot.startTime}-${slot.endTime}`,
    });

    ctx.persist();
    return slot;
  };

  const refreshServiceSchedulesFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const response = await backendRequest(`${ctx.apiBase}/gym/horarios-servicio`, { headers: ctx._authHeaders() });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'Error al cargar horarios de servicio'));
    }

    ctx.serviceSchedules.value = await response.json();
    ctx.persist();
    return ctx.serviceSchedules.value;
  };

  const refreshRoutinesFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const response = await backendRequest(`${ctx.apiBase}/gym/rutinas`, { headers: ctx._authHeaders() });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'Error al cargar rutinas'));
    }

    const list = await response.json();
    ctx.routines.value = list.map((r) => ({
      id_rutina: r.id_rutina,
      servicio: r.servicio || 'fitness',
      nombre_rutina: r.nombre_rutina,
      zonas_musculares: r.zonas_musculares || '',
      color: r.color || 'Azul',
    }));
    ctx.persist();
    return ctx.routines.value;
  };

  const upsertServiceSchedule = async (payload) => {
    const body = {
      id_horario_servicio: payload.id_horario_servicio || null,
      servicio: payload.servicio,
      id_rutina: Number(payload.id_rutina || 0),
      hora_inicio: payload.hora_inicio || '06:00',
      hora_fin: payload.hora_fin || '07:00',
      codigo_dia: payload.codigo_dia || '',
      dia: payload.dia || (Array.isArray(payload.dias) ? payload.dias[0] : 'lunes'),
      cupos: Number(payload.cupos || 10),
      activo: payload.activo !== false,
    };
    if (!body.id_rutina) {
      throw new Error('Selecciona una rutina para el servicio');
    }

    if (ctx.apiBase) {
      const response = await backendRequest(`${ctx.apiBase}/gym/horarios-servicio`, {
        method: 'POST',
        headers: ctx._authHeaders(),
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error(await ctx.readBackendError(response, 'Error al guardar horario de servicio'));
      }

      const saved = await response.json();
      const index = ctx.serviceSchedules.value.findIndex((entry) => Number(entry.id_horario_servicio) === Number(saved.id_horario_servicio));
      if (index >= 0) {
        ctx.serviceSchedules.value[index] = saved;
      } else {
        ctx.serviceSchedules.value.push(saved);
      }
      ctx.persist();
      return saved;
    }

    if (!body.id_horario_servicio) {
      body.id_horario_servicio = Date.now();
      body.cupos_usados = 0;
    }
    const index = ctx.serviceSchedules.value.findIndex((entry) => Number(entry.id_horario_servicio) === Number(body.id_horario_servicio));
    if (index >= 0) {
      ctx.serviceSchedules.value[index] = body;
    } else {
      ctx.serviceSchedules.value.push(body);
    }
    ctx.persist();
    return body;
  };

  const deleteServiceSchedule = async (idHorarioServicio) => {
    if (ctx.apiBase) {
      const response = await backendRequest(`${ctx.apiBase}/gym/horarios-servicio/${idHorarioServicio}`, {
        method: 'DELETE',
        headers: ctx._authHeaders(),
      });
      if (!response.ok && response.status !== 204) {
        throw new Error(await ctx.readBackendError(response, 'No se pudo eliminar el horario'));
      }
    }

    ctx.serviceSchedules.value = ctx.serviceSchedules.value.filter((entry) => Number(entry.id_horario_servicio) !== Number(idHorarioServicio));
    ctx.persist();
  };

  const refreshScheduleClientsFromBackend = async () => {
    const isClient = (ctx.authStore.userRole || ctx.authStore.user?.role) === 'user';
    const data = await apiGet(isClient ? '/clientes/me' : '/clientes', ctx.authStore.token);
    ctx.members.value = (isClient ? [data] : data).map(normalizeBackendClientToMember);
    ctx.persist();
    return ctx.members.value;
  };

  const refreshEnrollmentsFromBackend = async (filters = {}) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const params = new URLSearchParams();
    if (filters.id_cliente) params.set('id_cliente', filters.id_cliente);
    if (filters.dni) params.set('dni', filters.dni);
    const query = params.toString() ? `?${params.toString()}` : '';
    const response = await backendRequest(`${ctx.apiBase}/gym/matriculas${query}`, { headers: ctx._authHeaders() });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'Error al cargar matriculas'));
    }
    /**
     * Gestiona esta acción de la vista.
     */
    const list = (await response.json()).map((entry) => ({
      ...entry,
      estado: String(entry.estado || 'ACTIVA').toUpperCase(),
    }));
    if (filters.id_cliente || filters.dni) {
      const incomingIds = new Set(list.map((entry) => Number(entry.id_matricula)));
      const filteredClientId = Number(filters.id_cliente || list[0]?.id_cliente || 0);
      ctx.enrollments.value = [
        ...list,
        ...ctx.enrollments.value.filter((entry) => {
          if (filteredClientId && Number(entry.id_cliente) === filteredClientId) return false;
          return !incomingIds.has(Number(entry.id_matricula));
        }),
      ];
    } else {
      ctx.enrollments.value = list;
    }
    ctx.persist();
    return list;
  };

  const fetchTrainerOverview = async ({ force = false } = {}) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const scope = `${ctx.authStore.token}|${ctx.authStore.userRole}`;
    try {
      ctx.activeSyncs += 1;
      ctx.isSyncing.value = true;
      await ctx.trainerOverviewCache.load(scope, 'overview', async () => {
        const response = await backendRequest(`${ctx.apiBase}/trainer/overview`, { headers: ctx._authHeaders() });
        if (!response.ok) {
          throw new Error(await ctx.readBackendError(response, 'Error al cargar supervision del trainer'));
        }
        const data = await response.json();
        if (scope !== `${ctx.authStore.token}|${ctx.authStore.userRole}`) throw new Error('La sesión ha cambiado.');
        ctx.trainerOverview.value = data;
      }, { force });
      return ctx.trainerOverview.value;
    } finally {
      ctx.activeSyncs -= 1;
      ctx.isSyncing.value = ctx.activeSyncs > 0;
    }
  };

  const upsertTrainerRoutine = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const body = {
      id_rutina: payload.id_rutina || null,
      servicio: payload.servicio || 'fitness',
      nombre_rutina: String(payload.nombre_rutina || '').trim(),
      zonas_musculares: String(payload.zonas_musculares || '').trim(),
      color: payload.color || 'Azul',
      ejercicios: Array.isArray(payload.ejercicios) ? payload.ejercicios : [],
    };
    const response = await backendRequest(`${ctx.apiBase}/trainer/rutinas`, {
      method: 'POST',
      headers: ctx._authHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'No se pudo guardar la rutina'));
    }
    const saved = await response.json();
    const normalized = {
      id_rutina: saved.id_rutina,
      servicio: saved.servicio || body.servicio,
      nombre_rutina: saved.nombre_rutina || body.nombre_rutina,
      zonas_musculares: saved.zonas_musculares || body.zonas_musculares,
      color: saved.color || body.color,
      ejercicios: saved.ejercicios || body.ejercicios,
    };
    const index = ctx.routines.value.findIndex((entry) => Number(entry.id_rutina) === Number(normalized.id_rutina));
    if (index >= 0) ctx.routines.value[index] = normalized; else ctx.routines.value.unshift(normalized);
    await fetchTrainerOverview({ force: true }).catch(() => { });
    ctx.persist();
    return normalized;
  };

  const assignTrainerRoutine = async (idMatricula, idRutina) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const response = await backendRequest(`${ctx.apiBase}/trainer/matriculas/${idMatricula}/rutina`, {
      method: 'POST',
      headers: ctx._authHeaders(),
      body: JSON.stringify({ id_rutina: Number(idRutina) }),
    });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'No se pudo asignar la rutina'));
    }
    const saved = await response.json();
    const index = ctx.enrollments.value.findIndex((entry) => Number(entry.id_matricula) === Number(saved.id_matricula));
    if (index >= 0) ctx.enrollments.value[index] = { ...ctx.enrollments.value[index], ...saved };
    else ctx.enrollments.value.unshift(saved);
    await fetchTrainerOverview({ force: true }).catch(() => { });
    ctx.persist();
    return saved;
  };

  const fetchTrainerClientRoutines = async (dni) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    try {
      ctx.activeSyncs += 1;
      ctx.isSyncing.value = true;
      const params = new URLSearchParams({ dni: String(dni || '').trim() });
      const response = await backendRequest(`${ctx.apiBase}/trainer/clientes-rutinas?${params.toString()}`, { headers: ctx._authHeaders() });
      if (!response.ok) {
        throw new Error(await ctx.readBackendError(response, 'No se pudo cargar el cliente'));
      }
      return await response.json();
    } finally {
      ctx.activeSyncs -= 1;
      ctx.isSyncing.value = ctx.activeSyncs > 0;
    }
  };

  const markTrainerRoutineProgress = async (idMatricula, payload = {}) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const response = await backendRequest(`${ctx.apiBase}/trainer/matriculas/${idMatricula}/progreso`, {
      method: 'POST',
      headers: ctx._authHeaders(),
      body: JSON.stringify({
        fecha: payload.fecha || todayISO(),
        estado: payload.estado || 'REALIZADO',
        observacion: payload.observacion || '',
        id_usuario: getCurrentRegistrarId(ctx.authStore) || undefined,
        ejercicios_detalle: Array.isArray(payload.ejercicios_detalle) ? payload.ejercicios_detalle : [],
      }),
    });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'No se pudo registrar el progreso'));
    }
    return response.json();
  };

  const enrollSchedule = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const response = await backendRequest(`${ctx.apiBase}/gym/matriculas`, {
      method: 'POST',
      headers: ctx._authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await ctx.readBackendError(response, 'No se pudo matricular en el horario'));
    }
    const savedResponse = await response.json();
    const saved = {
      ...savedResponse,
      estado: String(savedResponse.estado || 'ACTIVA').toUpperCase(),
    };
    const index = ctx.enrollments.value.findIndex((entry) => Number(entry.id_matricula) === Number(saved.id_matricula));
    if (index >= 0) {
      ctx.enrollments.value[index] = saved;
    } else {
      ctx.enrollments.value.unshift(saved);
    }
    await refreshServiceSchedulesFromBackend().catch(() => { });
    ctx.persist();
    return saved;
  };

  const deleteEnrollment = async (idMatricula) => {
    if (ctx.apiBase) {
      const response = await backendRequest(`${ctx.apiBase}/gym/matriculas/${idMatricula}`, {
        method: 'DELETE',
        headers: ctx._authHeaders(),
      });
      if (!response.ok && response.status !== 204) {
        throw new Error(await ctx.readBackendError(response, 'No se pudo cancelar la matricula'));
      }
    }
    ctx.enrollments.value = ctx.enrollments.value.map((entry) =>
      Number(entry.id_matricula) === Number(idMatricula) ? { ...entry, estado: 'CANCELADA' } : entry,
    );
    await refreshServiceSchedulesFromBackend().catch(() => { });
    ctx.persist();
  };

  return { upsertRutina, upsertHorario, memberSchedules, assignMemberSchedule, refreshServiceSchedulesFromBackend, refreshRoutinesFromBackend, upsertServiceSchedule, deleteServiceSchedule, refreshScheduleClientsFromBackend, refreshEnrollmentsFromBackend, fetchTrainerOverview, upsertTrainerRoutine, assignTrainerRoutine, fetchTrainerClientRoutines, markTrainerRoutineProgress, enrollSchedule, deleteEnrollment };
};
