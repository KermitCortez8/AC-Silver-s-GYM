import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { APP_CONFIG } from '../config/appConfig';
import { apiDelete, apiGet, apiPost } from '../services/apiClient';
import { useAuthStore } from './authStore';

const PASS_STORAGE_KEY = 'gym_frontend_attendance_passes_v2';
const PASS_EXPIRY_MINUTES = 10;
const ALERT_DAYS = 7;
const WEEK_DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

const todayISO = () => new Date().toISOString().slice(0, 10);
const nowISO = () => new Date().toISOString();
const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const safeNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const addDays = (dateISO, days) => {
  const date = new Date(`${dateISO}T00:00:00`);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
};

const addMonths = (dateISO, months) => {
  const date = new Date(`${dateISO}T00:00:00`);
  date.setMonth(date.getMonth() + months);
  return date.toISOString().slice(0, 10);
};

const readPasses = () => {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    return JSON.parse(window.localStorage.getItem(PASS_STORAGE_KEY) || '[]');
  } catch (error) {
    return [];
  }
};

const savePasses = (passes) => {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(PASS_STORAGE_KEY, JSON.stringify(passes));
};

const normalizeClient = (client = {}) => ({
  ...client,
  id_cliente: safeNumber(client.id_cliente),
  estado: client.estado !== false,
  fecha_registro: client.fecha_registro || todayISO(),
});

const normalizeUser = (user = {}) => ({
  ...user,
  id_usuario: safeNumber(user.id_usuario),
  estado: user.estado !== false,
});

const normalizePlan = (plan = {}) => ({
  ...plan,
  id_pm: safeNumber(plan.id_pm),
  precio: safeNumber(plan.precio),
});

const normalizeMembership = (membership = {}) => ({
  ...membership,
  id_membresia: safeNumber(membership.id_membresia),
  id_cliente: safeNumber(membership.id_cliente),
  id_pm: safeNumber(membership.id_pm),
});

const normalizeInventory = (item = {}) => ({
  ...item,
  id_item: safeNumber(item.id_item),
  cantidad_stock: safeNumber(item.cantidad_stock),
  stock_minimo: safeNumber(item.stock_minimo),
});

const normalizeRoutine = (routine = {}) => ({
  ...routine,
  id_rutina: safeNumber(routine.id_rutina),
});

const normalizeSchedule = (schedule = {}) => ({
  ...schedule,
  id_horario: safeNumber(schedule.id_horario),
  id_cliente: safeNumber(schedule.id_cliente),
  id_rutina: safeNumber(schedule.id_rutina),
});

const normalizeAttendance = (entry = {}) => ({
  ...entry,
  id_asistencia: safeNumber(entry.id_asistencia),
  id_cliente: safeNumber(entry.id_cliente),
});

const normalizeTicket = (ticket = {}) => ({
  ...ticket,
  id_ticket: safeNumber(ticket.id_ticket),
  id_cliente: safeNumber(ticket.id_cliente),
  id_usuario: safeNumber(ticket.id_usuario),
});

const clientName = (client) => `${client?.nombres || ''} ${client?.apellidos || ''}`.trim() || 'Sin nombre';

const parseMemberId = (value) => safeNumber(String(value || '').replace(/^cliente-/, ''));
const parsePlanId = (value) => safeNumber(String(value || '').replace(/^pm-/, ''));
const membershipDurationMonths = (plan) => safeNumber(String(plan?.duracion || '').match(/\d+/)?.[0], 1);

const buildPassPayload = (pass) =>
  JSON.stringify({
    gym: 'AC-Silver-s-GYM',
    passId: pass.id,
    memberId: pass.memberId,
    code: pass.code,
    issuedAt: pass.issuedAt,
    expiresAt: pass.expiresAt,
  });

const buildMemberCard = (client, users, memberships, plans, schedules, attendance) => {
  const clientId = safeNumber(client.id_cliente);
  const clientMemberships = memberships
    .filter((membership) => safeNumber(membership.id_cliente) === clientId)
    .sort((left, right) => String(right.fecha_inicio || '').localeCompare(String(left.fecha_inicio || '')));
  const latestMembership = clientMemberships[0] || null;
  const plan = latestMembership ? plans.find((entry) => safeNumber(entry.id_pm) === safeNumber(latestMembership.id_pm)) || null : null;
  const linkedUser = users.find(
    (user) => String(user.dni || '').trim() === String(client.dni || '').trim() || String(user.email || '').toLowerCase() === String(client.email || '').toLowerCase(),
  );
  const clientAttendance = attendance.filter((entry) => safeNumber(entry.id_cliente) === clientId);
  const clientSchedules = schedules.filter((entry) => safeNumber(entry.id_cliente) === clientId);

  return {
    id: `cliente-${clientId}`,
    id_cliente: clientId,
    name: clientName(client),
    dni: client.dni || '',
    internalCode: `CL-${String(clientId).padStart(4, '0')}`,
    email: client.email || '',
    phone: client.telefono || '',
    role: linkedUser?.rol || 'user',
    plan: plan?.nombre_plan || 'Sin plan',
    planId: plan ? `pm-${plan.id_pm}` : '',
    membershipStart: latestMembership?.fecha_inicio || client.fecha_registro || todayISO(),
    membershipEnd: latestMembership?.fecha_fin || '',
    membershipPrice: plan?.precio || 0,
    status: client.estado ? 'Activa' : 'Inactiva',
    joinedAt: client.fecha_registro || '',
    attendanceRate: clientAttendance.length ? Math.min(100, clientAttendance.length * 10) : 0,
    membershipHistory: clientMemberships.map((entry) => ({
      id: `membership-${entry.id_membresia}`,
      type: entry.estado || 'Activa',
      at: entry.fecha_inicio || nowISO(),
      planId: `pm-${entry.id_pm}`,
      startDate: entry.fecha_inicio || '',
      endDate: entry.fecha_fin || '',
      price: plan?.precio || 0,
      discount: 0,
      note: entry.estado || 'Membresía',
    })),
    changeHistory: [],
    schedules: clientSchedules.map((entry) => ({
      id: `schedule-${entry.id_horario}`,
      day: entry.dia_semana,
      startTime: entry.hora_inicio,
      endTime: entry.hora_fin,
      note: `Rutina ${entry.id_rutina}`,
    })),
  };
};

const staticSchedule = () =>
  WEEK_DAYS.map((day, index) => ({
    day,
    hours: index === 5 ? '08:00 - 18:00' : index === 6 ? '09:00 - 14:00' : '06:00 - 22:00',
    focus: index === 0 ? 'Piernas y glúteos' : index === 1 ? 'Espalda y core' : index === 2 ? 'Pecho y hombros' : index === 3 ? 'Cardio y movilidad' : index === 4 ? 'Full body' : index === 5 ? 'Clases dirigidas' : 'Mantenimiento',
  }));

export const useGymStore = defineStore('gym', () => {
  const loading = ref(false);
  const error = ref('');
  const summary = ref({ stats: {}, flujos: {}, alertas: [] });

  const users = ref([]);
  const clients = ref([]);
  const plans = ref([]);
  const memberships = ref([]);
  const attendance = ref([]);
  const inventory = ref([]);
  const movements = ref([]);
  const tickets = ref([]);
  const routines = ref([]);
  const schedules = ref([]);
  const promotions = ref([]);
  const attendancePasses = ref(readPasses());

  const auth = useAuthStore();
  const authToken = computed(() => auth.token || '');
  const hasBackend = computed(() => Boolean(APP_CONFIG.authApiBaseUrl));

  const persistPasses = () => savePasses(attendancePasses.value);
  const memberCards = computed(() => clients.value.map((client) => buildMemberCard(client, users.value, memberships.value, plans.value, schedules.value, attendance.value)));

  const stats = computed(() => {
    const backendStats = summary.value.stats || {};
    return {
      totalMembers: safeNumber(backendStats.totalMembers, clients.value.length),
      activeMembers: safeNumber(backendStats.activeMembers, clients.value.filter((client) => client.estado).length),
      attendanceToday: safeNumber(backendStats.attendanceToday, attendance.value.filter((entry) => entry.fecha === todayISO()).length),
      inventoryItems: safeNumber(backendStats.inventoryItems, inventory.value.length),
      lowStockItems: safeNumber(backendStats.lowStockItems, inventory.value.filter((item) => safeNumber(item.cantidad_stock) <= safeNumber(item.stock_minimo)).length),
      attendanceRate: safeNumber(backendStats.attendanceRate, 0),
    };
  });

  const recentAttendance = computed(() =>
    [...attendance.value]
      .sort((left, right) => `${right.fecha || ''} ${right.hora || ''}`.localeCompare(`${left.fecha || ''} ${left.hora || ''}`))
      .slice(0, 10)
      .map((entry) => {
        const client = clients.value.find((item) => safeNumber(item.id_cliente) === safeNumber(entry.id_cliente));
        return {
          id: `attendance-${entry.id_asistencia}`,
          memberName: client ? clientName(client) : `Cliente #${entry.id_cliente}`,
          memberCode: `CL-${String(entry.id_cliente).padStart(4, '0')}`,
          type: entry.validacion === false ? 'Revisión' : 'Entrada',
          time: entry.hora || '',
          date: entry.fecha || '',
          exercise: entry.validacion === false ? 'Validación manual' : 'Acceso registrado',
          note: entry.validacion === false ? 'Requiere verificación' : 'Asistencia confirmada',
        };
      }),
  );

  const attendanceAnalytics = computed(() => {
    const countsByDate = attendance.value.reduce((accumulator, entry) => {
      const key = entry.fecha || '';
      accumulator[key] = (accumulator[key] || 0) + 1;
      return accumulator;
    }, {});

    return {
      today: countsByDate[todayISO()] || 0,
      week: attendance.value.filter((entry) => (entry.fecha || '') >= addDays(todayISO(), -6)).length,
      month: attendance.value.filter((entry) => (entry.fecha || '') >= `${todayISO().slice(0, 8)}01`).length,
      countsByDate,
    };
  });

  const activePlans = computed(() => plans.value.map((plan) => ({
    id: `pm-${plan.id_pm}`,
    name: plan.nombre_plan,
    durationMonths: membershipDurationMonths(plan),
    price: safeNumber(plan.precio),
    description: plan.duracion || '',
    active: true,
  })));

  const activePromotions = computed(() => promotions.value);
  const lowStockInventory = computed(() => inventory.value.filter((item) => safeNumber(item.cantidad_stock) <= safeNumber(item.stock_minimo)));
  const membershipAlerts = computed(() =>
    memberCards.value
      .filter((member) => member.membershipEnd && member.status === 'Activa')
      .map((member) => ({
        ...member,
        daysUntilExpiry: Math.ceil((new Date(`${member.membershipEnd}T00:00:00`).getTime() - new Date(`${todayISO()}T00:00:00`).getTime()) / (1000 * 60 * 60 * 24)),
      }))
      .filter((member) => member.daysUntilExpiry <= ALERT_DAYS),
  );

  const schedule = computed(() => {
    if (!schedules.value.length) {
      return staticSchedule();
    }

    return WEEK_DAYS.map((day) => {
      const daySchedule = schedules.value.find((entry) => String(entry.dia_semana || '').toLowerCase() === String(day).toLowerCase());
      const routine = daySchedule ? routines.value.find((entry) => safeNumber(entry.id_rutina) === safeNumber(daySchedule.id_rutina)) : null;

      return {
        day,
        hours: daySchedule ? `${daySchedule.hora_inicio || '--:--'} - ${daySchedule.hora_fin || '--:--'}` : 'Sin horario',
        focus: routine?.nombre_rutina || (daySchedule ? `Rutina ${daySchedule.id_rutina}` : 'Sin rutina asignada'),
      };
    });
  });

  const loadAll = async () => {
    if (!hasBackend.value) {
      return;
    }

    loading.value = true;
    error.value = '';

    try {
      const [summaryData, usersData, clientsData, plansData, membershipsData, attendanceData, inventoryData, movementsData, ticketsData, routinesData, schedulesData] = await Promise.all([
        apiGet('/gym/summary', authToken.value),
        apiGet('/usuarios', authToken.value),
        apiGet('/clientes', authToken.value),
        apiGet('/planes-membresia', authToken.value),
        apiGet('/membresias', authToken.value),
        apiGet('/asistencia', authToken.value),
        apiGet('/inventario', authToken.value),
        apiGet('/inventario/movimientos', authToken.value),
        apiGet('/gym/tickets', authToken.value),
        apiGet('/gym/rutinas', authToken.value),
        apiGet('/gym/horarios', authToken.value),
      ]);

      summary.value = summaryData || { stats: {}, flujos: {}, alertas: [] };
      users.value = Array.isArray(usersData) ? usersData.map(normalizeUser) : [];
      clients.value = Array.isArray(clientsData) ? clientsData.map(normalizeClient) : [];
      plans.value = Array.isArray(plansData) ? plansData.map(normalizePlan) : [];
      memberships.value = Array.isArray(membershipsData) ? membershipsData.map(normalizeMembership) : [];
      attendance.value = Array.isArray(attendanceData) ? attendanceData.map(normalizeAttendance) : [];
      inventory.value = Array.isArray(inventoryData) ? inventoryData.map(normalizeInventory) : [];
      movements.value = Array.isArray(movementsData) ? movementsData : [];
      tickets.value = Array.isArray(ticketsData) ? ticketsData.map(normalizeTicket) : [];
      routines.value = Array.isArray(routinesData) ? routinesData.map(normalizeRoutine) : [];
      schedules.value = Array.isArray(schedulesData) ? schedulesData.map(normalizeSchedule) : [];
      persistPasses();
    } catch (fetchError) {
      error.value = fetchError instanceof Error ? fetchError.message : 'No se pudo cargar el backend';
      throw fetchError;
    } finally {
      loading.value = false;
    }
  };

  const refresh = async () => {
    if (!hasBackend.value) {
      return;
    }

    await loadAll();
  };

  const searchMembers = (query) => {
    const normalizedQuery = String(query || '').trim().toLowerCase();
    if (!normalizedQuery) {
      return memberCards.value;
    }

    return memberCards.value.filter((member) =>
      [member.name, member.dni, member.email, member.phone, member.internalCode, member.plan, member.status].join(' ').toLowerCase().includes(normalizedQuery),
    );
  };

  const memberById = (id) => memberCards.value.find((member) => member.id === id || member.id_cliente === parseMemberId(id)) || null;
  const memberByEmail = (email) => memberCards.value.find((member) => String(member.email || '').toLowerCase() === String(email || '').toLowerCase()) || null;
  const memberByInternalCode = (code) => memberCards.value.find((member) => String(member.internalCode || '').trim().toUpperCase() === String(code || '').trim().toUpperCase()) || null;
  const memberSchedules = (memberId) => schedules.value.filter((entry) => safeNumber(entry.id_cliente) === parseMemberId(memberId));
  const getPlanById = (planId) => plans.value.find((plan) => safeNumber(plan.id_pm) === parsePlanId(planId)) || null;
  const getPromotionById = (promotionId) => promotions.value.find((promotion) => String(promotion.id) === String(promotionId)) || null;

  const isMembershipActive = (member, referenceDate = todayISO()) => {
    const card = typeof member === 'string' || typeof member === 'number' ? memberById(member) : member;
    if (!card) {
      return false;
    }

    const clientMembership = memberships.value.find((membership) => safeNumber(membership.id_cliente) === safeNumber(card.id_cliente) && String(membership.estado || '').toLowerCase() === 'activa');
    if (!clientMembership) {
      return false;
    }

    return (!clientMembership.fecha_inicio || clientMembership.fecha_inicio <= referenceDate) && (!clientMembership.fecha_fin || clientMembership.fecha_fin >= referenceDate);
  };

  const isMembershipExpiringSoon = (member) => Boolean(member?.membershipEnd) && member.membershipEnd <= addDays(todayISO(), ALERT_DAYS);

  const calculatePlanCharge = (planId) => {
    const plan = getPlanById(planId);
    if (!plan) {
      throw new Error('Plan no encontrado');
    }

    return {
      plan: {
        id: `pm-${plan.id_pm}`,
        name: plan.nombre_plan,
        durationMonths: membershipDurationMonths(plan),
        price: safeNumber(plan.precio),
      },
      promotion: null,
      basePrice: safeNumber(plan.precio),
      discountAmount: 0,
      finalPrice: safeNumber(plan.precio),
    };
  };

  const upsertPlan = async (payload) => {
    const body = {
      id_pm: payload.id_pm ? safeNumber(payload.id_pm) : undefined,
      nombre_plan: payload.nombre_plan || payload.name || 'Sin nombre',
      duracion: payload.duracion || `${safeNumber(payload.durationMonths, 1)} mes(es)`,
      precio: safeNumber(payload.precio ?? payload.price),
    };

    const saved = await apiPost('/planes-membresia', body, authToken.value);
    await refresh();
    return saved;
  };

  const upsertPromotion = async (payload) => {
    const promotion = {
      id: payload.id || `promo-${Date.now()}`,
      name: payload.name || 'Promoción',
      discountType: payload.discountType || 'percent',
      discountValue: safeNumber(payload.discountValue),
      appliesTo: Array.isArray(payload.appliesTo) ? payload.appliesTo : [],
      active: payload.active !== false,
      validUntil: payload.validUntil || '',
      note: payload.note || '',
    };

    const index = promotions.value.findIndex((item) => item.id === promotion.id);
    if (index >= 0) {
      promotions.value[index] = promotion;
    } else {
      promotions.value.unshift(promotion);
    }

    return promotion;
  };

  const upsertUsuario = async (payload) => {
    const saved = await apiPost('/usuarios', payload, authToken.value);
    await refresh();
    return saved;
  };

  const deleteUsuario = async (idUsuario) => {
    await apiDelete(`/usuarios/${idUsuario}`, authToken.value);
    await refresh();
  };

  const upsertCliente = async (payload) => {
    const body = {
      id_cliente: payload.id_cliente ? safeNumber(payload.id_cliente) : undefined,
      nombres: payload.nombres || payload.name?.split(' ')[0] || 'Sin nombre',
      apellidos: payload.apellidos || payload.name?.split(' ').slice(1).join(' ') || '',
      dni: payload.dni || '',
      telefono: payload.telefono || payload.phone || '',
      email: payload.email || '',
      fecha_registro: payload.fecha_registro || payload.joinedAt || todayISO(),
      estado: payload.estado !== false,
    };

    const saved = await apiPost('/clientes', body, authToken.value);
    await refresh();
    return saved;
  };

  const deleteCliente = async (idCliente) => {
    await apiDelete(`/clientes/${idCliente}`, authToken.value);
    await refresh();
  };

  const registerClienteMembresia = async (payload) => {
    const saved = await apiPost('/registro-cliente-membresia', payload, authToken.value);
    await refresh();
    return saved;
  };

  const upsertMembership = async (payload) => {
    const saved = await apiPost('/membresias', payload, authToken.value);
    await refresh();
    return saved;
  };

  const assignPlanToMember = async (memberId, planId, promotionId = '', note = 'Asignación de membresía') => {
    const member = memberById(memberId);
    const plan = getPlanById(planId);

    if (!member || !plan) {
      throw new Error('No se pudo asignar la membresía');
    }

    const startDate = member.membershipEnd && member.membershipEnd > todayISO() ? member.membershipEnd : todayISO();
    const endDate = addMonths(startDate, membershipDurationMonths(plan));

    return registerClienteMembresia({
      cliente: {
        id_cliente: member.id_cliente,
        nombres: member.name.split(' ')[0] || member.name,
        apellidos: member.name.split(' ').slice(1).join(' '),
        dni: member.dni,
        telefono: member.phone,
        email: member.email,
        fecha_registro: member.joinedAt || todayISO(),
        estado: member.status !== 'Inactiva',
      },
      id_pm: plan.id_pm,
      fecha_inicio: startDate,
      fecha_fin: endDate,
      note,
      promotionId,
    });
  };

  const renewMembership = async (memberId, planId = '', promotionId = '', note = 'Renovación de membresía') => {
    const member = memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    return assignPlanToMember(member.id, planId || member.planId || 'pm-1', promotionId, note);
  };

  const attendanceByMemberRange = (memberId, fromDate = '', toDate = '') =>
    attendance.value.filter((entry) => {
      const matchesMember = safeNumber(entry.id_cliente) === parseMemberId(memberId);
      const afterStart = !fromDate || entry.fecha >= fromDate;
      const beforeEnd = !toDate || entry.fecha <= toDate;
      return matchesMember && afterStart && beforeEnd;
    });

  const checkinById = async (idCliente) => {
    const saved = await apiPost('/asistencia/checkin', { id_cliente: safeNumber(idCliente) }, authToken.value);
    await refresh();
    return saved;
  };

  const checkinByDni = async (dni) => {
    const saved = await apiPost('/asistencia/checkin-dni', { dni }, authToken.value);
    await refresh();
    return saved;
  };

  const recordAttendanceByCode = async (internalCode, exercise = '', type = 'Entrada', note = '') => {
    const member = memberByInternalCode(internalCode);
    if (!member) {
      throw new Error('Código no encontrado');
    }

    const record = await checkinById(member.id_cliente);
    return {
      id: `attendance-${Date.now()}`,
      memberId: member.id,
      memberName: member.name,
      memberCode: member.internalCode,
      type,
      exercise: exercise || '',
      time: record?.hora || nowTime(),
      date: record?.fecha || todayISO(),
      note,
    };
  };

  const recordAttendance = async (memberId, type = 'Entrada', note = '') => {
    const member = memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    const record = await checkinById(member.id_cliente);
    return {
      id: `attendance-${Date.now()}`,
      memberId: member.id,
      memberName: member.name,
      memberCode: member.internalCode,
      type,
      exercise: note || 'Sin ejercicio',
      time: record?.hora || nowTime(),
      date: record?.fecha || todayISO(),
      note,
    };
  };

  const upsertInventoryItem = async (payload) => {
    const body = {
      id_item: payload.id_item ? safeNumber(payload.id_item) : undefined,
      nombre_item: payload.nombre_item || payload.name || 'Sin nombre',
      tipo: payload.tipo || payload.category || 'General',
      cantidad_stock: safeNumber(payload.cantidad_stock ?? payload.quantity),
      stock_minimo: safeNumber(payload.stock_minimo ?? payload.minQuantity),
      estado: payload.estado || payload.status || 'Operativo',
      n_activo: payload.n_activo ?? 1,
    };

    const saved = await apiPost('/inventario', body, authToken.value);
    await refresh();
    return saved;
  };

  const deleteInventoryItem = async (idItem) => {
    await apiDelete(`/inventario/${idItem}`, authToken.value);
    await refresh();
  };

  const registrarMovimientoToServer = async (payload) => {
    const saved = await apiPost('/inventario/movimientos', payload, authToken.value);
    await refresh();
    return saved;
  };

  const upsertTicket = async (payload) => {
    const saved = await apiPost('/gym/tickets', payload, authToken.value);
    await refresh();
    return saved;
  };

  const upsertRutina = async (payload) => {
    const saved = await apiPost('/gym/rutinas', payload, authToken.value);
    await refresh();
    return saved;
  };

  const upsertHorario = async (payload) => {
    const saved = await apiPost('/gym/horarios', payload, authToken.value);
    await refresh();
    return saved;
  };

  const createAttendancePass = (memberId, expiresInMinutes = PASS_EXPIRY_MINUTES) => {
    const member = memberById(memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    if (!isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía activa');
    }

    const issuedAt = nowISO();
    const expiresAt = new Date(Date.now() + expiresInMinutes * 60 * 1000).toISOString();
    const pass = {
      id: `pass-${Date.now()}`,
      memberId: member.id,
      memberName: member.name,
      code: `${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`,
      issuedAt,
      expiresAt,
      status: 'active',
      redeemedAt: null,
      redeemedAttendanceId: null,
    };

    attendancePasses.value = attendancePasses.value.map((entry) => (entry.memberId === member.id && entry.status === 'active' ? { ...entry, status: 'expired' } : entry));
    attendancePasses.value = [pass, ...attendancePasses.value];
    persistPasses();

    return { ...pass, qrPayload: buildPassPayload(pass) };
  };

  const redeemAttendancePass = async (input, type = 'Entrada', note = '') => {
    const raw = String(input || '').trim();
    if (!raw) {
      throw new Error('Ingresa un código o QR válido');
    }

    let code = raw;
    try {
      const parsed = JSON.parse(raw);
      code = String(parsed.code || '').trim() || code;
    } catch (error) {
      // Mantener el valor crudo.
    }

    const pass = attendancePasses.value.find((entry) => entry.code === code);
    if (!pass) {
      throw new Error('Código no encontrado');
    }

    if (pass.status !== 'active') {
      throw new Error('El código ya fue utilizado');
    }

    if (new Date().getTime() > new Date(pass.expiresAt).getTime()) {
      pass.status = 'expired';
      persistPasses();
      throw new Error('El código expiró');
    }

    const record = await checkinById(parseMemberId(pass.memberId));
    pass.status = 'redeemed';
    pass.redeemedAt = nowISO();
    pass.redeemedAttendanceId = record?.id_asistencia || null;
    persistPasses();

    return { record, pass: { ...pass, qrPayload: buildPassPayload(pass) } };
  };

  const activeAttendancePass = (memberId) => {
    const member = memberById(memberId);
    if (!member) {
      return null;
    }

    const pass = [...attendancePasses.value]
      .filter((entry) => entry.memberId === member.id && entry.status === 'active' && new Date(entry.expiresAt).getTime() > Date.now())
      .sort((left, right) => new Date(right.issuedAt).getTime() - new Date(left.issuedAt).getTime())[0] || null;

    if (!pass) {
      return null;
    }

    return { ...pass, qrPayload: buildPassPayload(pass) };
  };

  const userAttendance = (email) => {
    const member = memberByEmail(email);
    if (!member) {
      return [];
    }

    return attendanceByMemberRange(member.id).slice(0, 10).map((entry) => ({
      id: `attendance-${entry.id_asistencia}`,
      memberId: member.id,
      memberName: member.name,
      memberCode: member.internalCode,
      type: entry.validacion === false ? 'Revisión' : 'Entrada',
      time: entry.hora || '',
      date: entry.fecha || '',
      exercise: entry.validacion === false ? 'Validación manual' : 'Acceso registrado',
      note: entry.validacion === false ? 'Requiere verificación' : 'Asistencia confirmada',
    }));
  };

  const upsertMember = async (payload) => {
    const clientPayload = {
      id_cliente: payload.id_cliente ? safeNumber(payload.id_cliente) : undefined,
      nombres: payload.nombres || payload.name?.split(' ')[0] || 'Sin nombre',
      apellidos: payload.apellidos || payload.name?.split(' ').slice(1).join(' ') || '',
      dni: payload.dni || '',
      telefono: payload.telefono || payload.phone || '',
      email: payload.email || '',
      fecha_registro: payload.fecha_registro || payload.joinedAt || todayISO(),
      estado: payload.estado !== false,
    };

    const savedClient = await upsertCliente(clientPayload);

    if (payload.planId || payload.id_pm || payload.fecha_inicio || payload.fecha_fin) {
      const idCliente = safeNumber(savedClient.id_cliente || clientPayload.id_cliente);
      await registerClienteMembresia({
        cliente: {
          id_cliente: idCliente,
          nombres: clientPayload.nombres,
          apellidos: clientPayload.apellidos,
          dni: clientPayload.dni,
          telefono: clientPayload.telefono,
          email: clientPayload.email,
          fecha_registro: clientPayload.fecha_registro,
          estado: clientPayload.estado,
        },
        id_pm: safeNumber(payload.id_pm || parsePlanId(payload.planId)),
        fecha_inicio: payload.fecha_inicio || todayISO(),
        fecha_fin: payload.fecha_fin || addMonths(payload.fecha_inicio || todayISO(), membershipDurationMonths(getPlanById(payload.planId) || plans.value[0] || {})),
      });
    }

    return savedClient;
  };

  const deleteMember = async (id) => {
    await deleteCliente(parseMemberId(id));
  };

  const fetchFromBackend = async () => {
    if (!hasBackend.value) {
      return;
    }

    loading.value = true;
    error.value = '';

    try {
      const [summaryData, usersData, clientsData, plansData, membershipsData, attendanceData, inventoryData, movementsData, ticketsData, routinesData, schedulesData] = await Promise.all([
        apiGet('/gym/summary', authToken.value),
        apiGet('/usuarios', authToken.value),
        apiGet('/clientes', authToken.value),
        apiGet('/planes-membresia', authToken.value),
        apiGet('/membresias', authToken.value),
        apiGet('/asistencia', authToken.value),
        apiGet('/inventario', authToken.value),
        apiGet('/inventario/movimientos', authToken.value),
        apiGet('/gym/tickets', authToken.value),
        apiGet('/gym/rutinas', authToken.value),
        apiGet('/gym/horarios', authToken.value),
      ]);

      summary.value = summaryData || { stats: {}, flujos: {}, alertas: [] };
      users.value = Array.isArray(usersData) ? usersData.map(normalizeUser) : [];
      clients.value = Array.isArray(clientsData) ? clientsData.map(normalizeClient) : [];
      plans.value = Array.isArray(plansData) ? plansData.map(normalizePlan) : [];
      memberships.value = Array.isArray(membershipsData) ? membershipsData.map(normalizeMembership) : [];
      attendance.value = Array.isArray(attendanceData) ? attendanceData.map(normalizeAttendance) : [];
      inventory.value = Array.isArray(inventoryData) ? inventoryData.map(normalizeInventory) : [];
      movements.value = Array.isArray(movementsData) ? movementsData : [];
      tickets.value = Array.isArray(ticketsData) ? ticketsData.map(normalizeTicket) : [];
      routines.value = Array.isArray(routinesData) ? routinesData.map(normalizeRoutine) : [];
      schedules.value = Array.isArray(schedulesData) ? schedulesData.map(normalizeSchedule) : [];
      persistPasses();
    } catch (fetchError) {
      error.value = fetchError instanceof Error ? fetchError.message : 'No se pudo cargar el backend';
      throw fetchError;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    summary,
    users,
    clients,
    plans,
    memberships,
    attendance,
    inventory,
    movements,
    tickets,
    routines,
    schedules,
    promotions,
    attendancePasses,
    members: memberCards,
    memberCards,
    stats,
    recentAttendance,
    attendanceAnalytics,
    activePlans,
    activePromotions,
    membershipAlerts,
    lowStockInventory,
    schedule,
    searchMembers,
    getPlanById,
    getPromotionById,
    isMembershipActive,
    isMembershipExpiringSoon,
    calculatePlanCharge,
    upsertPlan,
    upsertPromotion,
    upsertUsuario,
    deleteUsuario,
    upsertCliente,
    deleteCliente,
    upsertMembership,
    registerClienteMembresia,
    assignPlanToMember,
    renewMembership,
    attendanceByMemberRange,
    checkinById,
    checkinByDni,
    recordAttendanceByCode,
    recordAttendance,
    memberByInternalCode,
    memberSchedules,
    memberByEmail,
    memberById,
    activeAttendancePass,
    createAttendancePass,
    redeemAttendancePass,
    upsertMember,
    deleteMember,
    upsertInventoryItem,
    deleteInventoryItem,
    upsertInventory: upsertInventoryItem,
    deleteInventory: deleteInventoryItem,
    registrarMovimientoToServer,
    upsertTicket,
    upsertRutina,
    upsertHorario,
    userAttendance,
    loadAll: fetchFromBackend,
    fetchFromBackend,
    refresh,
  };
});