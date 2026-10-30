import { requireList, requireRecord } from '../services/responseValidation.js';
import { refreshAfterMutation } from '../services/refreshAfterMutation.js';
import { bindSessionRepository } from '../services/sessionBoundary.js';
import { addDays } from '../../domain/utils/dates.js';
/** Estado y operaciones del módulo memberships. */
import { todayISO, daysUntilISO, MEMBER_ALERT_DAYS, normalizePlanFromBackend, normalizePromotionFromBackend, planDurationDays, nowISO } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';
import { discountedPrice, toCents } from '../../domain/utils/money.js';
import { clientMembershipGroup, normalizeMembershipStatus } from '../../domain/utils/clientDirectory.js';

export const createMembershipsModule = (ctx, repository) => {
  const remote = bindSessionRepository(repository, () => ctx.authStore.token, ctx.pinia);
  const activePlans = computed(() => ctx.planCatalog.value.filter((plan) => plan.active));

  const activePromotions = computed(() =>
    ctx.promotions.value.filter((promotion) => {
      if (!promotion.active) return false;
      const today = todayISO();
      if (promotion.validUntil && promotion.validUntil < today) return false;
      const isCupoCumplido =
        promotion.limite_cupos !== null &&
        promotion.limite_cupos !== undefined &&
        Number(promotion.usos_actuales || 0) >= Number(promotion.limite_cupos);
      if (isCupoCumplido) return false;
      return true;
    }),
  );

  const membershipAlerts = computed(() =>
    ctx.members.value
      .filter((member) => clientMembershipGroup(member) === 'active' && member.membershipEnd)
      .map((member) => ({
        ...member,
        daysUntilExpiry: daysUntilISO(member.membershipEnd),
      }))
      .filter((member) => member.daysUntilExpiry <= MEMBER_ALERT_DAYS),
  );

  const getPlanById = (planId) => ctx.planCatalog.value.find((plan) => plan.id === planId) || null;

  const getPromotionById = (promotionId) => ctx.promotions.value.find((promotion) => promotion.id === promotionId) || null;

  const isMembershipActive = (member, referenceDate = todayISO()) => {
    const status = String(member?.membershipStatus || member?.status || '').trim().toUpperCase();
    return Boolean(member) && ['ACTIVO', 'ACTIVA'].includes(status) && (!member.membershipEnd || member.membershipEnd >= referenceDate);
  };

  const isMembershipExpiringSoon = (member) => Boolean(member?.membershipEnd) && daysUntilISO(member.membershipEnd) <= MEMBER_ALERT_DAYS;

  const calculatePlanCharge = (planId, promotionId = '') => {
    const plan = getPlanById(planId);
    if (!plan) {
      throw new Error('Plan no encontrado');
    }

    const promotion = promotionId ? getPromotionById(promotionId) : null;
    let discountAmount = 0;

    if (
      promotion &&
      promotion.active &&
      (!promotion.startsAt || promotion.startsAt <= todayISO()) &&
      (promotion.limite_cupos == null || Number(promotion.usos_actuales || 0) < Number(promotion.limite_cupos)) &&
      (!promotion.validUntil || promotion.validUntil >= todayISO()) &&
      (!promotion.appliesTo?.length || promotion.appliesTo.includes(planId))
    ) {
      discountAmount = (toCents(plan.price) - toCents(discountedPrice(plan.price, promotion.discountValue || 0, promotion.discountType))) / 100;
    }

    return {
      plan,
      promotion,
      basePrice: Number(plan.price || 0),
      discountAmount,
      finalPrice: Math.max(0, toCents(plan.price || 0) - toCents(discountAmount)) / 100,
    };
  };

  const mergePlan = (plan) => {
    requireRecord(plan, 'id_pm');
    const normalized = normalizePlanFromBackend(plan);
    const index = ctx.planCatalog.value.findIndex((entry) => Number(entry.id_pm) === Number(normalized.id_pm));
    if (index >= 0) ctx.planCatalog.value[index] = normalized; else ctx.planCatalog.value.unshift(normalized);
    return normalized;
  };

  const upsertPlan = async (payload) => {
    const idPm = payload.id_pm || Number(String(payload.id || '').match(/(\d+)/)?.[1] || 0) || null;
    const body = {
      id_pm: idPm || undefined,
      nombre_plan: String(payload.nombre_plan || payload.name || '').trim().toUpperCase() || 'SIN NOMBRE',
      duracion: String(payload.duracion || payload.duration || `${payload.durationMonths || 1} dias`).trim(),
      precio: Number(payload.precio ?? payload.price ?? 0),
      descripcion: payload.descripcion || payload.description || '',
      beneficios: payload.beneficios || payload.benefits || '',
      activo: payload.activo ?? payload.active ?? true,
    };

    if (ctx.apiBase) {
      const response = await remote.upsertPlan(idPm, body);

      return mergePlan(response);
    }

    return mergePlan({ ...body, id_pm: idPm || Date.now() });
  };

  const deletePlan = async (planId) => {
    const idPm = Number(String(planId || '').match(/(\d+)/)?.[1] || 0);
    if (!idPm) throw new Error('Plan no encontrado');
    if (ctx.apiBase) {
      await remote.deletePlan(idPm);
    }
    ctx.planCatalog.value = ctx.planCatalog.value.filter((plan) => Number(plan.id_pm) !== idPm);
  };

  const mergePromotion = (promotion) => {
    requireRecord(promotion, 'id_promocion');
    const normalized = normalizePromotionFromBackend(promotion);
    const index = ctx.promotions.value.findIndex((entry) => Number(entry.id_promocion) === Number(normalized.id_promocion));
    if (index >= 0) ctx.promotions.value[index] = normalized; else ctx.promotions.value.unshift(normalized);
    return normalized;
  };

  const upsertPromotion = async (payload) => {
    const idPromocion = payload.id_promocion || Number(String(payload.id || '').match(/(\d+)/)?.[1] || 0) || null;
    const body = {
      id_promocion: idPromocion || undefined,
      nombre: String(payload.nombre || payload.name || '').trim() || 'Promocion',
      descripcion: payload.descripcion || payload.description || payload.note || '',
      tipo_descuento: payload.tipo_descuento || (payload.discountType === 'fixed' ? 'monto' : 'porcentaje'),
      valor_descuento: Number(payload.valor_descuento ?? payload.discountValue ?? 0),
      fecha_inicio: payload.fecha_inicio || payload.startsAt || '',
      fecha_fin: payload.fecha_fin || payload.validUntil || '',
      icono_etiqueta: payload.icono_etiqueta || payload.badgeIcon || '🏷️',
      palabra_clave: String(payload.palabra_clave || payload.badgeTag || '').trim().toUpperCase(),
      activo: payload.activo ?? payload.active ?? true,
      planes_aplicables: (payload.planes_aplicables || payload.appliesTo || [])
        .map((value) => Number(String(value).match(/(\d+)/)?.[1] || value))
        .filter(Boolean),
      limite_cupos: payload.limite_cupos !== undefined && payload.limite_cupos !== null && String(payload.limite_cupos).trim() !== '' ? Number(payload.limite_cupos) : null,
      usos_actuales: Number(payload.usos_actuales || 0),
    };

    if (ctx.apiBase) {
      const saved = await remote.upsertPromotion(idPromocion, body);
      requireRecord(saved, 'id_promocion');
      return mergePromotion({ ...body, ...saved });
    }

    return mergePromotion({ ...body, id_promocion: idPromocion || Date.now() });
  };

  const deletePromotion = async (promotionId) => {
    const idPromocion = Number(String(promotionId || '').match(/(\d+)/)?.[1] || 0);
    if (!idPromocion) throw new Error('Promocion no encontrada');
    if (ctx.apiBase) {
      await remote.deletePromotion(idPromocion);
    }
    ctx.promotions.value = ctx.promotions.value.filter((promotion) => Number(promotion.id_promocion) !== idPromocion);
  };

  const assignPlanToMember = (memberId, planId, promotionId = '', note = 'Asignación de membresía') => {
    // Si hay backend configurado, intentar delegar la creación/renovación al servidor
    const index = ctx.members.value.findIndex((entry) => entry.id === memberId);
    if (index < 0) {
      throw new Error('Miembro no encontrado');
    }

    const member = ctx.members.value[index];
    // Intentar extraer id_cliente si el id viene del backend (cliente-<id> o SGCLI<id>)
    if (ctx.apiBase && /^(?:cliente-|SGCLI)\d+$/i.test(memberId)) {
      const id_cliente = Number(String(memberId).replace(/^(?:cliente-|SGCLI)/i, ''));
      // Obtener id_pm numérico desde planId (soporta pm-<id> y 'pm-...')
      /**
       * Obtiene los datos necesarios.
       */
      const getNumericPm = (pid) => {
        if (!pid) return null;
        const m = String(pid).match(/(\d+)/);
        return m ? Number(m[0]) : null;
      };

      const id_pm = getNumericPm(planId) || getNumericPm(getPlanById(planId)?.id) || null;
      if (!id_pm) {
        throw new Error('No se pudo determinar id del plan para backend');
      }

      const startDate = member.membershipEnd && member.membershipEnd > todayISO() ? member.membershipEnd : todayISO();
      const endDate = addDays(startDate, planDurationDays(getPlanById(planId), planId));

      const id_promocion = promotionId ? Number(String(promotionId).match(/(\d+)/)?.[1] || promotionId) : null;
      const payload = { id_cliente, id_pm, fecha_inicio: startDate, fecha_fin: endDate, id_promocion };
      return remote.assignPlanToMember(payload)
        .then((memb) => {
          requireRecord(memb, 'id_membresia');
          // actualizar estado local mínimo
          ctx.members.value[index] = { ...member, plan: getPlanById(planId)?.name || member.plan, planId, membershipStart: startDate, membershipEnd: endDate, membershipPrice: memb.monto_pago ?? member.membershipPrice, id_membresia: memb.id_membresia, paymentStatus: memb.estado_pago || 'PENDIENTE', membershipStatus: normalizeMembershipStatus(memb.estado) };
          ctx.logMemberEvent(memberId, { action: memb.id_membresia ? 'Asignación' : 'Renovación', fields: ['plan', 'planId', 'membershipStart', 'membershipEnd', 'membershipPrice', 'status'], note });
          return ctx.members.value[index];
        });
    }

    // Fallback local
    const { plan, promotion, basePrice, discountAmount, finalPrice } = calculatePlanCharge(planId, promotionId);
    const startDate = member.membershipEnd && member.membershipEnd > todayISO() ? member.membershipEnd : todayISO();
    const endDate = addDays(startDate, planDurationDays(plan, planId));
    const eventType = member.planId && member.membershipHistory?.length ? 'Renovación' : 'Asignación';
    const historyEntry = {
      id: `membership-${Date.now()}`,
      type: eventType,
      at: nowISO(),
      planId: plan.id,
      planName: plan.name,
      startDate,
      endDate,
      price: basePrice,
      discount: discountAmount,
      finalPrice,
      promotionId: promotion?.id || '',
      note,
    };

    ctx.members.value[index] = {
      ...member,
      plan: plan.name,
      planId: plan.id,
      membershipStart: startDate,
      membershipEnd: endDate,
      membershipPrice: finalPrice,
      status: 'EN_TRAMITE',
      membershipStatus: 'EN_TRAMITE',
      paymentStatus: 'PENDIENTE',
      membershipHistory: [historyEntry, ...(member.membershipHistory || [])].slice(0, 20),
    };

    ctx.logMemberEvent(memberId, {
      action: eventType,
      fields: ['plan', 'planId', 'membershipStart', 'membershipEnd', 'membershipPrice', 'status'],
      note,
    });

    return ctx.members.value[index];
  };

  const renewMembership = (memberId, planId = '', promotionId = '', note = 'Renovación de membresía') => {
    const member = ctx.memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    return assignPlanToMember(memberId, planId || member.planId || 'plan-monthly', promotionId, note);
  };

  const refreshPromotionsFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const list = requireList(await remote.refreshPromotionsFromBackend(), 'id_promocion');
    ctx.promotions.value = list.map((promotion) => normalizePromotionFromBackend(promotion));
    return ctx.promotions.value;
  };

  const activateClientMembership = async (idCliente) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.activateClientMembership(idCliente);
    requireRecord(saved);
    requireRecord(saved.cliente);
    const membership = requireRecord(saved.membresia, 'id_membresia');
    const client = ctx.mergeClient({
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
    return { ...client, notification: saved.notification || null };
  };

  return { activePlans, activePromotions, membershipAlerts, getPlanById, getPromotionById, isMembershipActive, isMembershipExpiringSoon, calculatePlanCharge, mergePlan, upsertPlan, deletePlan, mergePromotion, upsertPromotion, deletePromotion, assignPlanToMember, renewMembership, refreshPromotionsFromBackend, activateClientMembership };
};
