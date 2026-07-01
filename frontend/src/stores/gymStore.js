import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { APP_CONFIG } from '../config/appConfig';
import { useAuthStore } from './authStore';

const PASS_EXPIRY_MINUTES = 10;
const MEMBER_ALERT_DAYS = 7;
const PLAN_DURATION_MONTHS = {
  'plan-monthly': 1,
  'plan-quarterly': 3,
  'plan-annual': 12,
};

const seedState = () => ({
  planCatalog: [],
  promotions: [],
  members: [],
  users: [],
  attendance: [],
  attendancePasses: [],
  inventory: [],
  productos_tienda: [],
  storeOrders: [],
  cart: [],
  routines: [],
  schedule: [],
  serviceSchedules: [],
  enrollments: [],
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
  inventoryCode: item.inventoryCode || (item.n_activo ? `ACT-${String(item.n_activo).padStart(4, '0')}` : `INV-${String(item.id || Date.now()).slice(-4).toUpperCase()}`),
  n_activo: item.n_activo || item.assetNumber || '',
  unidad_venta: item.unidad_venta || item.unit || 'unidad',
  precio_venta: Number(item.precio_venta ?? item.salePrice ?? 0),
  minQuantity: Number(item.minQuantity ?? item.stock_minimo ?? 1),
});

const normalizeStoreOrder = (order = {}) => ({
  id: `pedido-${order.id_pedido || order.id || Date.now()}`,
  id_pedido: Number(order.id_pedido || order.id || Date.now()),
  id_cliente: order.id_cliente || null,
  cliente_nombre: order.cliente_nombre || order.nombre_cliente || order.customerName || 'Cliente',
  cliente_correo: order.cliente_correo || order.correo || order.customerEmail || '',
  cliente_dni: order.cliente_dni || order.dni || '',
  fecha_pedido: order.fecha_pedido || order.createdAt || nowISO(),
  metodo_pago: order.metodo_pago || order.paymentMethod || 'tarjeta',
  referencia_pago: order.referencia_pago || order.paymentReference || '',
  estado_pago: order.estado_pago || 'PAGADO',
  estado_pedido: order.estado_pedido || 'PENDIENTE',
  subtotal: Number(order.subtotal || 0),
  igv: Number(order.igv || 0),
  total: Number(order.total || 0),
  items: Array.isArray(order.items)
    ? order.items.map((item) => ({
        id_producto: Number(item.id_producto || 0),
        nombre_producto: item.nombre_producto || item.nombre || 'Producto',
        cantidad: Number(item.cantidad || 1),
        precio_unitario: Number(item.precio_unitario || item.precio || 0),
        subtotal: Number(item.subtotal || Number(item.precio_unitario || item.precio || 0) * Number(item.cantidad || 1)),
      }))
    : [],
});

const normalizeStoreProductFromBackend = (product = {}) => ({
  id: `producto-${product.id_producto}`,
  id_producto: product.id_producto,
  id_item: product.id_item || null,
  nombre: product.nombre_producto,
  descripcion: product.descripcion || '',
  categoria: product.categoria || 'General',
  unidad_venta: product.unidad_venta || 'unidad',
  precio: Number(product.precio_venta || 0),
  cantidad: Number(product.cantidad_stock || 0),
  minimo: Number(product.stock_minimo || 0),
  estado: product.estado || 'Disponible',
});

const normalizeUser = (user = {}) => {
  const email = String(user.correo || user.email || '').trim();
  const rawId = String(user.id_usuario || user.id || '').trim().toUpperCase();
  const nombre = String(user.nombre || '').trim();


  return {
    ...user,
    id_usuario: rawId.replace(/^USSG(\d+)$/, 'SGUS$1'),
    nombre,
    correo: email,
    email,
    telefono: String(user.telefono || '').trim(),
    dni: String(user.dni || '').trim(),
    rol: user.rol || 'staff',
    hasPassword: Boolean(user.hasPassword ?? user.has_password),
  };
};

const normalizeMember = (member = {}) => {
  const planId = member.planId || (member.plan === 'Anual' ? 'plan-annual' : member.plan === 'Trimestral' ? 'plan-quarterly' : 'plan-monthly');
  const baseDate = member.membershipStart || member.joinedAt || todayISO();
  const memberCode = member.id_cliente ? String(member.id_cliente) : String(member.internalCode || '').trim();

  return {
    ...member,
    dni: member.dni || '',
    internalCode: memberCode || String(member.id || Date.now()),
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

const normalizeAttendanceRecord = (entry = {}) => {
  const rawId = entry.id_cliente || entry.id_cliente_uid || entry.memberId || entry.memberCode || '';
  const idStr = rawId === null || rawId === undefined ? '' : String(rawId);
  return {
    ...entry,
    memberId: entry.memberId || idStr,
    memberCode: entry.memberCode || idStr,
    service: entry.service || entry.servicio || entry.servicio || '',
    registeredBy: entry.registeredBy || entry.registrado_por || entry.id_usuario_registra || '',
    idMembresia: entry.idMembresia || entry.id_membresia || entry.id_membresia || null,
    idMatricula: entry.idMatricula || entry.id_matricula || null,
    idHorarioServicio: entry.idHorarioServicio || entry.id_horario_servicio || null,
    date: entry.date || entry.fecha || '',
    time: entry.time || entry.hora_entrada || entry.hora || '',
    entryTime: entry.entryTime || entry.hora_entrada || entry.hora || '',
    exitTime: entry.exitTime || entry.hora_salida || '',
  };
};

const findMemberForAttendance = (entry = {}, memberList = []) => {
  const rawCode = String(entry.id_cliente || entry.memberCode || '').trim().toUpperCase();
  const numericId = Number(entry.id_cliente_num ?? String(rawCode).match(/(\d+)/)?.[1] ?? 0);

  return (
    memberList.find((member) => {
      const memberId = String(member.id || '').trim().toUpperCase();
      const internalCode = String(member.internalCode || '').trim().toUpperCase();
      const memberBackendId = Number(member.id_cliente || 0);
      return (
        (numericId && memberBackendId === numericId) ||
        (rawCode && (memberId === rawCode || internalCode === rawCode))
      );
    }) || null
  );
};

const normalizeBackendAttendanceRecord = (entry = {}, memberList = []) => {
  const member = findMemberForAttendance(entry, memberList);
  const backendCode = String(entry.id_cliente || entry.id_cliente_num || '').trim();

  return normalizeAttendanceRecord({
    id: `asistencia-${entry.id_asistencia || `${entry.fecha || todayISO()}-${entry.hora || nowTime()}-${backendCode}`}`,
    id_asistencia: entry.id_asistencia || null,
    id_cliente: entry.id_cliente || '',
    id_cliente_num: entry.id_cliente_num || null,
    memberId: member?.id || backendCode,
    memberName: member?.name || entry.memberName || backendCode || 'Cliente',
    memberCode: member?.internalCode || backendCode,
    time: entry.hora || '',
    date: entry.fecha || '',
    service: entry.servicio || 'fitness',
    registeredBy: entry.id_usuario_registra || entry.registrado_por || '',
    idMembresia: entry.id_membresia || null,
    idMatricula: entry.id_matricula || null,
    idHorarioServicio: entry.id_horario_servicio || null,
    entryTime: entry.hora_entrada || entry.hora || '',
    exitTime: entry.hora_salida || '',
  });
};

const normalizeState = (state) => ({
  ...seedState(),
  ...state,
  members: Array.isArray(state?.members) ? state.members.map((member) => normalizeMember(member)) : seedState().members,
  users: Array.isArray(state?.users) ? state.users.map((user) => normalizeUser(user)) : seedState().users,
  planCatalog: Array.isArray(state?.planCatalog) ? state.planCatalog : seedState().planCatalog,
  promotions: Array.isArray(state?.promotions) ? state.promotions : seedState().promotions,
  routines: Array.isArray(state?.routines) ? state.routines : seedState().routines,
  attendancePasses: Array.isArray(state?.attendancePasses) ? state.attendancePasses : [],
  attendance: Array.isArray(state?.attendance) ? state.attendance.map((entry) => normalizeAttendanceRecord(entry)) : seedState().attendance,
  inventory: Array.isArray(state?.inventory) ? state.inventory.map((item) => normalizeInventoryItem(item)) : seedState().inventory,
  productos_tienda: Array.isArray(state?.productos_tienda) ? state.productos_tienda : seedState().productos_tienda,
  storeOrders: Array.isArray(state?.storeOrders) ? state.storeOrders.map((order) => normalizeStoreOrder(order)) : seedState().storeOrders,
  cart: Array.isArray(state?.cart) ? state.cart : seedState().cart,
  serviceSchedules: Array.isArray(state?.serviceSchedules) ? state.serviceSchedules : seedState().serviceSchedules,
  enrollments: Array.isArray(state?.enrollments) ? state.enrollments : seedState().enrollments,
});

const buildAttendanceRecord = (member, response = {}, fallback = {}) =>
  normalizeAttendanceRecord({
    id: `asistencia-${response.id_asistencia || Date.now()}`,
    id_asistencia: response.id_asistencia || null,
    id_cliente: response.id_cliente || member.internalCode || member.id || '',
    id_cliente_num: response.id_cliente_num || member.id_cliente || null,
    memberId: member.id || member.internalCode,
    memberName: member.name,
    memberCode: member.internalCode,
    service: response.service || response.servicio || fallback.service || '',
    registeredBy: response.registeredBy || response.registrado_por || response.id_usuario_registra || fallback.registeredBy || '',
    idMembresia: response.idMembresia || response.id_membresia || fallback.idMembresia || null,
    idMatricula: response.idMatricula || response.id_matricula || fallback.idMatricula || null,
    idHorarioServicio: response.idHorarioServicio || response.id_horario_servicio || fallback.idHorarioServicio || null,
    time: response.time || response.hora || fallback.time || nowTime(),
    entryTime: response.entryTime || response.hora_entrada || response.hora || fallback.entryTime || fallback.time || nowTime(),
    exitTime: response.exitTime || response.hora_salida || fallback.exitTime || '',
    date: response.date || response.fecha || fallback.date || todayISO(),
  });

const getCurrentRegistrarId = (authStore) => authStore.user?.id_usuario || authStore.user?.id || authStore.user?.email || null;

const getClientIdForBackend = (member) => {
  if (!member) return '';
  if (member.id_cliente) return String(member.id_cliente);
  if (member.id) return String(member.id);
  if (member.internalCode) return String(member.internalCode);
  return '';
};

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

const loadState = () => seedState();

export const useGymStore = defineStore('gym', () => {
  const initialState = loadState();
  const authStore = useAuthStore();
  const planCatalog = ref(initialState.planCatalog);
  const promotions = ref(initialState.promotions);
  const members = ref(initialState.members);
  const users = ref(initialState.users);
  const attendance = ref(initialState.attendance);
  const attendancePasses = ref(initialState.attendancePasses || []);
  const inventory = ref(initialState.inventory);
  const productos_tienda = ref(initialState.productos_tienda);
  const storeOrders = ref(initialState.storeOrders);
  const cart = ref(initialState.cart);
  const routines = ref(initialState.routines);
  const schedule = ref(initialState.schedule);
  const serviceSchedules = ref(initialState.serviceSchedules);
  const enrollments = ref(initialState.enrollments);

  const persist = () => {
    // Business data is persisted only through the backend, which writes to Supabase.
  };

  const mergeAttendanceRecord = (record) => {
    const normalized = normalizeAttendanceRecord(record);
    const index = attendance.value.findIndex((entry) => {
      if (normalized.id_asistencia && entry.id_asistencia) {
        return Number(entry.id_asistencia) === Number(normalized.id_asistencia);
      }

      return entry.id === normalized.id;
    });

    if (index >= 0) {
      attendance.value[index] = normalized;
    } else {
      attendance.value.unshift(normalized);
    }

    persist();
    return normalized;
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

  const memberByInternalCode = (code) => {
    const normalizedCode = String(code || '').trim().toUpperCase();
    if (!normalizedCode) {
      return null;
    }

    return (
      members.value.find((member) => {
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

  const isMembershipActive = (member, referenceDate = todayISO()) => {
    const status = String(member?.membershipStatus || member?.status || '').trim().toUpperCase();
    return Boolean(member) && ['ACTIVO', 'ACTIVA'].includes(status) && (!member.membershipEnd || member.membershipEnd >= referenceDate);
  };

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

  const upsertRutina = async (payload) => {
    const rutina = {
      id_rutina: payload.id_rutina || payload.id || null,
      nombre_rutina: payload.nombre_rutina?.trim() || 'Sin nombre',
      zonas_musculares: payload.zonas_musculares || '',
      color: payload.color || 'Azul',
    };

    if (apiBase) {
      const response = await fetch(`${apiBase}/gym/rutinas`, {
        method: 'POST',
        headers: _authHeaders(),
        body: JSON.stringify(rutina),
      });

      if (!response.ok) {
        throw new Error('Error al guardar rutina en backend');
      }

      const saved = await response.json();
      const normalized = {
        id_rutina: saved.id_rutina,
        nombre_rutina: saved.nombre_rutina || rutina.nombre_rutina,
        zonas_musculares: saved.zonas_musculares || rutina.zonas_musculares,
        color: saved.color || rutina.color,
      };

      const index = routines.value.findIndex((entry) => Number(entry.id_rutina) === Number(normalized.id_rutina));
      if (index >= 0) {
        routines.value[index] = normalized;
      } else {
        routines.value.unshift(normalized);
      }

      persist();
      return normalized;
    }

    const nextId = rutina.id_rutina || (routines.value.length ? Math.max(...routines.value.map((entry) => Number(entry.id_rutina) || 0)) + 1 : 1);
    const normalized = { ...rutina, id_rutina: nextId };
    const index = routines.value.findIndex((entry) => Number(entry.id_rutina) === Number(normalized.id_rutina));
    if (index >= 0) {
      routines.value[index] = normalized;
    } else {
      routines.value.unshift(normalized);
    }

    persist();
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

    if (apiBase) {
      const response = await fetch(`${apiBase}/gym/horarios`, {
        method: 'POST',
        headers: _authHeaders(),
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

      const index = schedule.value.findIndex((entry) => Number(entry.id_horario) === Number(normalized.id_horario));
      if (index >= 0) {
        schedule.value[index] = normalized;
      } else {
        schedule.value.unshift(normalized);
      }

      const memberIndex = members.value.findIndex((member) => Number(member.id_cliente) === Number(normalized.id_cliente));
      if (memberIndex >= 0) {
        const member = members.value[memberIndex];
        members.value[memberIndex] = {
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

      persist();
      return normalized;
    }

    const nextId = scheduleItem.id_horario || (schedule.value.length ? Math.max(...schedule.value.map((entry) => Number(entry.id_horario) || 0)) + 1 : 1);
    const normalized = { ...scheduleItem, id_horario: nextId };
    const index = schedule.value.findIndex((entry) => Number(entry.id_horario) === Number(normalized.id_horario));
    if (index >= 0) {
      schedule.value[index] = normalized;
    } else {
      schedule.value.unshift(normalized);
    }

    persist();
    return normalized;
  };

  const assignPlanToMember = (memberId, planId, promotionId = '', note = 'Asignación de membresía') => {
    // Si hay backend configurado, intentar delegar la creación/renovación al servidor
    const index = members.value.findIndex((entry) => entry.id === memberId);
    if (index < 0) {
      throw new Error('Miembro no encontrado');
    }

    const member = members.value[index];
    // Intentar extraer id_cliente si el id viene del backend (cliente-<id> o SGCLI<id>)
    if (apiBase && /^(?:cliente-|SGCLI)\d+$/i.test(memberId)) {
      const id_cliente = Number(String(memberId).replace(/^(?:cliente-|SGCLI)/i, ''));
      // Obtener id_pm numérico desde planId (soporta pm-<id> y 'pm-...')
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
      const endDate = addMonthsISO(startDate, getPlanById(planId)?.durationMonths || 1);

      const payload = { id_cliente, id_pm, fecha_inicio: startDate, fecha_fin: endDate };
      return fetch(`${apiBase}/membresias`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) })
        .then((r) => {
          if (!r.ok) throw new Error('Error al asignar membresía en backend');
          return r.json();
        })
        .then((memb) => {
          // actualizar estado local mínimo
          members.value[index] = { ...member, plan: getPlanById(planId)?.name || member.plan, planId, membershipStart: startDate, membershipEnd: endDate, membershipPrice: memb.precio || member.membershipPrice, status: 'Activa' };
          logMemberEvent(memberId, { action: memb.id_membresia ? 'Asignación' : 'Renovación', fields: ['plan', 'planId', 'membershipStart', 'membershipEnd', 'membershipPrice', 'status'], note });
          persist();
          return members.value[index];
        });
    }

    // Fallback local
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

  const recordAttendanceByCode = (internalCode, service = 'fitness', options = {}) => {
    const member = memberByInternalCode(internalCode);
    if (!member) {
      throw new Error('Código no encontrado');
    }

    if (apiBase) {
      const backendMemberId = getClientIdForBackend(member);
      const registrarId = getCurrentRegistrarId(authStore);
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

    if (!isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía vigente');
    }

    const record = buildAttendanceRecord(member, {}, {
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

    const localMember = members.value.find((member) => String(member.dni || '').trim() === normalizedDni) || null;

    if (apiBase) {
      return checkinByDniServer({
        dni: normalizedDni,
        id_usuario: getCurrentRegistrarId(authStore),
        servicio: service || 'fitness',
        fecha: options.fecha || options.date || todayISO(),
        hora: options.hora || options.time || nowTime(),
      }).then((res) => {
        const member = localMember || findMemberForAttendance(res, members.value) || {
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

  const memberSchedules = (memberId) => {
    const member = memberById(memberId);
    if (!member) return [];

    if (apiBase && schedule.value.length) {
      const backendId = Number(member.id_cliente || String(member.id || '').match(/^(?:cliente-|SGCLI)(\d+)$/i)?.[1] || 0);
      if (backendId) {
        return schedule.value.filter((entry) => Number(entry.id_cliente) === backendId);
      }
    }

    return member.schedules || [];
  };

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

  const normalizeLookupEmail = (value) => String(value || '').trim().toLowerCase();

  const userAttendance = (email) => {
    const normalizedEmail = normalizeLookupEmail(email);
    const member = members.value.find((entry) => normalizeLookupEmail(entry.email || entry.correo) === normalizedEmail);
    if (!member) return [];

    return attendance.value
      .filter((entry) => {
        const entryCodes = [entry.memberId, entry.memberCode, entry.id_cliente].map((value) => String(value || '').trim().toUpperCase());
        const memberCodes = [member.id, member.internalCode, member.memberCode, member.id_cliente].map((value) => String(value || '').trim().toUpperCase());
        return entryCodes.some((code) => memberCodes.includes(code));
      })
      .slice(0, 10);
  };

  const memberByEmail = (email) => {
    const normalizedEmail = normalizeLookupEmail(email);
    return members.value.find((member) => normalizeLookupEmail(member.email || member.correo) === normalizedEmail) || null;
  };

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

  const redeemAttendancePass = async (input, type = 'fitness', note = '') => {
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

    const record = await recordAttendance(pass.memberId, type, { note });
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
      status: payload.status || existingMember?.status || 'Activa',
      joinedAt: payload.joinedAt || existingMember?.joinedAt || todayISO(),
      attendanceRate: Number(payload.attendanceRate ?? existingMember?.attendanceRate ?? 0),
      membershipHistory: Array.isArray(payload.membershipHistory) ? payload.membershipHistory : existingMember?.membershipHistory || [],
      changeHistory: Array.isArray(payload.changeHistory) ? payload.changeHistory : existingMember?.changeHistory || [],
      schedules: Array.isArray(payload.schedules) ? payload.schedules : existingMember?.schedules || [],
    };

    if (apiBase) {
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

      return fetch(`${apiBase}/clientes`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(body) })
        .then((r) => {
          if (!r.ok) throw new Error('Error al crear/actualizar cliente en backend');
          return r.json();
        })
        .then((created) => {
          const id_cliente = Number(String(created.id_usuario || created.id || '').replace(/^SGCLI/i, '')) || backendId || Date.now();
          const localId = created.id_usuario || `SGCLI${String(id_cliente).padStart(3, '0')}`;
          const localMember = { ...member, id: localId, id_cliente, internalCode: String(localId), joinedAt: created.fecha_registro || member.joinedAt };
          const idx = members.value.findIndex((m) => m.id === localMember.id || m.dni === localMember.dni);
          if (idx >= 0) members.value[idx] = localMember; else members.value.unshift(localMember);
          persist();

          // Si se asignó un plan en el payload, registrar membresía
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
    if (apiBase && /^(?:cliente-|SGCLI)\d+$/i.test(id)) {
      const id_cliente = Number(String(id).replace(/^(?:cliente-|SGCLI)/i, ''));
      fetch(`${apiBase}/clientes/${id_cliente}`, { method: 'DELETE', headers: _authHeaders() }).catch(() => {});
    }
    members.value = members.value.filter((member) => member.id !== id);
    attendance.value = attendance.value.filter((entry) => entry.memberId !== id);
    attendancePasses.value = attendancePasses.value.filter((pass) => pass.memberId !== id);
    persist();
  };

  const deleteClient = (id) => deleteMember(id);

  const recordAttendance = (memberId, service = 'fitness', options = {}) => {
    const member = members.value.find((entry) => entry.id === memberId);
    if (!member) {
      throw new Error('Miembro no encontrado');
    }

    // Si hay backend, primero intentar con id_cliente y luego con DNI.
    if (apiBase) {
      const backendMemberId = getClientIdForBackend(member);
      const registrarId = getCurrentRegistrarId(authStore);
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

    if (!isMembershipActive(member)) {
      throw new Error('El socio no tiene una membresía vigente');
    }

    const record = buildAttendanceRecord(member, {}, {
      service: service || 'fitness',
      time: options.hora || options.time || nowTime(),
      date: options.fecha || options.date || todayISO(),
    });

    return mergeAttendanceRecord(record);
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
    if (apiBase) {
      // map frontend payload to backend InventarioInput
      const body = {
        id_item: payload.id ? Number(String(payload.id).split('-').pop()) : undefined,
        nombre_item: payload.name,
        tipo: payload.category,
        cantidad_stock: Number(payload.quantity ?? 0),
        estado: payload.status || 'Operativo',
        n_activo: payload.n_activo || undefined,
        unidad_venta: payload.unidad_venta || payload.unit || 'unidad',
        precio_venta: Number(payload.precio_venta ?? payload.salePrice ?? 0),
        stock_minimo: Number(payload.minQuantity ?? payload.stock_minimo ?? 1),
        ubicacion: payload.location || 'Almacén',
        observaciones: payload.observations || '',
      };
      return upsertInventoryToServer(body).then((res) => {
        const id_item = res.id_item || (res.id && Number(res.id)) || (body.id_item || Date.now());
        const item = {
          id: `item-${id_item}`,
          inventoryCode: `ACT-${String(res.n_activo || id_item).padStart(4, '0')}`,
          n_activo: res.n_activo || id_item,
          name: res.nombre_item || payload.name,
          category: res.tipo || payload.category,
          quantity: res.cantidad_stock ?? Number(payload.quantity ?? 0),
          minQuantity: Number(res.stock_minimo ?? payload.minQuantity ?? 1),
          unidad_venta: res.unidad_venta || payload.unidad_venta || 'unidad',
          precio_venta: Number(res.precio_venta ?? payload.precio_venta ?? 0),
          location: res.ubicacion || payload.location || 'Almacén',
          status: res.estado || payload.status || 'Operativo',
          observations: res.observaciones || payload.observations || '',
        };
        const index = inventory.value.findIndex((entry) => entry.id === item.id);
        if (index >= 0) inventory.value[index] = item; else inventory.value.unshift(item);
        persist();
        return item;
      });
    }

    const existingItem = inventory.value.find((entry) => entry.id === payload.id);
    const item = {
      id: payload.id || `item-${Date.now()}`,
      inventoryCode: payload.inventoryCode?.trim() || existingItem?.inventoryCode || generateInventoryCode(),
      n_activo: payload.n_activo || existingItem?.n_activo || '',
      name: payload.name?.trim() || 'Sin nombre',
      category: payload.category || 'General',
      quantity: Number(payload.quantity ?? 0),
      minQuantity: Number(payload.minQuantity ?? existingItem?.minQuantity ?? 1),
      unidad_venta: payload.unidad_venta || existingItem?.unidad_venta || 'unidad',
      precio_venta: Number(payload.precio_venta ?? existingItem?.precio_venta ?? 0),
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

  const upsertUser = async (payload) => {
    const existingUser = users.value.find((entry) => String(entry.id_usuario) === String(payload.id_usuario || '').trim());
    const userPayload = {
      ...(existingUser?.id_usuario ? { id_usuario: existingUser.id_usuario } : {}),
      nombre: String(payload.nombre || existingUser?.nombre || '').trim(),
      correo: String(payload.correo || payload.email || existingUser?.correo || '').trim(),
      telefono: String(payload.telefono || existingUser?.telefono || '').trim(),
      dni: String(payload.dni || existingUser?.dni || '').trim(),
      password: String(payload.password || payload.contrasena || '').trim(),
      rol: payload.rol || existingUser?.rol || 'staff',
    };

    if (apiBase) {
      if (payload.id_usuario) {
        userPayload.id_usuario = String(payload.id_usuario).trim();
      }

      const saved = await upsertUserToServer(userPayload);
      const normalized = normalizeUser(saved);
      const index = users.value.findIndex((entry) => String(entry.id_usuario) === String(normalized.id_usuario));
      if (index >= 0) {
        users.value[index] = normalized;
      } else {
        users.value.unshift(normalized);
      }
      persist();
      return normalized;
    }

    const nextId = userPayload.id_usuario || `SGUS${String(users.value.length + 1).padStart(3, '0')}`;
    const normalized = normalizeUser({ ...userPayload, id_usuario: nextId });
    const index = users.value.findIndex((entry) => String(entry.id_usuario) === String(normalized.id_usuario));
    if (index >= 0) {
      users.value[index] = normalized;
    } else {
      users.value.unshift(normalized);
    }
    persist();
    return normalized;
  };

  const deleteUser = async (idUsuario) => {
    const normalizedId = String(idUsuario || '').trim();
    if (!normalizedId) {
      throw new Error('Usuario no encontrado');
    }

    if (apiBase) {
      await deleteUserFromServer(normalizedId);
    }

    users.value = users.value.filter((user) => String(user.id_usuario) !== normalizedId);
    persist();
  };

  const deleteInventoryItem = (id) => {
    if (apiBase && /^item-\d+$/.test(id)) {
      const id_item = Number(id.split('-')[1]);
      fetch(`${apiBase}/inventario/${id_item}`, { method: 'DELETE', headers: _authHeaders() }).catch(() => {});
    }
    inventory.value = inventory.value.filter((item) => item.id !== id);
    persist();
  };

  // Funciones para productos de tienda
  const upsertProductoTienda = async (payload) => {
    const producto = {
      id_producto: payload.id_producto || null,
      nombre_producto: payload.nombre?.trim() || 'Sin nombre',
      descripcion: payload.descripcion || '',
      categoria: payload.categoria || 'General',
      id_item: payload.id_item ? Number(payload.id_item) : null,
      unidad_venta: payload.unidad_venta || 'unidad',
      precio_venta: Number(payload.precio ?? 0),
      cantidad_stock: Number(payload.cantidad ?? 0),
      stock_minimo: Number(payload.minimo ?? 5),
      estado: payload.estado || 'Disponible',
    };

    if (apiBase) {
      const body = {
        ...producto,
        id_producto: producto.id_producto || undefined,
      };
      
      const res = await fetch(`${apiBase}/tienda`, {
        method: 'POST',
        headers: _authHeaders(),
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error('Error al guardar producto en backend');
      const saved = await res.json();
      
      const id_producto = saved.id_producto || payload.id_producto || Date.now();
      const normalized = {
        id: `producto-${id_producto}`,
        id_producto,
        nombre: saved.nombre_producto || producto.nombre_producto,
        descripcion: saved.descripcion || producto.descripcion,
        categoria: saved.categoria || producto.categoria,
        id_item: saved.id_item || producto.id_item || null,
        unidad_venta: saved.unidad_venta || producto.unidad_venta || 'unidad',
        precio: Number(saved.precio_venta || producto.precio_venta),
        cantidad: saved.cantidad_stock ?? producto.cantidad_stock,
        minimo: Number(saved.stock_minimo || producto.stock_minimo),
        estado: saved.estado || producto.estado,
      };

      const index = productos_tienda.value.findIndex((p) => p.id_producto === id_producto);
      if (index >= 0) {
        productos_tienda.value[index] = normalized;
      } else {
        productos_tienda.value.unshift(normalized);
      }
      
      persist();
      return normalized;
    }

    const id_producto = payload.id_producto || Date.now();
    const normalized = {
      id: `producto-${id_producto}`,
      id_producto,
      nombre: producto.nombre_producto,
      descripcion: producto.descripcion,
      categoria: producto.categoria,
      id_item: producto.id_item || null,
      unidad_venta: producto.unidad_venta || 'unidad',
      precio: Number(producto.precio_venta),
      cantidad: Number(producto.cantidad_stock),
      estado: producto.estado,
    };

    const index = productos_tienda.value.findIndex((p) => p.id_producto === id_producto);
    if (index >= 0) {
      productos_tienda.value[index] = normalized;
    } else {
      productos_tienda.value.unshift(normalized);
    }
    
    persist();
    return normalized;
  };

  const deleteProductoTienda = async (id_producto) => {
    if (apiBase) {
      try {
        await fetch(`${apiBase}/tienda/${id_producto}`, {
          method: 'DELETE',
          headers: _authHeaders(),
        });
      } catch (error) {
        console.error('Error al eliminar producto en backend:', error);
      }
    }
    
    productos_tienda.value = productos_tienda.value.filter((p) => p.id_producto !== id_producto);
    persist();
  };

  // Funciones del carrito
  const addToCart = (producto, cantidad = 1) => {
    const existingItem = cart.value.find((item) => item.id_producto === producto.id_producto);
    
    if (existingItem) {
      existingItem.cantidad += cantidad;
    } else {
      cart.value.push({
        id_producto: producto.id_producto,
        nombre: producto.nombre,
        precio: producto.precio,
        cantidad: Math.max(1, cantidad),
      });
    }
    
    persist();
  };

  const removeFromCart = (id_producto) => {
    cart.value = cart.value.filter((item) => item.id_producto !== id_producto);
    persist();
  };

  const updateCartQuantity = (id_producto, cantidad) => {
    const item = cart.value.find((item) => item.id_producto === id_producto);
    if (item) {
      item.cantidad = Math.max(1, cantidad);
      persist();
    }
  };

  const clearCart = () => {
    cart.value = [];
    persist();
  };

 const cartTotal = computed(() => {
    const subtotal = cart.value.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    const igv = subtotal * 0.18;
    const total = subtotal + igv;
    return { subtotal, igv, total };
  });

  /* ----------------- Integración con backend ----------------- */
  const apiBase = APP_CONFIG.authApiBaseUrl || '/api';

  const _authHeaders = () => {
    try {
      const auth = useAuthStore();
      const headers = { 'Content-Type': 'application/json' };
      if (auth?.token) headers.Authorization = `Bearer ${auth.token}`;
      return headers;
    } catch (e) {
      return { 'Content-Type': 'application/json' };
    }
  };

  const readBackendError = async (response, fallbackMessage) => {
    try {
      const data = await response.json();
      return data?.detail || data?.message || fallbackMessage;
    } catch (error) {
      return fallbackMessage;
    }
  };

  const mergeStoreOrder = (order) => {
    const normalized = normalizeStoreOrder(order);
    const index = storeOrders.value.findIndex((entry) => Number(entry.id_pedido) === Number(normalized.id_pedido));
    if (index >= 0) {
      storeOrders.value[index] = normalized;
    } else {
      storeOrders.value.unshift(normalized);
    }
    persist();
    return normalized;
  };

  const refreshStoreProductsFromBackend = async () => {
    if (!apiBase) throw new Error('No hay backend configurado');

    const response = await fetch(`${apiBase}/tienda`, { headers: _authHeaders() });
    if (!response.ok) {
      throw new Error(await readBackendError(response, 'Error al cargar productos de tienda'));
    }

    const list = await response.json();
    productos_tienda.value = list.map((product) => normalizeStoreProductFromBackend(product));
    persist();
    return productos_tienda.value;
  };

  const refreshStoreOrdersFromBackend = async () => {
    if (!apiBase) throw new Error('No hay backend configurado');

    const response = await fetch(`${apiBase}/tienda/pedidos`, { headers: _authHeaders() });
    if (!response.ok) {
      throw new Error(await readBackendError(response, 'Error al cargar pedidos'));
    }

    const list = await response.json();
    storeOrders.value = list.map((order) => normalizeStoreOrder(order));
    persist();
    return storeOrders.value;
  };

  const createStoreOrder = async (payload = {}) => {
    const items = Array.isArray(payload.items) && payload.items.length ? payload.items : cart.value;
    if (!items.length) {
      throw new Error('El carrito esta vacio');
    }

    const body = {
      id_cliente: payload.id_cliente || null,
      cliente_nombre: payload.cliente_nombre || payload.customerName || authStore.user?.name || 'Cliente',
      cliente_correo: payload.cliente_correo || payload.customerEmail || authStore.user?.email || '',
      cliente_dni: payload.cliente_dni || payload.dni || authStore.user?.dni || '',
      metodo_pago: payload.metodo_pago || 'tarjeta',
      referencia_pago: payload.referencia_pago || `WEB-${Date.now()}`,
      items: items.map((item) => ({
        id_producto: Number(item.id_producto),
        cantidad: Math.max(1, Number(item.cantidad || 1)),
      })),
    };

    if (apiBase) {
      const response = await fetch(`${apiBase}/tienda/pedidos`, {
        method: 'POST',
        headers: _authHeaders(),
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error(await readBackendError(response, 'No se pudo registrar el pedido'));
      }

      const saved = mergeStoreOrder(await response.json());
      clearCart();
      await refreshStoreProductsFromBackend().catch(() => {});
      return saved;
    }

    const orderItems = body.items.map((item) => {
      const product = productos_tienda.value.find((entry) => Number(entry.id_producto) === Number(item.id_producto));
      if (!product) {
        throw new Error(`Producto no encontrado: ${item.id_producto}`);
      }
      if (Number(product.cantidad || 0) < item.cantidad) {
        throw new Error(`Stock insuficiente para ${product.nombre}`);
      }

      product.cantidad = Number(product.cantidad || 0) - item.cantidad;
      return {
        id_producto: product.id_producto,
        nombre_producto: product.nombre,
        cantidad: item.cantidad,
        precio_unitario: Number(product.precio || 0),
        subtotal: Number(product.precio || 0) * item.cantidad,
      };
    });

    const subtotal = orderItems.reduce((sum, item) => sum + Number(item.subtotal || 0), 0);
    const igv = subtotal * 0.18;
    const saved = mergeStoreOrder({
      id_pedido: Date.now(),
      ...body,
      fecha_pedido: nowISO(),
      estado_pago: 'PAGADO',
      estado_pedido: 'PENDIENTE',
      subtotal,
      igv,
      total: subtotal + igv,
      items: orderItems,
    });
    clearCart();
    return saved;
  };

  const refreshAttendanceFromBackend = async () => {
    if (!apiBase) throw new Error('No hay backend configurado');

    const response = await fetch(`${apiBase}/asistencia`, { headers: _authHeaders() });
    if (!response.ok) {
      throw new Error(await readBackendError(response, 'Error al cargar asistencia'));
    }

    const list = await response.json();
    attendance.value = list.map((entry) => normalizeBackendAttendanceRecord(entry, members.value));
    persist();
    return attendance.value;
  };

  const refreshServiceSchedulesFromBackend = async () => {
    if (!apiBase) throw new Error('No hay backend configurado');

    const response = await fetch(`${apiBase}/gym/horarios-servicio`, { headers: _authHeaders() });
    if (!response.ok) {
      throw new Error(await readBackendError(response, 'Error al cargar horarios de servicio'));
    }

    serviceSchedules.value = await response.json();
    persist();
    return serviceSchedules.value;
  };

  const upsertServiceSchedule = async (payload) => {
    const body = {
      id_horario_servicio: payload.id_horario_servicio || null,
      servicio: payload.servicio,
      hora_inicio: payload.hora_inicio || '06:00',
      hora_fin: payload.hora_fin || '07:00',
      codigo_dia: payload.codigo_dia || '',
      dia: payload.dia || (Array.isArray(payload.dias) ? payload.dias[0] : 'lunes'),
      cupos: Number(payload.cupos || 10),
      activo: payload.activo !== false,
    };

    if (apiBase) {
      const response = await fetch(`${apiBase}/gym/horarios-servicio`, {
        method: 'POST',
        headers: _authHeaders(),
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error(await readBackendError(response, 'Error al guardar horario de servicio'));
      }

      const saved = await response.json();
      const index = serviceSchedules.value.findIndex((entry) => Number(entry.id_horario_servicio) === Number(saved.id_horario_servicio));
      if (index >= 0) {
        serviceSchedules.value[index] = saved;
      } else {
        serviceSchedules.value.push(saved);
      }
      persist();
      return saved;
    }

    if (!body.id_horario_servicio) {
      body.id_horario_servicio = Date.now();
      body.cupos_usados = 0;
    }
    const index = serviceSchedules.value.findIndex((entry) => Number(entry.id_horario_servicio) === Number(body.id_horario_servicio));
    if (index >= 0) {
      serviceSchedules.value[index] = body;
    } else {
      serviceSchedules.value.push(body);
    }
    persist();
    return body;
  };

  const deleteServiceSchedule = async (idHorarioServicio) => {
    if (apiBase) {
      const response = await fetch(`${apiBase}/gym/horarios-servicio/${idHorarioServicio}`, {
        method: 'DELETE',
        headers: _authHeaders(),
      });
      if (!response.ok && response.status !== 204) {
        throw new Error(await readBackendError(response, 'No se pudo eliminar el horario'));
      }
    }

    serviceSchedules.value = serviceSchedules.value.filter((entry) => Number(entry.id_horario_servicio) !== Number(idHorarioServicio));
    persist();
  };

  const refreshEnrollmentsFromBackend = async (filters = {}) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const params = new URLSearchParams();
    if (filters.id_cliente) params.set('id_cliente', filters.id_cliente);
    if (filters.dni) params.set('dni', filters.dni);
    const query = params.toString() ? `?${params.toString()}` : '';
    const response = await fetch(`${apiBase}/gym/matriculas${query}`, { headers: _authHeaders() });
    if (!response.ok) {
      throw new Error(await readBackendError(response, 'Error al cargar matriculas'));
    }
    const list = (await response.json()).map((entry) => ({
      ...entry,
      estado: String(entry.estado || 'ACTIVA').toUpperCase(),
    }));
    if (filters.id_cliente || filters.dni) {
      const incomingIds = new Set(list.map((entry) => Number(entry.id_matricula)));
      const filteredClientId = Number(filters.id_cliente || list[0]?.id_cliente || 0);
      enrollments.value = [
        ...list,
        ...enrollments.value.filter((entry) => {
          if (filteredClientId && Number(entry.id_cliente) === filteredClientId) return false;
          return !incomingIds.has(Number(entry.id_matricula));
        }),
      ];
    } else {
      enrollments.value = list;
    }
    persist();
    return list;
  };

  const enrollSchedule = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const response = await fetch(`${apiBase}/gym/matriculas`, {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await readBackendError(response, 'No se pudo matricular en el horario'));
    }
    const savedResponse = await response.json();
    const saved = {
      ...savedResponse,
      estado: String(savedResponse.estado || 'ACTIVA').toUpperCase(),
    };
    const index = enrollments.value.findIndex((entry) => Number(entry.id_matricula) === Number(saved.id_matricula));
    if (index >= 0) {
      enrollments.value[index] = saved;
    } else {
      enrollments.value.unshift(saved);
    }
    await refreshServiceSchedulesFromBackend().catch(() => {});
    persist();
    return saved;
  };

  const deleteEnrollment = async (idMatricula) => {
    if (apiBase) {
      const response = await fetch(`${apiBase}/gym/matriculas/${idMatricula}`, {
        method: 'DELETE',
        headers: _authHeaders(),
      });
      if (!response.ok && response.status !== 204) {
        throw new Error(await readBackendError(response, 'No se pudo cancelar la matricula'));
      }
    }
    enrollments.value = enrollments.value.map((entry) =>
      Number(entry.id_matricula) === Number(idMatricula) ? { ...entry, estado: 'CANCELADA' } : entry,
    );
    await refreshServiceSchedulesFromBackend().catch(() => {});
    persist();
  };

  const fetchFromBackend = async () => {
    if (!apiBase) throw new Error('No hay backend configurado en APP_CONFIG.authApiBaseUrl');

    // Clientes -> members
    const resClientes = await fetch(`${apiBase}/clientes`, { headers: _authHeaders() });
    if (resClientes.ok) {
      const list = await resClientes.json();
      members.value = list.map((c) => ({
        id: c.id_usuario || `cliente-${c.id_cliente || Date.now()}`,
        id_cliente:
          c.id_cliente || Number(String(c.id_usuario || '').match(/(?:SGCLI|cliente-)(\d+)/)?.[1] || 0) || null,
        name: c.nombre || `${c.nombres || ''} ${c.apellidos || ''}`.trim(),
        dni: c.dni || '',
        internalCode: String(c.id_usuario || c.id_cliente || '').trim(),
        email: c.correo || c.email || '',
        phone: c.telefono || c.phone || '',
        role: 'user',
        plan: c.plan || '',
        promocion: c.promocion || '',
        planId: '',
        id_membresia: c.id_membresia || null,
        membershipStatus: c.membership_status || c.estado || '',
        membershipStart: c.membership_start || c.fecha_registro || c.joinedAt || '',
        membershipEnd: c.membership_end || '',
        paymentStatus: c.payment_status || '',
        paymentReference: c.payment_reference || '',
        hasPassword: Boolean(c.has_password ?? c.hasPassword),
        membershipPrice: 0,
        status: String(c.estado || (c.estado === false ? 'INACTIVO' : 'ACTIVO')).toUpperCase(),
        joinedAt: c.fecha_registro || c.joinedAt || '',
        attendanceRate: 0,
        membershipHistory: [],
        changeHistory: [],
        schedules: [],
      }));
    }

    const resUsuarios = await fetch(`${apiBase}/usuarios`, { headers: _authHeaders() });
    if (resUsuarios.ok) {
      const list = await resUsuarios.json();
      users.value = list.map((user) => normalizeUser(user));
    }

    // Inventario
    const resInv = await fetch(`${apiBase}/inventario`, { headers: _authHeaders() });
    if (resInv.ok) {
      const list = await resInv.json();
      inventory.value = list.map((i) => ({
        id: `item-${i.id_item}`,
        inventoryCode: `ACT-${String(i.n_activo || i.id_item).padStart(4, '0')}`,
        n_activo: i.n_activo || i.id_item,
        name: i.nombre_item,
        category: i.tipo,
        quantity: i.cantidad_stock,
        minQuantity: Number(i.stock_minimo ?? 1),
        unidad_venta: i.unidad_venta || 'unidad',
        precio_venta: Number(i.precio_venta ?? 0),
        location: i.ubicacion || 'Almacén',
        status: i.estado || '',
        observations: i.observaciones || '',
      }));
    }

    // Productos de tienda
    const resTienda = await fetch(`${apiBase}/tienda`, { headers: _authHeaders() });
    if (resTienda.ok) {
      const list = await resTienda.json();
      productos_tienda.value = list.map((p) => normalizeStoreProductFromBackend(p));
    }

    const resPedidos = await fetch(`${apiBase}/tienda/pedidos`, { headers: _authHeaders() });
    if (resPedidos.ok) {
      const list = await resPedidos.json();
      storeOrders.value = list.map((order) => normalizeStoreOrder(order));
    }

    // Planes de membresía
    const resPlanes = await fetch(`${apiBase}/planes-membresia`, { headers: _authHeaders() });
    if (resPlanes.ok) {
      const list = await resPlanes.json();
      planCatalog.value = list.map((p) => ({
        id: `pm-${p.id_pm}`,
        name: p.nombre_plan,
        durationMonths: Number(String(p.duracion).match(/\d+/)?.[0] || 1),
        price: Number(p.precio || 0),
        description: p.duracion || '',
        active: true,
      }));
    }

    const resHorarios = await fetch(`${apiBase}/gym/horarios`, { headers: _authHeaders() });
    if (resHorarios.ok) {
      const list = await resHorarios.json();
      schedule.value = list.map((h) => ({
        id_horario: h.id_horario,
        id_cliente: h.id_cliente,
        id_rutina: h.id_rutina,
        dia_semana: h.dia_semana,
        hora_inicio: h.hora_inicio,
        hora_fin: h.hora_fin,
        capacidad_maxima: Number(h.capacidad_maxima ?? 1),
        cupos_usados: Number(h.cupos_usados ?? 1),
      }));
    }

    await refreshServiceSchedulesFromBackend();
    await refreshEnrollmentsFromBackend();

    const resRutinas = await fetch(`${apiBase}/gym/rutinas`, { headers: _authHeaders() });
    if (resRutinas.ok) {
      const list = await resRutinas.json();
      routines.value = list.map((r) => ({
        id_rutina: r.id_rutina,
        nombre_rutina: r.nombre_rutina,
        zonas_musculares: r.zonas_musculares || '',
        color: r.color || 'Azul',
      }));
    }

    await refreshAttendanceFromBackend();
  };

  const upsertClienteToServer = async (clientePayload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/clientes`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(clientePayload) });
    if (!res.ok) throw new Error('Error al guardar cliente en backend');
    return res.json();
  };

  const upsertClient = async (payload) => {
    const existingClient = members.value.find((entry) => String(entry.id) === String(payload.id_usuario || '').trim());
    const clientPayload = {
      ...(payload.id_usuario ? { id_usuario: String(payload.id_usuario).trim() } : {}),
      nombre: String(payload.nombre || existingClient?.name || '').trim(),
      correo: String(payload.correo || payload.email || existingClient?.email || '').trim(),
      telefono: String(payload.telefono || existingClient?.phone || '').trim(),
      dni: String(payload.dni || existingClient?.dni || '').trim(),
      password: String(payload.password || payload.contrasena || '').trim(),
      plan: String(payload.plan || existingClient?.plan || 'MENSUAL').trim() || 'MENSUAL',
      promocion: String(payload.promocion || existingClient?.promocion || 'SIN PROMOCION').trim() || 'SIN PROMOCION',
      estado: String(payload.estado || existingClient?.status || 'ACTIVO').trim().toUpperCase() || 'ACTIVO',
    };

    if (apiBase) {
      const saved = await upsertClienteToServer(clientPayload);
      const numericId = Number(saved.id_cliente || 0) || Number(String(saved.id_usuario || '').replace(/^SGCLI/i, '')) || Number(existingClient?.id_cliente || 0) || Date.now();
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
        planId: '',
        id_membresia: saved.id_membresia || existingClient?.id_membresia || null,
        membershipStatus: saved.membership_status || existingClient?.membershipStatus || saved.estado || clientPayload.estado,
        membershipStart: saved.membership_start || existingClient?.membershipStart || '',
        membershipEnd: saved.membership_end || existingClient?.membershipEnd || '',
        paymentStatus: saved.payment_status || existingClient?.paymentStatus || '',
        paymentReference: saved.payment_reference || existingClient?.paymentReference || '',
        hasPassword: Boolean(saved.has_password ?? saved.hasPassword ?? existingClient?.hasPassword),
        membershipPrice: Number(existingClient?.membershipPrice ?? 0),
        status: saved.estado || clientPayload.estado,
        joinedAt: existingClient?.joinedAt || '',
        attendanceRate: Number(existingClient?.attendanceRate ?? 0),
        membershipHistory: Array.isArray(existingClient?.membershipHistory) ? existingClient.membershipHistory : [],
        changeHistory: Array.isArray(existingClient?.changeHistory) ? existingClient.changeHistory : [],
        schedules: Array.isArray(existingClient?.schedules) ? existingClient.schedules : [],
      };

      const index = members.value.findIndex((entry) => String(entry.id) === String(normalized.id));
      if (index >= 0) {
        members.value[index] = normalized;
      } else {
        members.value.unshift(normalized);
      }
      persist();
      return normalized;
    }

    const fallbackId = clientPayload.id_usuario || `SGCLI${String(members.value.length + 1).padStart(3, '0')}`;
    const normalized = {
      id: fallbackId,
      id_cliente: Number(String(fallbackId).replace(/^SGCLI/i, '')) || members.value.length + 1,
      name: clientPayload.nombre,
      dni: clientPayload.dni,
      internalCode: fallbackId,
      email: clientPayload.correo,
      phone: clientPayload.telefono,
      role: 'user',
      plan: clientPayload.plan,
      planId: '',
      id_membresia: null,
      membershipStatus: clientPayload.estado,
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

    const index = members.value.findIndex((entry) => String(entry.id) === String(normalized.id));
    if (index >= 0) {
      members.value[index] = normalized;
    } else {
      members.value.unshift(normalized);
    }
    persist();
    return normalized;
  };

  const registerClienteMembresiaToServer = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/registro-cliente-membresia`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) });
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
      membershipStatus: client.membership_status || client.estado || '',
      membershipStart: client.membership_start || '',
      membershipEnd: client.membership_end || '',
      paymentStatus: client.payment_status || '',
      paymentReference: client.payment_reference || '',
      hasPassword: Boolean(client.has_password ?? client.hasPassword),
      membershipPrice: 0,
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
    const index = members.value.findIndex((entry) => String(entry.id) === String(normalized.id) || Number(entry.id_cliente) === Number(normalized.id_cliente));
    if (index >= 0) {
      members.value[index] = { ...members.value[index], ...normalized };
    } else {
      members.value.unshift(normalized);
    }
    persist();
    return normalized;
  };

  const registerPublicClient = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/registro-publico`, {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await readBackendError(res, 'No se pudo completar el registro'));

    const saved = await res.json();
    const membership = saved.membresia || {};
    return mergeClient({
      ...(saved.cliente || {}),
      id_membresia: membership.id_membresia,
      membership_status: membership.estado,
      membership_start: membership.fecha_inicio,
      membership_end: membership.fecha_fin,
      payment_status: membership.estado_pago,
      payment_reference: membership.referencia_pago,
    });
  };

  const confirmPublicPayment = async (idCliente, payload = {}) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/registro-publico/${idCliente}/pago`, {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify({
        metodo_pago: payload.metodo_pago || 'pasarela',
        referencia_pago: payload.referencia_pago || `WEB-${Date.now()}`,
      }),
    });
    if (!res.ok) throw new Error(await readBackendError(res, 'No se pudo confirmar el pago'));

    const saved = await res.json();
    const membership = saved.membresia || {};
    return mergeClient({
      ...(saved.cliente || {}),
      id_membresia: membership.id_membresia,
      membership_status: membership.estado,
      membership_start: membership.fecha_inicio,
      membership_end: membership.fecha_fin,
      payment_status: membership.estado_pago,
      payment_reference: membership.referencia_pago,
    });
  };

  const activateClientMembership = async (idCliente) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/clientes/${idCliente}/activar-membresia`, {
      method: 'POST',
      headers: _authHeaders(),
    });
    if (!res.ok) throw new Error(await readBackendError(res, 'No se pudo activar la membresía'));

    const saved = await res.json();
    const membership = saved.membresia || {};
    return mergeClient({
      ...(saved.cliente || {}),
      id_membresia: membership.id_membresia,
      membership_status: membership.estado,
      membership_start: membership.fecha_inicio,
      membership_end: membership.fecha_fin,
      payment_status: membership.estado_pago,
      payment_reference: membership.referencia_pago,
    });
  };

  const checkinByDniServer = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/asistencia/checkin-dni`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error(await readBackendError(res, 'Error en checkin por DNI'));
    return res.json();
  };

  const checkinByIdServer = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/asistencia/checkin`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error(await readBackendError(res, 'Error en checkin por cliente'));
    return res.json();
  };

  const registerAttendanceEntry = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/asistencia/entrada`, {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await readBackendError(res, 'No se pudo registrar entrada'));
    const saved = await res.json();
    return mergeAttendanceRecord(normalizeBackendAttendanceRecord(saved, members.value));
  };

  const registerAttendanceExit = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/asistencia/salida`, {
      method: 'POST',
      headers: _authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await readBackendError(res, 'No se pudo registrar salida'));
    const saved = await res.json();
    return mergeAttendanceRecord(normalizeBackendAttendanceRecord(saved, members.value));
  };

  const updateAttendanceRecord = async (idAsistencia, payload) => {
    const current = attendance.value.find((entry) => Number(entry.id_asistencia) === Number(idAsistencia) || entry.id === idAsistencia);
    if (!current) {
      throw new Error('Asistencia no encontrada');
    }

    const body = {
      id_cliente: payload.id_cliente || payload.memberCode || current.id_cliente_num || current.id_cliente || current.memberCode,
      fecha: payload.fecha || payload.date || current.date,
      hora: payload.hora || payload.time || current.time,
      servicio: payload.servicio || payload.service || current.service || 'fitness',
      id_usuario: payload.id_usuario || getCurrentRegistrarId(authStore) || undefined,
    };

    if (apiBase && current.id_asistencia) {
      const res = await fetch(`${apiBase}/asistencia/${current.id_asistencia}`, {
        method: 'PUT',
        headers: _authHeaders(),
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await readBackendError(res, 'Error al actualizar asistencia'));

      const saved = await res.json();
      return mergeAttendanceRecord(normalizeBackendAttendanceRecord(saved, members.value));
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
    const current = attendance.value.find((entry) => Number(entry.id_asistencia) === Number(idAsistencia) || entry.id === idAsistencia);
    if (!current) {
      throw new Error('Asistencia no encontrada');
    }

    if (apiBase && current.id_asistencia) {
      const res = await fetch(`${apiBase}/asistencia/${current.id_asistencia}`, {
        method: 'DELETE',
        headers: _authHeaders(),
      });
      if (!res.ok && res.status !== 204) throw new Error(await readBackendError(res, 'Error al eliminar asistencia'));
    }

    attendance.value = attendance.value.filter((entry) => {
      if (current.id_asistencia && entry.id_asistencia) {
        return Number(entry.id_asistencia) !== Number(current.id_asistencia);
      }

      return entry.id !== current.id;
    });
    persist();
  };

  const upsertInventoryToServer = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/inventario`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error('Error al guardar inventario');
    return res.json();
  };

  const upsertUserToServer = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/usuarios`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error('Error al guardar usuario');
    return res.json();
  };

  const deleteUserFromServer = async (idUsuario) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/usuarios/${encodeURIComponent(idUsuario)}`, { method: 'DELETE', headers: _authHeaders() });
    if (!res.ok && res.status !== 204) throw new Error('Error al eliminar usuario');
    return true;
  };

  const registrarMovimientoToServer = async (payload) => {
    if (!apiBase) throw new Error('No hay backend configurado');
    const res = await fetch(`${apiBase}/inventario/movimientos`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error('Error al crear movimiento de inventario');
    return res.json();
  };

  return {
    members,
    users,
    attendance,
    attendancePasses,
    planCatalog,
    promotions,
    routines,
    inventory,
    productos_tienda,
    storeOrders,
    cart,
    schedule,
    serviceSchedules,
    enrollments,
    stats,
    recentAttendance,
    attendanceAnalytics,
    activePlans,
    activePromotions,
    membershipAlerts,
    lowStockInventory,
    cartTotal,
    searchMembers,
    getPlanById,
    getPromotionById,
    isMembershipActive,
    isMembershipExpiringSoon,
    calculatePlanCharge,
    upsertPlan,
    upsertPromotion,
    upsertRutina,
    assignPlanToMember,
    renewMembership,
    attendanceByMemberRange,
    memberByInternalCode,
    recordAttendanceByCode,
    recordAttendanceByDni,
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
    upsertClient,
    deleteClient,
    recordAttendance,
    upsertInventoryItem,
    deleteInventoryItem,
    upsertProductoTienda,
    deleteProductoTienda,
    addToCart,
    removeFromCart,
    updateCartQuantity,
    clearCart,
    createStoreOrder,
    upsertUser,
    deleteUser,
    // Backend sync
    fetchFromBackend,
    refreshStoreProductsFromBackend,
    refreshStoreOrdersFromBackend,
    refreshAttendanceFromBackend,
    refreshServiceSchedulesFromBackend,
    upsertServiceSchedule,
    deleteServiceSchedule,
    refreshEnrollmentsFromBackend,
    enrollSchedule,
    deleteEnrollment,
    upsertClienteToServer,
    registerClienteMembresiaToServer,
    registerPublicClient,
    confirmPublicPayment,
    activateClientMembership,
    checkinByDniServer,
    checkinByIdServer,
    registerAttendanceEntry,
    registerAttendanceExit,
    updateAttendanceRecord,
    deleteAttendanceRecord,
    upsertInventoryToServer,
    upsertUserToServer,
    deleteUserFromServer,
    registrarMovimientoToServer,
  };
});
