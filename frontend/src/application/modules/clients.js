/** Estado y operaciones del módulo clients. */
import { nowISO, todayISO, addMonthsISO, planDurationById } from '../../domain/utils/gymRules.js';
import { normalizeMembershipStatus } from '../../domain/utils/clientDirectory.js';
import { backendRequest, apiPost } from '../services/backendGateway.js';
import { useAuthStore } from '../stores/authStore.js';

export const createClientsModule = (ctx) => {
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
        addMonthsISO(baseMembershipStart, planDurationById(resolvedPlanId)),
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
        id_usuario: member.id || undefined,
        nombre: member.name || '',
        correo: member.email || '',
        telefono: member.phone || '',
        dni: member.dni || '',
        password: payload.password || payload.contrasena || '',
        plan: member.plan || 'MENSUAL',
        promocion: member.promocion || 'SIN PROMOCION',
        estado: String(member.status || 'ACTIVO').toUpperCase(),
      };

      return backendRequest(`${ctx.apiBase}/clientes`, { method: 'POST', headers: ctx._authHeaders(), body: JSON.stringify(body) })
        .then((r) => {
          if (!r.ok) throw new Error('Error al crear/actualizar cliente en backend');
          return r.json();
        })
        .then((created) => {
          const id_cliente = Number(String(created.id_usuario || created.id || '').replace(/^SGCLI/i, '')) || backendId || Date.now();
          const localId = created.id_usuario || `SGCLI${String(id_cliente).padStart(3, '0')}`;
          const localMember = { ...member, id: localId, id_cliente, internalCode: String(localId), joinedAt: created.fecha_registro || member.joinedAt };
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

  const deleteMember = (id) => {
    if (ctx.apiBase && /^(?:cliente-|SGCLI)\d+$/i.test(id)) {
      const id_cliente = Number(String(id).replace(/^(?:cliente-|SGCLI)/i, ''));
      backendRequest(`${ctx.apiBase}/clientes/${id_cliente}`, { method: 'DELETE', headers: ctx._authHeaders() }).catch(() => { });
    }
    ctx.members.value = ctx.members.value.filter((member) => member.id !== id);
    ctx.attendance.value = ctx.attendance.value.filter((entry) => entry.memberId !== id);
    ctx.attendancePasses.value = ctx.attendancePasses.value.filter((pass) => pass.memberId !== id);
  };

  const deleteClient = (id) => deleteMember(id);

  const upsertClienteToServer = async (clientePayload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/clientes`, { method: 'POST', headers: ctx._authHeaders(), body: JSON.stringify(clientePayload) });
    if (!res.ok) throw new Error('Error al guardar cliente en backend');
    return res.json();
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
      promocion: 'SIN PROMOCION',
      estado: String(payload.estado || existingClient?.status || 'ACTIVO').trim().toUpperCase() || 'ACTIVO',
    };

    if (ctx.apiBase) {
      let saved;
      const isNewClient = !payload.id_usuario;

      if (isNewClient) {
        const result = await apiPost('/clientes/registro-admin', {
          ...clientPayload,
          id_promocion: Number(payload.id_promocion) || null,
          pagar_con_stripe: Boolean(payload.pagar_con_stripe),
        }, useAuthStore().token);
        const membership = result.membresia || {};
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

      // Resolver nombre real de la promoción usando el catálogo local
      const numericId = Number(saved.id_cliente || 0) || Number(String(saved.id_usuario || '').replace(/^SGCLI/i, '')) || Number(existingClient?.id_cliente || 0) || Date.now();
      const savedPromoId = saved.id_promocion || (payload.id_promocion && Number(payload.id_promocion) > 0 ? Number(payload.id_promocion) : null);
      const promoObj = savedPromoId ? ctx.promotions.value.find(p => Number(p.id_promocion) === Number(savedPromoId)) : null;
      const promoName = promoObj ? (promoObj.name || promoObj.nombre || `promo-${savedPromoId}`) : 'SIN PROMOCION';

      const normalized = {
        id: saved.id_usuario || `SGCLI${String(numericId).padStart(3, '0')}`,
        id_cliente: numericId,
        name: saved.nombre || clientPayload.nombre,
        dni: saved.dni || clientPayload.dni,
        internalCode: String(saved.id_usuario || `SGCLI${String(numericId).padStart(3, '0')}`),
        email: saved.correo || clientPayload.correo,
        phone: saved.telefono || clientPayload.telefono,
        role: 'user',
        plan: saved.plan || clientPayload.plan,
        promocion: promoName,
        id_promocion: savedPromoId,
        planId: '',
        id_membresia: saved.id_membresia || existingClient?.id_membresia || null,
        membershipStatus: normalizeMembershipStatus(saved.membership_status || saved.estado || existingClient?.membershipStatus || clientPayload.estado),
        membershipStart: saved.membership_start || saved.fecha_inicio || existingClient?.membershipStart || '',
        membershipEnd: saved.membership_end || saved.fecha_fin || existingClient?.membershipEnd || '',
        registrationOrigin: saved.origen_registro || existingClient?.registrationOrigin || '',
        paymentStatus: saved.payment_status || saved.estado_pago || existingClient?.paymentStatus || '',
        paymentReference: saved.payment_reference || saved.referencia_pago || existingClient?.paymentReference || '',
        hasPassword: Boolean(saved.has_password ?? saved.hasPassword ?? existingClient?.hasPassword),
        membershipPrice: Number(saved.monto_pago ?? existingClient?.membershipPrice ?? 0),
        status: saved.estado || clientPayload.estado,
        joinedAt: existingClient?.joinedAt || '',
        attendanceRate: Number(existingClient?.attendanceRate ?? 0),
        membershipHistory: Array.isArray(existingClient?.membershipHistory) ? existingClient.membershipHistory : [],
        changeHistory: Array.isArray(existingClient?.changeHistory) ? existingClient.changeHistory : [],
        schedules: Array.isArray(existingClient?.schedules) ? existingClient.schedules : [],
      };


      const index = ctx.members.value.findIndex((entry) => String(entry.id) === String(normalized.id));
      if (index >= 0) {
        ctx.members.value[index] = normalized;
      } else {
        ctx.members.value.unshift(normalized);
      }
      ctx.fetchFromBackend({ section: 'clients', force: true }).catch(() => {});
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
    const res = await backendRequest(`${ctx.apiBase}/registro-cliente-membresia`, { method: 'POST', headers: ctx._authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error('Error al registrar cliente y membresía');
    return res.json();
  };

  const normalizeClientFromBackend = (client = {}) => {
    const numericId = Number(client.id_cliente || 0) || Number(String(client.id_usuario || '').replace(/^SGCLI/i, '')) || Date.now();
    return {
      id: client.id_usuario || `SGCLI${String(numericId).padStart(3, '0')}`,
      id_cliente: numericId,
      name: client.nombre || '',
      dni: client.dni || '',
      internalCode: String(client.id_usuario || `SGCLI${String(numericId).padStart(3, '0')}`),
      email: client.correo || client.email || '',
      phone: client.telefono || client.phone || '',
      role: 'user',
      plan: client.plan || 'MENSUAL',
      promocion: client.promocion || 'SIN PROMOCION',
      planId: '',
      id_membresia: client.id_membresia || null,
      membershipStatus: normalizeMembershipStatus(client.membership_status || client.estado),
      membershipStart: client.membership_start || '',
      membershipEnd: client.membership_end || '',
      registrationOrigin: client.origen_registro || '',
      id_promocion: client.id_promocion || null,
      paymentStatus: client.payment_status || '',
      paymentReference: client.payment_reference || '',
      hasPassword: Boolean(client.has_password ?? client.hasPassword),
      membershipPrice: Number(client.monto_pago ?? 0),
      status: String(client.estado || 'EN_TRAMITE').toUpperCase(),
      joinedAt: client.fecha_registro || '',
      attendanceRate: 0,
      membershipHistory: [],
      changeHistory: [],
      schedules: [],
    };
  };

  const mergeClient = (client) => {
    const normalized = normalizeClientFromBackend(client);
    const index = ctx.members.value.findIndex((entry) => String(entry.id) === String(normalized.id) || Number(entry.id_cliente) === Number(normalized.id_cliente));
    if (index >= 0) {
      ctx.members.value[index] = { ...ctx.members.value[index], ...normalized };
    } else {
      ctx.members.value.unshift(normalized);
    }
    return normalized;
  };

  const registerPublicClient = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/registro-publico`, {
      method: 'POST',
      headers: ctx._authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await ctx.readBackendError(res, 'No se pudo completar el registro'));

    const saved = await res.json();
    const membership = saved.membresia || {};
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
    const res = await backendRequest(`${ctx.apiBase}/clientes/${idCliente}/confirmar-pago-manual`, {
      method: 'POST',
      headers: ctx._authHeaders(),
    });
    if (!res.ok) throw new Error(await ctx.readBackendError(res, 'No se pudo confirmar el pago manual'));

    const data = await res.json();
    const saved = data.data;
    const membership = saved.membresia || {};
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
    await ctx.fetchFromBackend({ section: 'clients', force: true }).catch(() => {});
    return client;
  };

  return { memberByInternalCode, searchMembers, logMemberEvent, memberByEmail, memberById, upsertMember, deleteMember, deleteClient, upsertClienteToServer, upsertClient, registerClienteMembresiaToServer, normalizeClientFromBackend, mergeClient, registerPublicClient, confirmarPagoEfectivo };
};
