import { requireRecord } from '../services/responseValidation.js';
import { refreshAfterMutation } from '../services/refreshAfterMutation.js';
import { bindSessionRepository } from '../services/sessionBoundary.js';
import { addDays } from '../../domain/utils/dates.js';
/** Estado y operaciones del módulo clients. */
import { nowISO, todayISO, planDurationDays, normalizeBackendClientToMember } from '../../domain/utils/gymRules.js';
import { normalizeMembershipStatus } from '../../domain/utils/clientDirectory.js';

export const createClientsModule = (ctx, repository) => {
  const remote = bindSessionRepository(repository, () => ctx.authStore.token, ctx.pinia);
  const memberByInternalCode = (code) => {
    const normalizedCode = String(code || '').trim().toUpperCase();
    if (!normalizedCode) {
      return null;
    }

    return (
      ctx.members.value.find((member) => {
        const identifiers = [member.id_cliente, member.internalCode, member.id, member.memberCode]
          .map((value) => String(value || '').trim().toUpperCase())
          .filter(Boolean);
        return identifiers.includes(normalizedCode);
      }) || null
    );
  };

  const searchMembers = (query) => {
    const normalizedQuery = query?.trim().toLowerCase() || '';
    if (!normalizedQuery) {
      return ctx.members.value;
    }

    return ctx.members.value.filter((member) =>
      [member.dni, member.internalCode, member.name, member.email, member.phone, member.plan, member.status]
        .join(' ')
        .toLowerCase()
        .includes(normalizedQuery),
    );
  };

  const logMemberEvent = (memberId, event) => {
    const index = ctx.members.value.findIndex((entry) => entry.id === memberId);
    if (index < 0) return null;

    const entry = {
      id: event.id || `history-${Date.now()}`,
      at: event.at || nowISO(),
      ...event,
    };

    const member = ctx.members.value[index];
    ctx.members.value[index] = {
      ...member,
      changeHistory: [entry, ...(member.changeHistory || [])].slice(0, 20),
    };

    return entry;
  };

  const memberByEmail = (email) => {
    const normalizedEmail = ctx.normalizeLookupEmail(email);
    return ctx.members.value.find((member) => ctx.normalizeLookupEmail(member.email || member.correo) === normalizedEmail) || null;
  };

  const memberById = (id) => ctx.members.value.find((member) => member.id === id) || null;

  const upsertMember = (payload) => {
    const existingMember = ctx.members.value.find((entry) => entry.id === payload.id);
    const baseMembershipStart = payload.membershipStart || existingMember?.membershipStart || payload.joinedAt || todayISO();
    const resolvedPlanId = payload.planId || existingMember?.planId || 'plan-monthly';

    const member = {
      id: payload.id || `member-${Date.now()}`,
      name: payload.name?.trim() || existingMember?.name || 'Sin nombre',
      dni: payload.dni?.trim() || existingMember?.dni || '',
      internalCode: String(existingMember?.id_cliente || payload.id_cliente || existingMember?.internalCode || '').trim(),
      email: payload.email?.trim() || existingMember?.email || '',
      phone: payload.phone?.trim() || existingMember?.phone || '',
      role: payload.role || existingMember?.role || 'user',
      plan: payload.plan || existingMember?.plan || 'Mensual',
      planId: resolvedPlanId,
      membershipStart: baseMembershipStart,
      membershipEnd:
        payload.membershipEnd ||
        existingMember?.membershipEnd ||
        addDays(baseMembershipStart, planDurationDays(ctx.getPlanById?.(resolvedPlanId), resolvedPlanId)),
      membershipPrice: Number(payload.membershipPrice ?? existingMember?.membershipPrice ?? 0),
      status: normalizeMembershipStatus(payload.status || existingMember?.status),
      membershipStatus: normalizeMembershipStatus(payload.membershipStatus || existingMember?.membershipStatus || payload.status),
      joinedAt: payload.joinedAt || existingMember?.joinedAt || todayISO(),
      attendanceRate: Number(payload.attendanceRate ?? existingMember?.attendanceRate ?? 0),
      membershipHistory: Array.isArray(payload.membershipHistory) ? payload.membershipHistory : existingMember?.membershipHistory || [],
      changeHistory: Array.isArray(payload.changeHistory) ? payload.changeHistory : existingMember?.changeHistory || [],
      schedules: Array.isArray(payload.schedules) ? payload.schedules : existingMember?.schedules || [],
    };

    if (ctx.apiBase) {
      const backendId = Number(existingMember?.id_cliente || String(payload.id || '').match(/^(?:cliente-|SGCLI)(\d+)$/i)?.[1] || payload.id_cliente || 0) || null;
      const body = {
        ...(backendId ? { id_cliente: backendId } : {}),
        id_usuario: backendId ? `SGCLI${String(backendId).padStart(3, '0')}` : undefined,
        nombre: member.name || '',
        correo: member.email || '',
        telefono: member.phone || '',
        dni: member.dni || '',
        password: payload.password || payload.contrasena || '',
        plan: member.plan || 'MENSUAL',
        promocion: member.promocion || 'SIN PROMOCION',
        estado: String(member.status || 'ACTIVO').toUpperCase(),
      };

      return remote.upsertMember(body)
        .then((created) => {
          const localMember = { ...member, ...normalizeBackendClientToMember(created, member) };
          const idx = ctx.members.value.findIndex((m) => m.id === localMember.id || m.dni === localMember.dni);
          if (idx >= 0) ctx.members.value[idx] = localMember; else ctx.members.value.unshift(localMember);

          // Si se asignó un plan en el payload, registrar membresía
          /**
           * Gestiona esta acción de la vista.
           */
          const numericPm = (() => {
            if (payload.planId && String(payload.planId).match(/\d+/)) return Number(String(payload.planId).match(/\d+/)[0]);
            return null;
          })();
          if (numericPm) {
            const regPayload = { cliente: created, id_pm: numericPm, fecha_inicio: member.membershipStart, fecha_fin: member.membershipEnd };
            return registerClienteMembresiaToServer(regPayload).then(() => localMember);
          }

          return localMember;
        });
    }

    const index = ctx.members.value.findIndex((entry) => entry.id === member.id);
    if (index >= 0) {
      ctx.members.value[index] = member;
    } else {
      ctx.members.value.unshift(member);
    }
    return member;
  };

  const deleteMember = async (id) => {
    if (ctx.apiBase && /^(?:cliente-|SGCLI)\d+$/i.test(id)) {
      const id_cliente = Number(String(id).replace(/^(?:cliente-|SGCLI)/i, ''));
      await remote.deleteMember(id_cliente);
    }
    ctx.members.value = ctx.members.value.filter((member) => member.id !== id);
    ctx.attendance.value = ctx.attendance.value.filter((entry) => entry.memberId !== id);
    ctx.attendancePasses.value = ctx.attendancePasses.value.filter((pass) => pass.memberId !== id);
  };

  const deleteClient = (id) => deleteMember(id);

  const upsertClienteToServer = async (clientePayload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return await remote.upsertClienteToServer(clientePayload);
  };

  const upsertClient = async (payload) => {
    const existingClient = ctx.members.value.find((entry) => String(entry.id) === String(payload.id_usuario || '').trim());
    const clientPayload = {
      ...(payload.id_usuario ? { id_usuario: String(payload.id_usuario).trim() } : {}),
      nombre: String(payload.nombre || existingClient?.name || '').trim(),
      correo: String(payload.correo || payload.email || existingClient?.email || '').trim(),
      telefono: String(payload.telefono || existingClient?.phone || '').trim(),
      dni: String(payload.dni || existingClient?.dni || '').trim(),
      password: String(payload.password || payload.contrasena || '').trim(),
      plan: String(payload.plan || existingClient?.plan || 'MENSUAL').trim() || 'MENSUAL',
      // id_promocion NO va dentro del objeto cliente — va en la raíz del payload de registro
      promocion: existingClient?.promocion || 'SIN PROMOCION',
      estado: String(payload.estado || existingClient?.status || 'ACTIVO').trim().toUpperCase() || 'ACTIVO',
    };

    if (ctx.apiBase) {
      let saved;
      const isNewClient = !payload.id_usuario;

      if (isNewClient) {
        const result = await remote.registerAdmin({
          ...clientPayload,
          id_promocion: Number(payload.id_promocion) || null,
          pagar_con_stripe: Boolean(payload.pagar_con_stripe),
        });
        requireRecord(result);
        requireRecord(result.cliente);
        const membership = requireRecord(result.membresia, 'id_membresia');
        const client = mergeClient({
          ...result.cliente,
          id_membresia: membership.id_membresia,
          id_promocion: membership.id_promocion,
          membership_status: membership.estado,
          membership_start: membership.fecha_inicio,
          membership_end: membership.fecha_fin,
          payment_status: membership.estado_pago,
          payment_reference: membership.referencia_pago,
          monto_pago: membership.monto_pago,
        });
        return { ...client, payment: result.payment };
      } else {
        // EDICIÓN: solo actualizar datos del cliente
        saved = await upsertClienteToServer(clientPayload);
      }

      const normalized = {
        ...existingClient,
        ...normalizeBackendClientToMember(requireRecord(saved, 'id_cliente'), existingClient),
        attendanceRate: Number(existingClient?.attendanceRate ?? 0),
        membershipHistory: existingClient?.membershipHistory || [],
        changeHistory: existingClient?.changeHistory || [],
        schedules: existingClient?.schedules || [],
      };

      const index = ctx.members.value.findIndex((entry) => String(entry.id) === String(normalized.id));
      if (index >= 0) {
        ctx.members.value[index] = normalized;
      } else {
        ctx.members.value.unshift(normalized);
      }
      refreshAfterMutation(ctx, () => ctx.fetchFromBackend({ section: 'clients', force: true }));
      return normalized;
    }

    const fallbackId = clientPayload.id_usuario || `SGCLI${String(ctx.members.value.length + 1).padStart(3, '0')}`;
    const normalized = {
      id: fallbackId,
      id_cliente: Number(String(fallbackId).replace(/^SGCLI/i, '')) || ctx.members.value.length + 1,
      name: clientPayload.nombre,
      dni: clientPayload.dni,
      internalCode: fallbackId,
      email: clientPayload.correo,
      phone: clientPayload.telefono,
      role: 'user',
      plan: clientPayload.plan,
      planId: '',
      id_membresia: null,
      membershipStatus: normalizeMembershipStatus(clientPayload.estado),
      membershipStart: '',
      membershipEnd: '',
      paymentStatus: '',
      paymentReference: '',
      hasPassword: Boolean(clientPayload.password),
      membershipPrice: 0,
      status: clientPayload.estado,
      joinedAt: todayISO(),
      attendanceRate: 0,
      membershipHistory: [],
      changeHistory: [],
      schedules: [],
    };

    const index = ctx.members.value.findIndex((entry) => String(entry.id) === String(normalized.id));
    if (index >= 0) {
      ctx.members.value[index] = normalized;
    } else {
      ctx.members.value.unshift(normalized);
    }
    return normalized;
  };

  const registerClienteMembresiaToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return await remote.registerClienteMembresiaToServer(payload);
  };

  const mergeClient = (client) => {
    requireRecord(client);
    let normalized = normalizeBackendClientToMember(client);
    const index = ctx.members.value.findIndex((entry) => String(entry.id) === String(normalized.id) || Number(entry.id_cliente) === Number(normalized.id_cliente));
    if (index >= 0) {
      normalized = normalizeBackendClientToMember(client, ctx.members.value[index]);
      ctx.members.value[index] = normalized;
    } else {
      ctx.members.value.unshift(normalized);
    }
    return normalized;
  };

  const registerPublicClient = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.registerPublicClient(payload);
    requireRecord(saved);
    if (saved.preregistro) {
      const request = requireRecord(saved.preregistro);
      if (!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(String(request.token || ''))
        || !['PENDIENTE', 'CONVERTIDO'].includes(request.estado) || !(Number(request.monto_pago) > 0)) {
        throw new Error('El servidor no devolvió un preregistro pendiente válido.');
      }
      return { preregistration: request, payment: saved.payment || null };
    }
    requireRecord(saved.cliente);
    const membership = requireRecord(saved.membresia, 'id_membresia');
    const client = mergeClient({
      ...(saved.cliente || {}),
      id_membresia: membership.id_membresia,
      membership_status: membership.estado,
      membership_start: membership.fecha_inicio,
      membership_end: membership.fecha_fin,
      payment_status: membership.estado_pago,
      payment_reference: membership.referencia_pago,
      monto_pago: membership.monto_pago,
      id_promocion: membership.id_promocion,
    });
    return { client, payment: saved.payment || null };
  };

  const confirmarPagoEfectivo = async (idCliente) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const data = await remote.confirmarPagoEfectivo(idCliente);
    const saved = requireRecord(data).data;
    requireRecord(saved);
    requireRecord(saved.cliente);
    const membership = requireRecord(saved.membresia, 'id_membresia');
    const client = mergeClient({
      ...(saved.cliente || {}),
      id_membresia: membership.id_membresia,
      membership_status: membership.estado,
      membership_start: membership.fecha_inicio,
      membership_end: membership.fecha_fin,
      payment_status: membership.estado_pago,
      payment_reference: membership.referencia_pago,
      monto_pago: membership.monto_pago,
      id_promocion: membership.id_promocion,
    });
    await refreshAfterMutation(ctx, () => ctx.fetchFromBackend({ section: 'clients', force: true }));
    return client;
  };

  return { memberByInternalCode, searchMembers, logMemberEvent, memberByEmail, memberById, upsertMember, deleteMember, deleteClient, upsertClienteToServer, upsertClient, registerClienteMembresiaToServer, normalizeClientFromBackend: normalizeBackendClientToMember, mergeClient, registerPublicClient, confirmarPagoEfectivo };
};
