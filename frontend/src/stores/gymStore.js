import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

const STORAGE_KEY = 'gym_frontend_data_v1';
const PASS_EXPIRY_MINUTES = 10;
const MEMBER_ALERT_DAYS = 7;
const PLAN_DURATION_MONTHS = {
  'plan-monthly': 1,
  'plan-quarterly': 3,
  'plan-annual': 12,
};

const seedState = () => ({
  planCatalog: [
    {
      id: 'plan-monthly',
      name: 'Mensual',
      durationMonths: 1,
      price: 80,
      description: 'Acceso estándar por 30 días.',
      active: true,
    },
    {
      id: 'plan-quarterly',
      name: 'Trimestral',
      durationMonths: 3,
      price: 210,
      description: 'Ideal para continuidad de corto plazo.',
      active: true,
    },
    {
      id: 'plan-annual',
      name: 'Anual',
      durationMonths: 12,
      price: 720,
      description: 'Mejor relación costo/beneficio.',
      active: true,
    },
  ],
  promotions: [
    {
      id: 'promo-welcome',
      name: 'Bienvenida 10%',
      discountType: 'percent',
      discountValue: 10,
      appliesTo: ['plan-monthly', 'plan-quarterly'],
      active: true,
      validUntil: '2026-12-31',
      note: 'Promoción inicial de captación.',
    },
  ],
  members: [
    {
      id: 'member-1',
      name: 'María Fernández',
      dni: '74281635',
      internalCode: 'GYM-0001',
      email: 'maria@ejemplo.com',
      phone: '999 111 222',
      role: 'user',
      plan: 'Mensual',
      planId: 'plan-monthly',
      membershipStart: '2026-01-12',
      membershipEnd: '2026-06-12',
      membershipPrice: 80,
      status: 'Activa',
      joinedAt: '2026-01-12',
      attendanceRate: 92,
      membershipHistory: [
        {
          id: 'memhist-1',
          type: 'Alta',
          at: '2026-01-12T08:00:00.000Z',
          planId: 'plan-monthly',
          startDate: '2026-01-12',
          endDate: '2026-06-12',
          price: 80,
          discount: 0,
          note: 'Registro inicial del socio.',
        },
      ],
      changeHistory: [
        {
          id: 'change-1',
          at: '2026-01-12T08:00:00.000Z',
          action: 'Registro inicial',
          fields: ['name', 'email', 'phone', 'plan', 'status'],
        },
      ],
      schedules: [],
    },
    {
      id: 'member-2',
      name: 'Carlos Rojas',
      dni: '71928451',
      internalCode: 'GYM-0002',
      email: 'carlos@urp.edu.pe',
      phone: '988 222 333',
      role: 'admin',
      plan: 'Anual',
      planId: 'plan-annual',
      membershipStart: '2025-11-03',
      membershipEnd: '2026-11-03',
      membershipPrice: 720,
      status: 'Activa',
      joinedAt: '2025-11-03',
      attendanceRate: 88,
      membershipHistory: [],
      changeHistory: [],
      schedules: [],
    },
    {
      id: 'member-3',
      name: 'Lucía Torres',
      dni: '78451236',
      internalCode: 'GYM-0003',
      email: 'lucia@ejemplo.com',
      phone: '977 444 555',
      role: 'user',
      plan: 'Trimestral',
      planId: 'plan-quarterly',
      membershipStart: '2026-03-20',
      membershipEnd: '2026-06-20',
      membershipPrice: 210,
      status: 'Pendiente',
      joinedAt: '2026-03-20',
      attendanceRate: 76,
      membershipHistory: [],
      changeHistory: [],
      schedules: [],
    },
  ],
  attendance: [
    {
      id: 'attendance-1',
      memberId: 'member-1',
      memberName: 'María Fernández',
      type: 'Entrada',
      time: '07:10',
      date: '2026-05-03',
      note: 'Rutina funcional',
    },
    {
      id: 'attendance-2',
      memberId: 'member-2',
      memberName: 'Carlos Rojas',
      type: 'Entrada',
      time: '06:45',
      date: '2026-05-03',
      note: 'Revisión general',
    },
    {
      id: 'attendance-3',
      memberId: 'member-3',
      memberName: 'Lucía Torres',
      type: 'Salida',
      time: '19:05',
      date: '2026-05-02',
      note: 'Finalizó cardio',
    },
  ],
  attendancePasses: [],
  inventory: [
    {
      id: 'item-1',
      inventoryCode: 'INV-0001',
      name: 'Mancuernas ajustables',
      category: 'Pesas',
      quantity: 12,
      minQuantity: 6,
      location: 'Sala 1',
      status: 'Operativo',
      observations: 'En buen estado operativo.',
    },
    {
      id: 'item-2',
      inventoryCode: 'INV-0002',
      name: 'Tapetes de yoga',
      category: 'Accesorios',
      quantity: 8,
      minQuantity: 10,
      location: 'Depósito',
      status: 'En mantenimiento',
      observations: 'Requiere revisión por desgaste.',
    },
    {
      id: 'item-3',
      inventoryCode: 'INV-0003',
      name: 'Bandas de resistencia',
      category: 'Accesorios',
      quantity: 18,
      minQuantity: 8,
      location: 'Recepción',
      status: 'Operativo',
      observations: 'Reposición reciente.',
    },
  ],
  schedule: [
    { day: 'Lunes', hours: '06:00 - 22:00', focus: 'Piernas y glúteos' },
    { day: 'Martes', hours: '06:00 - 22:00', focus: 'Espalda y core' },
    { day: 'Miércoles', hours: '06:00 - 22:00', focus: 'Pecho y hombros' },
    { day: 'Jueves', hours: '06:00 - 22:00', focus: 'Cardio y movilidad' },
    { day: 'Viernes', hours: '06:00 - 22:00', focus: 'Full body' },
    { day: 'Sábado', hours: '08:00 - 18:00', focus: 'Clases dirigidas' },
    { day: 'Domingo', hours: '09:00 - 14:00', focus: 'Mantenimiento' },
  ],
});

const todayISO = () => new Date().toISOString().slice(0, 10);
const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
const nowISO = () => new Date().toISOString();
const dateFromISO = (value) => new Date(`${value}T00:00:00`);
const toISODate = (value) => value.toISOString().slice(0, 10);

const addMonthsISO = (dateISO, months) => {
  const date = dateFromISO(dateISO);
  date.setMonth(date.getMonth() + months);
  return toISODate(date);
};

const daysUntilISO = (dateISO) => {
  const diff = dateFromISO(dateISO).getTime() - dateFromISO(todayISO()).getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
};

const planDurationById = (planId) => PLAN_DURATION_MONTHS[planId] || 1;

const planNameById = (planId) =>
  ({
    'plan-monthly': 'Mensual',
    'plan-quarterly': 'Trimestral',
    'plan-annual': 'Anual',
  })[planId] || 'Mensual';

const generateInventoryCode = () =>
  `INV-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 5).toUpperCase()}`;

const normalizeInventoryItem = (item = {}) => ({
  ...item,
  inventoryCode: item.inventoryCode || `INV-${String(item.id || Date.now()).slice(-4).toUpperCase()}`,
});

const normalizeMember = (member = {}) => {
  const planId = member.planId || (member.plan === 'Anual' ? 'plan-annual' : member.plan === 'Trimestral' ? 'plan-quarterly' : 'plan-monthly');
  const baseDate = member.membershipStart || member.joinedAt || todayISO();

  return {
    ...member,
    dni: member.dni || '',
    internalCode: member.internalCode || `GYM-${String(member.id || Date.now()).slice(-4).toUpperCase()}`,
    plan: member.plan || planNameById(planId),
    planId,
    membershipStart: baseDate,
    membershipEnd: member.membershipEnd || addMonthsISO(baseDate, planDurationById(planId)),
    membershipPrice: Number(member.membershipPrice ?? 0),
    membershipHistory: Array.isArray(member.membershipHistory) ? member.membershipHistory : [],
    changeHistory: Array.isArray(member.changeHistory) ? member.changeHistory : [],
    schedules: Array.isArray(member.schedules) ? member.schedules : [],
  };
};

const normalizeState = (state) => ({
  ...seedState(),
  ...state,
  members: Array.isArray(state?.members) ? state.members.map((member) => normalizeMember(member)) : seedState().members,
  planCatalog: Array.isArray(state?.planCatalog) ? state.planCatalog : seedState().planCatalog,
  promotions: Array.isArray(state?.promotions) ? state.promotions : seedState().promotions,
  attendancePasses: Array.isArray(state?.attendancePasses) ? state.attendancePasses : [],
  inventory: Array.isArray(state?.inventory) ? state.inventory.map((item) => normalizeInventoryItem(item)) : seedState().inventory,
});

const generatePassCode = () => {
  const timeSegment = Date.now().toString(36).toUpperCase();
  const randomSegment = Math.random().toString(36).slice(2, 8).toUpperCase();
  return `${timeSegment}-${randomSegment}`;
};

const isPassExpired = (pass) => {
  if (!pass?.expiresAt) return true;
  return Date.now() > new Date(pass.expiresAt).getTime();
};

const getPassPayload = (pass) =>
  JSON.stringify({
    gym: 'AC-Silver-s-GYM',
    passId: pass.id,
    memberId: pass.memberId,
    code: pass.code,
    issuedAt: pass.issuedAt,
    expiresAt: pass.expiresAt,
  });

const parsePassInput = (input) => {
  if (!input) return '';

  const normalized = input.trim();
  if (!normalized) return '';

  try {
    const parsed = JSON.parse(normalized);
    if (parsed?.code) {
      return String(parsed.code).trim();
    }
  } catch (error) {
    // Keep the raw value if the payload is not JSON.
  }

  return normalized;
};

const loadState = () => {
  if (typeof window === 'undefined') {
    return seedState();
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    return seedState();
  }

  try {
    const parsed = JSON.parse(stored);
    return normalizeState(parsed);
  } catch (error) {
    return seedState();
  }
};

export const useGymStore = defineStore('gym', () => {
  const initialState = loadState();
  const planCatalog = ref(initialState.planCatalog);
  const promotions = ref(initialState.promotions);
  const members = ref(initialState.members);
  const attendance = ref(initialState.attendance);
  const attendancePasses = ref(initialState.attendancePasses || []);
  const inventory = ref(initialState.inventory);
  const schedule = ref(initialState.schedule);

  const persist = () => {
    if (typeof window === 'undefined') return;

    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        members: members.value,
        attendance: attendance.value,
        attendancePasses: attendancePasses.value,
        planCatalog: planCatalog.value,
        promotions: promotions.value,
        inventory: inventory.value,
        schedule: schedule.value,
      }),
    );
  };

  const stats = computed(() => {
    const today = todayISO();
    const lowStockItems = inventory.value.filter((item) => item.quantity <= item.minQuantity).length;

    return {
      totalMembers: members.value.length,
      activeMembers: members.value.filter((member) => member.status === 'Activa').length,
      attendanceToday: attendance.value.filter((entry) => entry.date === today).length,
      inventoryItems: inventory.value.length,
      lowStockItems,
      attendanceRate: members.value.length
        ? Math.round(
            members.value.reduce((sum, member) => sum + Number(member.attendanceRate || 0), 0) /
              members.value.length,
          )
        : 0,
    };
  });

  const recentAttendance = computed(() =>
    [...attendance.value].sort((a, b) => `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`)).slice(0, 10),
  );

  const attendanceAnalytics = computed(() => {
    const today = todayISO();
    const weekStart = dateFromISO(today);
    weekStart.setDate(weekStart.getDate() - 6);
    const monthStart = dateFromISO(today);
    monthStart.setDate(1);

    const countsByDate = attendance.value.reduce((accumulator, entry) => {
      accumulator[entry.date] = (accumulator[entry.date] || 0) + 1;
      return accumulator;
    }, {});

    const totalInPeriod = (startDate) =>
      attendance.value.filter((entry) => dateFromISO(entry.date).getTime() >= startDate.getTime()).length;

    return {
      today: countsByDate[today] || 0,
      week: totalInPeriod(weekStart),
      month: totalInPeriod(monthStart),
      countsByDate,
    };
  });

  const activePlans = computed(() => planCatalog.value.filter((plan) => plan.active));

  const activePromotions = computed(() =>
    promotions.value.filter((promotion) => promotion.active && (!promotion.validUntil || promotion.validUntil >= todayISO())),
  );

  const membershipAlerts = computed(() =>
    members.value
      .filter((member) => member.status === 'Activa' && member.membershipEnd)
      .map((member) => ({
        ...member,
        daysUntilExpiry: daysUntilISO(member.membershipEnd),
      }))
      .filter((member) => member.daysUntilExpiry <= MEMBER_ALERT_DAYS),
  );

  const lowStockInventory = computed(() =>
    inventory.value.filter((item) => item.quantity <= item.minQuantity),
  );

  const searchMembers = (query) => {
    const normalizedQuery = query?.trim().toLowerCase() || '';
    if (!normalizedQuery) {
      return members.value;
    }

    return members.value.filter((member) =>
      [member.dni, member.internalCode, member.name, member.email, member.phone, member.plan, member.status]
        .join(' ')
        .toLowerCase()
        .includes(normalizedQuery),
    );
  };

  const getPlanById = (planId) => planCatalog.value.find((plan) => plan.id === planId) || null;

  const getPromotionById = (promotionId) => promotions.value.find((promotion) => promotion.id === promotionId) || null;

  const isMembershipActive = (member, referenceDate = todayISO()) =>
    Boolean(member) && member.status === 'Activa' && (!member.membershipEnd || member.membershipEnd >= referenceDate);

  const isMembershipExpiringSoon = (member) => Boolean(member?.membershipEnd) && daysUntilISO(member.membershipEnd) <= MEMBER_ALERT_DAYS;

  const logMemberEvent = (memberId, event) => {
    const index = members.value.findIndex((entry) => entry.id === memberId);
    if (index < 0) return null;

    const entry = {
      id: event.id || `history-${Date.now()}`,
      at: event.at || nowISO(),
      ...event,
    };

    const member = members.value[index];
    members.value[index] = {
      ...member,
      changeHistory: [entry, ...(member.changeHistory || [])].slice(0, 20),
    };

    persist();
    return entry;
  };

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
      (!promotion.validUntil || promotion.validUntil >= todayISO()) &&
      (!promotion.appliesTo?.length || promotion.appliesTo.includes(planId))
    ) {
      discountAmount = promotion.discountType === 'fixed' ? Number(promotion.discountValue || 0) : Math.round((Number(plan.price) * Number(promotion.discountValue || 0)) / 100);
    }

    return {
      plan,
      promotion,
      basePrice: Number(plan.price || 0),
      discountAmount,
      finalPrice: Math.max(0, Number(plan.price || 0) - discountAmount),
    };
  };

  const upsertPlan = (payload) => {
    const plan = {
      id: payload.id || `plan-${Date.now()}`,
      name: payload.name?.trim() || 'Sin nombre',
      durationMonths: Number(payload.durationMonths ?? 1),
      price: Number(payload.price ?? 0),
      description: payload.description || '',
      active: payload.active !== false,
    };

    const index = planCatalog.value.findIndex((entry) => entry.id === plan.id);
    if (index >= 0) {
      planCatalog.value[index] = plan;
    } else {
      planCatalog.value.unshift(plan);
    }

    persist();
    return plan;
  };

  const upsertPromotion = (payload) => {
    const promotion = {
      id: payload.id || `promo-${Date.now()}`,
      name: payload.name?.trim() || 'Sin nombre',
      discountType: payload.discountType || 'percent',
      discountValue: Number(payload.discountValue ?? 0),
      appliesTo: Array.isArray(payload.appliesTo) ? payload.appliesTo : [],
      active: payload.active !== false,
      validUntil: payload.validUntil || '',
      note: payload.note || '',
    };

    const index = promotions.value.findIndex((entry) => entry.id === promotion.id);
    if (index >= 0) {
      promotions.value[index] = promotion;
    } else {
      promotions.value.unshift(promotion);
    }

    persist();
    return promotion;
  };

  const assignPlanToMember = (memberId, planId, promotionId = '', note = 'Asignación de membresía') => {
    const index = members.value.findIndex((entry) => entry.id === memberId);
    if (index < 0) {
      throw new Error('Miembro no encontrado');
    }

    const member = members.value[index];
    const { plan, promotion, basePrice, discountAmount, finalPrice } = calculatePlanCharge(planId, promotionId);
    const startDate = member.membershipEnd && member.membershipEnd > todayISO() ? member.membershipEnd : todayISO();
    const endDate = addMonthsISO(startDate, plan.durationMonths || planDurationById(planId));
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

    members.value[index] = {
      ...member,
      plan: plan.name,
      planId: plan.id,
      membershipStart: startDate,
      membershipEnd: endDate,
      membershipPrice: finalPrice,
      status: member.status === 'Bloqueada' ? member.status : 'Activa',
      membershipHistory: [historyEntry, ...(member.membershipHistory || [])].slice(0, 20),
    };

    logMemberEvent(memberId, {
      action: eventType,
      fields: ['plan', 'planId', 'membershipStart', 'membershipEnd', 'membershipPrice', 'status'],
      note,
    });

    persist();
    return members.value[index];
  };

  const renewMembership = (memberId, planId = '', promotionId = '', note = 'Renovación de membresía') => {
    const member = memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    return assignPlanToMember(memberId, planId || member.planId || 'plan-monthly', promotionId, note);
  };

  const attendanceByMemberRange = (memberId, fromDate = '', toDate = '') =>
    attendance.value.filter((entry) => {
      const matchesMember = entry.memberId === memberId;
      const afterStart = !fromDate || entry.date >= fromDate;
      const beforeEnd = !toDate || entry.date <= toDate;
      return matchesMember && afterStart && beforeEnd;
    });

  const memberSchedules = (memberId) => memberById(memberId)?.schedules || [];

  const assignMemberSchedule = (memberId, payload) => {
    const index = members.value.findIndex((entry) => entry.id === memberId);
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

    const member = members.value[index];
    members.value[index] = {
      ...member,
      schedules: [slot, ...(member.schedules || [])].slice(0, 20),
    };

    logMemberEvent(memberId, {
      action: 'Horario asignado',
      fields: ['schedules'],
      note: `${slot.day} ${slot.startTime}-${slot.endTime}`,
    });

    persist();
    return slot;
  };

  const userAttendance = (email) => {
    const member = members.value.find((entry) => entry.email === email);
    if (!member) return [];

    return attendance.value.filter((entry) => entry.memberId === member.id).slice(0, 10);
  };

  const memberByEmail = (email) => members.value.find((member) => member.email === email) || null;

  const memberById = (id) => members.value.find((member) => member.id === id) || null;

  const activeAttendancePass = (memberId) => {
    const pass =
      [...attendancePasses.value]
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
    const member = memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    if (!isMembershipActive(member)) {
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

    attendancePasses.value = attendancePasses.value.map((entry) => {
      if (entry.memberId === memberId && entry.status === 'active' && !isPassExpired(entry)) {
        return { ...entry, status: 'expired' };
      }

      return entry;
    });

    attendancePasses.value = [pass, ...attendancePasses.value];
    persist();
    return {
      ...pass,
      qrPayload: getPassPayload(pass),
    };
  };

  const redeemAttendancePass = (input, type = 'Entrada', note = '') => {
    const code = parsePassInput(input);
    if (!code) {
      throw new Error('Ingresa un código o QR válido');
    }

    const pass = attendancePasses.value.find((entry) => entry.code === code);
    if (!pass) {
      throw new Error('Código no encontrado');
    }

    if (pass.status !== 'active') {
      throw new Error('El código ya fue utilizado');
    }

    if (isPassExpired(pass)) {
      pass.status = 'expired';
      persist();
      throw new Error('El código expiró');
    }

    const record = recordAttendance(pass.memberId, type, note);
    pass.status = 'redeemed';
    pass.redeemedAt = nowISO();
    pass.redeemedAttendanceId = record.id;
    persist();

    return {
      record,
      pass: {
        ...pass,
        qrPayload: getPassPayload(pass),
      },
    };
  };

  const upsertMember = (payload) => {
    const existingMember = members.value.find((entry) => entry.id === payload.id);
    const baseMembershipStart = payload.membershipStart || existingMember?.membershipStart || payload.joinedAt || todayISO();
    const resolvedPlanId = payload.planId || existingMember?.planId || 'plan-monthly';

    const member = {
      id: payload.id || `member-${Date.now()}`,
      name: payload.name?.trim() || existingMember?.name || 'Sin nombre',
      dni: payload.dni?.trim() || existingMember?.dni || '',
      internalCode: payload.internalCode?.trim() || existingMember?.internalCode || `GYM-${String(payload.id || Date.now()).slice(-4).toUpperCase()}`,
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
      status: payload.status || existingMember?.status || 'Activa',
      joinedAt: payload.joinedAt || existingMember?.joinedAt || todayISO(),
      attendanceRate: Number(payload.attendanceRate ?? existingMember?.attendanceRate ?? 0),
      membershipHistory: Array.isArray(payload.membershipHistory) ? payload.membershipHistory : existingMember?.membershipHistory || [],
      changeHistory: Array.isArray(payload.changeHistory) ? payload.changeHistory : existingMember?.changeHistory || [],
      schedules: Array.isArray(payload.schedules) ? payload.schedules : existingMember?.schedules || [],
    };

    const index = members.value.findIndex((entry) => entry.id === member.id);
    if (index >= 0) {
      members.value[index] = member;
    } else {
      members.value.unshift(member);
    }
    persist();
    return member;
  };

  const deleteMember = (id) => {
    members.value = members.value.filter((member) => member.id !== id);
    attendance.value = attendance.value.filter((entry) => entry.memberId !== id);
    attendancePasses.value = attendancePasses.value.filter((pass) => pass.memberId !== id);
    persist();
  };

  const recordAttendance = (memberId, type = 'Entrada', note = '') => {
    const member = members.value.find((entry) => entry.id === memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    if (!isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía vigente');
    }

    const record = {
      id: `attendance-${Date.now()}`,
      memberId,
      memberName: member.name,
      type,
      time: nowTime(),
      date: todayISO(),
      note,
    };

    attendance.value.unshift(record);
    persist();
    return record;
  };

  const pruneExpiredAttendancePasses = () => {
    let changed = false;

    attendancePasses.value = attendancePasses.value.map((pass) => {
      if (pass.status === 'active' && isPassExpired(pass)) {
        changed = true;
        return { ...pass, status: 'expired' };
      }

      return pass;
    });

    if (changed) {
      persist();
    }
  };

  pruneExpiredAttendancePasses();

  const upsertInventoryItem = (payload) => {
    const existingItem = inventory.value.find((entry) => entry.id === payload.id);
    const item = {
      id: payload.id || `item-${Date.now()}`,
      inventoryCode: payload.inventoryCode?.trim() || existingItem?.inventoryCode || generateInventoryCode(),
      name: payload.name?.trim() || 'Sin nombre',
      category: payload.category || 'General',
      quantity: Number(payload.quantity ?? 0),
      minQuantity: Number(payload.minQuantity ?? 0),
      location: payload.location || 'Sin ubicación',
      status: payload.status || 'Disponible',
      observations: payload.observations || '',
    };

    const index = inventory.value.findIndex((entry) => entry.id === item.id);
    if (index >= 0) {
      inventory.value[index] = item;
    } else {
      inventory.value.unshift(item);
    }
    persist();
    return item;
  };

  const deleteInventoryItem = (id) => {
    inventory.value = inventory.value.filter((item) => item.id !== id);
    persist();
  };

  return {
    members,
    attendance,
    attendancePasses,
    planCatalog,
    promotions,
    inventory,
    schedule,
    stats,
    recentAttendance,
    attendanceAnalytics,
    activePlans,
    activePromotions,
    membershipAlerts,
    lowStockInventory,
    searchMembers,
    getPlanById,
    getPromotionById,
    isMembershipActive,
    isMembershipExpiringSoon,
    calculatePlanCharge,
    upsertPlan,
    upsertPromotion,
    assignPlanToMember,
    renewMembership,
    attendanceByMemberRange,
    memberSchedules,
    assignMemberSchedule,
    userAttendance,
    memberByEmail,
    memberById,
    activeAttendancePass,
    createAttendancePass,
    redeemAttendancePass,
    upsertMember,
    deleteMember,
    recordAttendance,
    upsertInventoryItem,
    deleteInventoryItem,
  };
});
