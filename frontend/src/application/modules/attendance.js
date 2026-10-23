import { bindSessionRepository } from '../services/sessionBoundary.js';
/** Estado y operaciones del módulo attendance. */
import { normalizeAttendanceRecord, todayISO, dateFromISO, getClientIdForBackend, getCurrentRegistrarId, nowTime, buildAttendanceRecord, findMemberForAttendance, isPassExpired, getPassPayload, PASS_EXPIRY_MINUTES, nowISO, generatePassCode, parsePassInput, normalizeBackendAttendanceRecord } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';

export const createAttendanceModule = (ctx, repository) => {
  const remote = bindSessionRepository(repository, () => ctx.authStore.token);
  const mergeAttendanceRecord = (record) => {
    const normalized = normalizeAttendanceRecord(record);
    const index = ctx.attendance.value.findIndex((entry) => {
      if (normalized.id_asistencia && entry.id_asistencia) {
        return Number(entry.id_asistencia) === Number(normalized.id_asistencia);
      }

      return entry.id === normalized.id;
    });

    if (index >= 0) {
      ctx.attendance.value[index] = normalized;
    } else {
      ctx.attendance.value.unshift(normalized);
    }

    return normalized;
  };

  const recentAttendance = computed(() =>
    [...ctx.attendance.value].sort((a, b) => `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`)).slice(0, 10),
  );

  const attendanceAnalytics = computed(() => {
    const today = todayISO();
    const weekStart = dateFromISO(today);
    weekStart.setDate(weekStart.getDate() - 6);
    const monthStart = dateFromISO(today);
    monthStart.setDate(1);

    const countsByDate = ctx.attendance.value.reduce((accumulator, entry) => {
      accumulator[entry.date] = (accumulator[entry.date] || 0) + 1;
      return accumulator;
    }, {});

    /**
     * Gestiona esta acción de la vista.
     */
    const totalInPeriod = (startDate) =>
      ctx.attendance.value.filter((entry) => dateFromISO(entry.date).getTime() >= startDate.getTime()).length;

    return {
      today: countsByDate[today] || 0,
      week: totalInPeriod(weekStart),
      month: totalInPeriod(monthStart),
      countsByDate,
    };
  });

  const attendanceByMemberRange = (memberId, fromDate = '', toDate = '') =>
    ctx.attendance.value.filter((entry) => {
      const matchesMember = entry.memberId === memberId;
      const afterStart = !fromDate || entry.date >= fromDate;
      const beforeEnd = !toDate || entry.date <= toDate;
      return matchesMember && afterStart && beforeEnd;
    });

  const recordAttendanceByCode = (internalCode, service = 'fitness', options = {}) => {
    const member = ctx.memberByInternalCode(internalCode);
    if (!member) {
      throw new Error('Código no encontrado');
    }

    if (ctx.apiBase) {
      const backendMemberId = getClientIdForBackend(member);
      const registrarId = getCurrentRegistrarId(ctx.authStore);
      if (backendMemberId) {
        return checkinByIdServer({
          id_cliente: backendMemberId,
          id_usuario: registrarId,
          servicio: service || 'fitness',
          fecha: options.fecha || options.date || todayISO(),
          hora: options.hora || options.time || nowTime(),
        }).then((res) => {
          const record = buildAttendanceRecord(member, res, {
            service: service || 'fitness',
          });
          return mergeAttendanceRecord(record);
        });
      }

      if (member.dni) {
        return checkinByDniServer({
          dni: member.dni,
          id_usuario: registrarId,
          servicio: service || 'fitness',
          fecha: options.fecha || options.date || todayISO(),
          hora: options.hora || options.time || nowTime(),
        }).then((res) => {
          const record = buildAttendanceRecord(member, res, {
            service: service || 'fitness',
          });
          return mergeAttendanceRecord(record);
        });
      }
    }

    if (!ctx.isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía vigente');
    }

    const record = buildAttendanceRecord(member, {}, {
      local: true,
      service: service || 'fitness',
      time: options.hora || options.time || nowTime(),
      date: options.fecha || options.date || todayISO(),
    });

    return mergeAttendanceRecord(record);
  };

  const recordAttendanceByDni = (dni, service = 'fitness', options = {}) => {
    const normalizedDni = String(dni || '').trim();
    if (!normalizedDni) {
      throw new Error('Ingresa un DNI válido');
    }

    const localMember = ctx.members.value.find((member) => String(member.dni || '').trim() === normalizedDni) || null;

    if (ctx.apiBase) {
      return checkinByDniServer({
        dni: normalizedDni,
        id_usuario: getCurrentRegistrarId(ctx.authStore),
        servicio: service || 'fitness',
        fecha: options.fecha || options.date || todayISO(),
        hora: options.hora || options.time || nowTime(),
      }).then((res) => {
        const member = localMember || findMemberForAttendance(res, ctx.members.value) || {
          id: String(res.id_cliente || normalizedDni),
          id_cliente: res.id_cliente_num || null,
          internalCode: String(res.id_cliente || normalizedDni),
          name: String(res.id_cliente || normalizedDni),
        };

        const record = buildAttendanceRecord(member, res, {
          service: service || 'fitness',
        });
        return mergeAttendanceRecord(record);
      });
    }

    if (!localMember) {
      throw new Error('DNI no registrado');
    }

    return recordAttendance(localMember.id, service, options);
  };

  const userAttendance = (email) => {
    const normalizedEmail = ctx.normalizeLookupEmail(email);
    const member = ctx.members.value.find((entry) => ctx.normalizeLookupEmail(entry.email || entry.correo) === normalizedEmail);
    if (!member) return [];

    return ctx.attendance.value
      .filter((entry) => {
        const entryCodes = [entry.memberId, entry.memberCode, entry.id_cliente].map((value) => String(value || '').trim().toUpperCase());
        const memberCodes = [member.id, member.internalCode, member.memberCode, member.id_cliente].map((value) => String(value || '').trim().toUpperCase());
        return entryCodes.some((code) => memberCodes.includes(code));
      })
      .slice(0, 10);
  };

  const activeAttendancePass = (memberId) => {
    const pass =
      [...ctx.attendancePasses.value]
        .filter((entry) => entry.memberId === memberId && entry.status === 'active' && !isPassExpired(entry))
        .sort((a, b) => new Date(b.issuedAt) - new Date(a.issuedAt))[0] || null;

    if (!pass) {
      return null;
    }

    return {
      ...pass,
      qrPayload: getPassPayload(pass),
    };
  };

  const createAttendancePass = (memberId, expiresInMinutes = PASS_EXPIRY_MINUTES) => {
    const member = ctx.memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    if (!ctx.isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía vigente');
    }

    const issuedAt = nowISO();
    const expiresAt = new Date(Date.now() + expiresInMinutes * 60 * 1000).toISOString();
    const pass = {
      id: `pass-${Date.now()}`,
      memberId,
      memberName: member.name,
      code: generatePassCode(),
      issuedAt,
      expiresAt,
      status: 'active',
      redeemedAt: null,
      redeemedAttendanceId: null,
    };

    ctx.attendancePasses.value = ctx.attendancePasses.value.map((entry) => {
      if (entry.memberId === memberId && entry.status === 'active' && !isPassExpired(entry)) {
        return { ...entry, status: 'expired' };
      }

      return entry;
    });

    ctx.attendancePasses.value = [pass, ...ctx.attendancePasses.value];
    return {
      ...pass,
      qrPayload: getPassPayload(pass),
    };
  };

  const redeemAttendancePass = async (input, type = 'fitness', note = '') => {
    const code = parsePassInput(input);
    if (!code) {
      throw new Error('Ingresa un código o QR válido');
    }

    const pass = ctx.attendancePasses.value.find((entry) => entry.code === code);
    if (!pass) {
      throw new Error('Código no encontrado');
    }

    if (pass.status !== 'active') {
      throw new Error('El código ya fue utilizado');
    }

    if (isPassExpired(pass)) {
      pass.status = 'expired';
      throw new Error('El código expiró');
    }

    const record = await recordAttendance(pass.memberId, type, { note });
    pass.status = 'redeemed';
    pass.redeemedAt = nowISO();
    pass.redeemedAttendanceId = record.id;

    return {
      record,
      pass: {
        ...pass,
        qrPayload: getPassPayload(pass),
      },
    };
  };

  const recordAttendance = (memberId, service = 'fitness', options = {}) => {
    const member = ctx.members.value.find((entry) => entry.id === memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    // Si hay backend, primero intentar con id_cliente y luego con DNI.
    if (ctx.apiBase) {
      const backendMemberId = getClientIdForBackend(member);
      const registrarId = getCurrentRegistrarId(ctx.authStore);
      if (backendMemberId) {
        return checkinByIdServer({
          id_cliente: backendMemberId,
          id_usuario: registrarId,
          servicio: service || 'fitness',
          fecha: options.fecha || options.date || todayISO(),
          hora: options.hora || options.time || nowTime(),
        }).then((res) => {
          const record = buildAttendanceRecord(member, res, {
            service: service || 'fitness',
          });
          return mergeAttendanceRecord(record);
        });
      }

      if (member.dni) {
        return checkinByDniServer({
          dni: member.dni,
          id_usuario: registrarId,
          servicio: service || 'fitness',
          fecha: options.fecha || options.date || todayISO(),
          hora: options.hora || options.time || nowTime(),
        }).then((res) => {
          const record = buildAttendanceRecord(member, res, {
            service: service || 'fitness',
          });
          return mergeAttendanceRecord(record);
        });
      }
    }

    if (!ctx.isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía vigente');
    }

    const record = buildAttendanceRecord(member, {}, {
      local: true,
      service: service || 'fitness',
      time: options.hora || options.time || nowTime(),
      date: options.fecha || options.date || todayISO(),
    });

    return mergeAttendanceRecord(record);
  };

  const pruneExpiredAttendancePasses = () => {
    ctx.attendancePasses.value = ctx.attendancePasses.value.map((pass) => {
      if (pass.status === 'active' && isPassExpired(pass)) {
        return { ...pass, status: 'expired' };
      }

      return pass;
    });
  };

  const refreshAttendanceFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const list = await remote.refreshAttendanceFromBackend();
    ctx.attendance.value = list.map((entry) => normalizeBackendAttendanceRecord(entry, ctx.members.value));
    return ctx.attendance.value;
  };

  const checkinByDniServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return await remote.checkinByDniServer(payload);
  };

  const checkinByIdServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return await remote.checkinByIdServer(payload);
  };

  const registerAttendanceEntry = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.registerAttendanceEntry(payload);
    return mergeAttendanceRecord(normalizeBackendAttendanceRecord(saved, ctx.members.value));
  };

  const registerAttendanceExit = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.registerAttendanceExit(payload);
    return mergeAttendanceRecord(normalizeBackendAttendanceRecord(saved, ctx.members.value));
  };

  const updateAttendanceRecord = async (idAsistencia, payload) => {
    const current = ctx.attendance.value.find((entry) => Number(entry.id_asistencia) === Number(idAsistencia) || entry.id === idAsistencia);
    if (!current) {
      throw new Error('Asistencia no encontrada');
    }

    const body = {
      id_cliente: payload.id_cliente || payload.memberCode || current.id_cliente_num || current.id_cliente || current.memberCode,
      fecha: payload.fecha || payload.date || current.date,
      hora: payload.hora || payload.time || current.time,
      servicio: payload.servicio || payload.service || current.service || 'fitness',
      id_usuario: payload.id_usuario || getCurrentRegistrarId(ctx.authStore) || undefined,
    };

    if (ctx.apiBase && current.id_asistencia) {
      // El backend ahora exige versión y motivo (y rechaza campos extra), así que el
      // PUT con este formato antiguo siempre respondía 422. La corrección se hace en
      // Asistencias > Historial > Corregir (AttendanceCorrectionDialog).
      throw new Error('Las correcciones de asistencia se hacen desde Asistencias › Historial › Corregir.');
    }

    const updated = normalizeAttendanceRecord({
      ...current,
      date: body.fecha,
      time: body.hora,
      service: body.servicio,
      memberCode: body.id_cliente,
    });
    return mergeAttendanceRecord(updated);
  };

  const deleteAttendanceRecord = async (idAsistencia) => {
    const current = ctx.attendance.value.find((entry) => Number(entry.id_asistencia) === Number(idAsistencia) || entry.id === idAsistencia);
    if (!current) {
      throw new Error('Asistencia no encontrada');
    }

    if (ctx.apiBase && current.id_asistencia) {
      // El backend ya no elimina: anula con versión y motivo (queda auditado).
      // Se hace en Asistencias > Historial > Anular.
      throw new Error('Las anulaciones de asistencia se hacen desde Asistencias › Historial › Anular.');
    }

    ctx.attendance.value = ctx.attendance.value.filter((entry) => {
      if (current.id_asistencia && entry.id_asistencia) {
        return Number(entry.id_asistencia) !== Number(current.id_asistencia);
      }

      return entry.id !== current.id;
    });
  };

  return { mergeAttendanceRecord, recentAttendance, attendanceAnalytics, attendanceByMemberRange, recordAttendanceByCode, recordAttendanceByDni, userAttendance, activeAttendancePass, createAttendancePass, redeemAttendancePass, recordAttendance, pruneExpiredAttendancePasses, refreshAttendanceFromBackend, checkinByDniServer, checkinByIdServer, registerAttendanceEntry, registerAttendanceExit, updateAttendanceRecord, deleteAttendanceRecord };
};
