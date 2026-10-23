import { normalizeMembershipStatus, clientMembershipGroup } from './clientDirectory.js';

export const PASS_EXPIRY_MINUTES = 10;

export const MEMBER_ALERT_DAYS = 7;

export const PLAN_DURATION_MONTHS = {
  'plan-monthly': 1,
  'plan-quarterly': 3,
  'plan-annual': 12,
};

export const seedState = () => ({
  planCatalog: [],
  promotions: [],
  members: [],
  users: [],
  attendance: [],
  attendancePasses: [],
  inventory: [],
  inventoryMovements: [],
  productos_tienda: [],
  storeOrders: [],
  cart: [],
  routines: [],
  schedule: [],
  serviceSchedules: [],
  enrollments: [],
  trainerOverview: null,
  gymSettings: {
    capacidad_total: 30,
    capacidad_por_hora: 10,
  },
});

export const todayISO = () => new Date().toISOString().slice(0, 10);

export const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export const nowISO = () => new Date().toISOString();

export const dateFromISO = (value) => new Date(`${value}T00:00:00`);

export const toISODate = (value) => value.toISOString().slice(0, 10);

export const addMonthsISO = (dateISO, months) => {
  const date = dateFromISO(dateISO);
  date.setMonth(date.getMonth() + months);
  return toISODate(date);
};

export const daysUntilISO = (dateISO) => {
  const diff = dateFromISO(dateISO).getTime() - dateFromISO(todayISO()).getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
};

export const planDurationById = (planId) => PLAN_DURATION_MONTHS[planId] || 1;

export const planNameById = (planId) =>
  ({
    'plan-monthly': 'Mensual',
    'plan-quarterly': 'Trimestral',
    'plan-annual': 'Anual',
  })[planId] || 'Mensual';

export const SECURE_CODE_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';

export const generateSecureCodeSegment = (length) => {
  const result = [];

  while (result.length < length) {
    const randomBytes = new Uint8Array(length - result.length);
    crypto.getRandomValues(randomBytes);

    for (const byte of randomBytes) {
      // Discard the incomplete range so every character has the same probability.
      if (byte >= 252) continue;
      result.push(SECURE_CODE_ALPHABET[byte % SECURE_CODE_ALPHABET.length]);
    }
  }

  return result.join('');
};

export const generateInventoryCode = () =>
  `INV-${Date.now().toString(36).toUpperCase()}-${generateSecureCodeSegment(3)}`;

export const normalizeInventoryItem = (item = {}) => ({
  ...item,
  inventoryCode: item.inventoryCode || (item.n_activo ? `ACT-${String(item.n_activo).padStart(4, '0')}` : `INV-${String(item.id || Date.now()).slice(-4).toUpperCase()}`),
  n_activo: item.n_activo || item.assetNumber || '',
  unidad_venta: item.unidad_venta || item.unit || 'unidad',
  precio_venta: Number(item.precio_venta ?? item.salePrice ?? 0),
  minQuantity: Number(item.minQuantity ?? item.stock_minimo ?? 1),
});

export const normalizeStoreOrder = (order = {}) => ({
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
  observacion_admin: order.observacion_admin || '',
  fecha_actualizacion: order.fecha_actualizacion || order.fecha_pedido || nowISO(),
  subtotal: Number(order.subtotal || 0),
  igv: Number(order.igv || 0),
  total: Number(order.total || 0),
  items: Array.isArray(order.items)
    ? order.items.map((item) => ({
      id_producto: Number(item.id_producto || 0),
      nombre_producto: item.nombre_producto || item.nombre || 'Producto',
      imagen_url: item.imagen_url || item.imageUrl || '',
      cantidad: Number(item.cantidad || 1),
      precio_unitario: Number(item.precio_unitario || item.precio || 0),
      subtotal: Number(item.subtotal || Number(item.precio_unitario || item.precio || 0) * Number(item.cantidad || 1)),
    }))
    : [],
});

export const normalizePlanFromBackend = (plan = {}) => {
  const idPm = Number(plan.id_pm || String(plan.id || '').match(/(\d+)/)?.[1] || Date.now());
  const durationNumber = Number(String(plan.duracion || plan.duration || '').match(/\d+/)?.[0] || plan.durationMonths || 1);
  return {
    id: `pm-${idPm}`,
    id_pm: idPm,
    name: plan.nombre_plan || plan.name || 'MENSUAL',
    duration: plan.duracion || `${durationNumber} dias`,
    durationMonths: durationNumber,
    price: Number(plan.precio ?? plan.price ?? 0),
    description: plan.descripcion || plan.description || '',
    benefits: plan.beneficios || plan.benefits || '',
    active: plan.activo !== false && plan.active !== false,
  };
};

export const normalizePromotionFromBackend = (promotion = {}) => {
  const idPromocion = Number(promotion.id_promocion || String(promotion.id || '').match(/(\d+)/)?.[1] || Date.now());
  const plans = Array.isArray(promotion.planes_aplicables)
    ? promotion.planes_aplicables.map((value) => `pm-${Number(value)}`).filter((value) => value !== 'pm-0')
    : Array.isArray(promotion.appliesTo)
      ? promotion.appliesTo
      : [];
  return {
    id: `promo-${idPromocion}`,
    id_promocion: idPromocion,
    name: promotion.nombre || promotion.name || 'Promocion',
    description: promotion.descripcion || promotion.note || '',
    discountType: promotion.tipo_descuento === 'monto' || promotion.discountType === 'fixed' ? 'fixed' : 'percent',
    discountValue: Number(promotion.valor_descuento ?? promotion.discountValue ?? 0),
    startsAt: promotion.fecha_inicio || promotion.startsAt || '',
    validUntil: promotion.fecha_fin || promotion.validUntil || '',
    icono_etiqueta: promotion.icono_etiqueta || promotion.badgeIcon || '🏷️',
    palabra_clave: promotion.palabra_clave || promotion.badgeTag || '',
    appliesTo: plans,
    limite_cupos: promotion.limite_cupos !== undefined && promotion.limite_cupos !== null && String(promotion.limite_cupos).trim() !== '' ? Number(promotion.limite_cupos) : null,
    usos_actuales: Number(promotion.usos_actuales ?? promotion.usesCount ?? 0),
    active: promotion.activo !== false && promotion.active !== false,
  };
};

export const normalizeStoreProductFromBackend = (product = {}) => ({
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
  imagen_url: product.imagen_url || product.imageUrl || '',
});

export const normalizeBackendClientToMember = (client = {}) => ({
  id: client.id_usuario || `cliente-${client.id_cliente || Date.now()}`,
  id_cliente:
    client.id_cliente || Number(String(client.id_usuario || '').match(/(?:SGCLI|cliente-)(\d+)/)?.[1] || 0) || null,
  name: client.nombre || `${client.nombres || ''} ${client.apellidos || ''}`.trim(),
  dni: client.dni || '',
  internalCode: String(client.id_usuario || client.id_cliente || '').trim(),
  email: client.correo || client.email || '',
  phone: client.telefono || client.phone || '',
  role: 'user',
  plan: client.plan || '',
  promocion: client.promocion || 'SIN PROMOCION',
  id_promocion: client.id_promocion || (client.promocion && String(client.promocion).startsWith('promo-') ? Number(String(client.promocion).replace('promo-', '')) : null),
  planId: '',
  id_membresia: client.id_membresia || null,
  membershipStatus: normalizeMembershipStatus(client.membership_status || client.estado),
  membershipStart: client.membership_start || client.fecha_inicio || client.fecha_registro || client.joinedAt || '',
  membershipEnd: client.membership_end || client.fecha_fin || '',
  registrationOrigin: client.origen_registro || '',
  paymentStatus: client.payment_status || client.estado_pago || '',
  paymentReference: client.payment_reference || client.referencia_pago || '',
  hasPassword: Boolean(client.has_password ?? client.hasPassword),
  membershipPrice: Number(client.monto_pago ?? 0),
  status: String(client.estado || (client.estado === false ? 'INACTIVO' : 'ACTIVO')).toUpperCase(),
  joinedAt: client.fecha_registro || client.joinedAt || '',
  attendanceRate: 0,
  membershipHistory: [],
  changeHistory: [],
  schedules: [],
});

export const normalizeUser = (user = {}) => {
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

export const normalizeMember = (member = {}) => {
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

export const normalizeAttendanceRecord = (entry = {}) => {
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

export const findMemberForAttendance = (entry = {}, memberList = []) => {
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

export const normalizeBackendAttendanceRecord = (entry = {}, memberList = []) => {
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

export const normalizeState = (state) => ({
  ...seedState(),
  ...state,
  members: Array.isArray(state?.members) ? state.members.map((member) => normalizeMember(member)) : seedState().members,
  users: Array.isArray(state?.users) ? state.users.map((user) => normalizeUser(user)) : seedState().users,
  planCatalog: Array.isArray(state?.planCatalog) ? state.planCatalog.map((plan) => normalizePlanFromBackend(plan)) : seedState().planCatalog,
  promotions: Array.isArray(state?.promotions) ? state.promotions.map((promotion) => normalizePromotionFromBackend(promotion)) : seedState().promotions,
  routines: Array.isArray(state?.routines) ? state.routines : seedState().routines,
  attendancePasses: Array.isArray(state?.attendancePasses) ? state.attendancePasses : [],
  attendance: Array.isArray(state?.attendance) ? state.attendance.map((entry) => normalizeAttendanceRecord(entry)) : seedState().attendance,
  inventory: Array.isArray(state?.inventory) ? state.inventory.map((item) => normalizeInventoryItem(item)) : seedState().inventory,
  inventoryMovements: Array.isArray(state?.inventoryMovements) ? state.inventoryMovements : seedState().inventoryMovements,
  productos_tienda: Array.isArray(state?.productos_tienda) ? state.productos_tienda : seedState().productos_tienda,
  storeOrders: Array.isArray(state?.storeOrders) ? state.storeOrders.map((order) => normalizeStoreOrder(order)) : seedState().storeOrders,
  cart: Array.isArray(state?.cart) ? state.cart : seedState().cart,
  serviceSchedules: Array.isArray(state?.serviceSchedules) ? state.serviceSchedules : seedState().serviceSchedules,
  enrollments: Array.isArray(state?.enrollments) ? state.enrollments : seedState().enrollments,
  gymSettings: state?.gymSettings && typeof state.gymSettings === 'object' ? state.gymSettings : seedState().gymSettings,
});

export const buildAttendanceRecord = (member, response = {}, fallback = {}) =>
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

export const getCurrentRegistrarId = (authStore) => authStore.user?.id_usuario || authStore.user?.id || authStore.user?.email || null;

export const getClientIdForBackend = (member) => {
  if (!member) return '';
  if (member.id_cliente) return String(member.id_cliente);
  if (member.id) return String(member.id);
  if (member.internalCode) return String(member.internalCode);
  return '';
};

export const generatePassCode = () => {
  const timeSegment = Date.now().toString(36).toUpperCase();
  const randomSegment = generateSecureCodeSegment(6);
  return `${timeSegment}-${randomSegment}`;
};

export const isPassExpired = (pass) => {
  if (!pass?.expiresAt) return true;
  return Date.now() > new Date(pass.expiresAt).getTime();
};

export const getPassPayload = (pass) =>
  JSON.stringify({
    gym: 'AC-Silver-s-GYM',
    passId: pass.id,
    memberId: pass.memberId,
    code: pass.code,
    issuedAt: pass.issuedAt,
    expiresAt: pass.expiresAt,
  });

export const parsePassInput = (input) => {
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

export const loadState = () => seedState();
