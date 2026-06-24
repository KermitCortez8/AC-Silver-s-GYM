import { supabase, useSupabaseData } from './supabaseClient';

const TABLES = {
  attendance: 'ASISTENCIA',
  clients: 'CLIENTES',
  inventory: 'INVENTARIO',
  memberships: 'MEMBRESIA',
  plans: 'PLANES_MEMBRESIA',
  routines: 'CATALOGO_RUTINA',
  schedules: 'HORARIO',
  saleDetails: 'DETALLE_VENTA',
  storeProducts: 'TIENDA_PRODUCTOS',
  users: 'USUARIO',
  sales: 'VENTAS',
};

const todayISO = () => new Date().toISOString().slice(0, 10);
const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const assertSupabaseData = () => {
  if (!useSupabaseData || !supabase) {
    throw new Error('Supabase Database no esta configurado');
  }
};

const throwIfError = ({ error }, fallback) => {
  if (error) {
    throw new Error(error.message || fallback);
  }
};

const one = async (query, fallback) => {
  const result = await query;
  throwIfError(result, fallback);
  return result.data;
};

const fullNameParts = (value = '') => {
  const parts = String(value || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length <= 1) {
    return { nombres: parts[0] || '', apellidos: '' };
  }
  return { nombres: parts.slice(0, -1).join(' '), apellidos: parts.slice(-1).join('') };
};

const normalizeBoolStatus = (value) => {
  if (typeof value === 'boolean') return value;
  const status = String(value || '').trim().toUpperCase();
  return !['INACTIVO', 'INACTIVA', 'PENDIENTE', 'PENDIENTE_PAGO', 'EN_TRAMITE', 'FALSE', '0'].includes(status);
};

export const mapSupabaseClient = (client = {}, membership = {}, plan = {}) => {
  const idCliente = client.id_cliente || null;
  const name = [client.Nombres, client.Apellidos].filter(Boolean).join(' ').trim();
  const isActive = client.Estado !== false;

  return {
    id: `SGCLI${String(idCliente || Date.now()).padStart(3, '0')}`,
    id_cliente: idCliente,
    name,
    dni: client.DNI || '',
    internalCode: `SGCLI${String(idCliente || '').padStart(3, '0')}`,
    email: client.Email || client.Correo || '',
    phone: client.Telefono ? String(client.Telefono) : '',
    role: 'user',
    plan: plan.Nombre_Plan || client.Plan || '',
    promocion: 'SIN PROMOCION',
    planId: plan.id_PM ? `pm-${plan.id_PM}` : '',
    id_membresia: membership.id_membresia || null,
    membershipStatus: membership.Estado || (isActive ? 'ACTIVO' : 'PENDIENTE_PAGO'),
    membershipStart: membership.Fecha_Inicio || client.Fecha_Registro || '',
    membershipEnd: membership.Fecha_Fin || '',
    paymentStatus: membership.Estado === 'ACTIVA' ? 'PAGADO' : 'PENDIENTE',
    paymentReference: '',
    hasPassword: false,
    membershipPrice: Number(plan.Precio || 0),
    status: isActive ? 'ACTIVO' : 'PENDIENTE_PAGO',
    joinedAt: client.Fecha_Registro || '',
    attendanceRate: 0,
    membershipHistory: [],
    changeHistory: [],
    schedules: [],
  };
};

export const mapSupabaseInventoryItem = (item = {}) => ({
  id: `item-${item.id_item}`,
  inventoryCode: `ACT-${String(item.N_ACTIVO || item.id_item || '').padStart(4, '0')}`,
  n_activo: item.N_ACTIVO || item.id_item || '',
  name: item.Nombre_item || '',
  category: item.Tipo || 'General',
  quantity: Number(item.Cantidad_Stock_E ?? 0),
  minQuantity: 1,
  unidad_venta: 'unidad',
  precio_venta: 0,
  location: 'Almacen',
  status: item.Estado || 'Operativo',
  observations: '',
});

export const mapSupabaseStoreProduct = (product = {}) => ({
  id: `producto-${product.id_producto}`,
  id_producto: product.id_producto,
  id_item: null,
  nombre: product.nombre_Producto || '',
  descripcion: '',
  categoria: product.categoria || 'General',
  unidad_venta: 'unidad',
  precio: Number(product.precio_Venta || 0),
  cantidad: Number(product.cantidad_stock || 0),
  minimo: Number(product.stock_minimo || 0),
  estado: Number(product.cantidad_stock || 0) > 0 ? 'Disponible' : 'Sin stock',
});

export const mapSupabaseAttendance = (entry = {}, member = null) => ({
  id: `asistencia-${entry.id_asistencia || Date.now()}`,
  id_asistencia: entry.id_asistencia || null,
  id_cliente: entry.id_cliente || '',
  id_cliente_num: entry.id_cliente || null,
  memberId: member?.id || `SGCLI${String(entry.id_cliente || '').padStart(3, '0')}`,
  memberName: member?.name || `Cliente ${entry.id_cliente || ''}`,
  memberCode: member?.internalCode || `SGCLI${String(entry.id_cliente || '').padStart(3, '0')}`,
  time: entry.Hora || '',
  date: entry.Fecha || '',
  service: 'fitness',
  registeredBy: '',
  idMembresia: entry.id_membresia || null,
  entryTime: entry.Hora || '',
  exitTime: '',
  validacion: entry.Validación,
});

export const fetchSupabaseGymData = async () => {
  assertSupabaseData();

  const [clients, memberships, plans, users, inventory, products, sales, routines, schedules, attendance] =
    await Promise.all([
      one(supabase.from(TABLES.clients).select('*').order('id_cliente', { ascending: false }), 'Error al cargar clientes'),
      one(supabase.from(TABLES.memberships).select('*').order('id_membresia', { ascending: false }), 'Error al cargar membresias'),
      one(supabase.from(TABLES.plans).select('*').order('id_PM', { ascending: true }), 'Error al cargar planes'),
      one(supabase.from(TABLES.users).select('*').order('id_usuario', { ascending: true }), 'Error al cargar usuarios'),
      one(supabase.from(TABLES.inventory).select('*').order('id_item', { ascending: true }), 'Error al cargar inventario'),
      one(supabase.from(TABLES.storeProducts).select('*').order('id_producto', { ascending: true }), 'Error al cargar productos'),
      one(supabase.from(TABLES.sales).select('*').order('id_venta', { ascending: false }), 'Error al cargar ventas'),
      one(supabase.from(TABLES.routines).select('*').order('id_rutina', { ascending: true }), 'Error al cargar rutinas'),
      one(supabase.from(TABLES.schedules).select('*').order('id_horario', { ascending: true }), 'Error al cargar horarios'),
      one(supabase.from(TABLES.attendance).select('*').order('Fecha', { ascending: false }), 'Error al cargar asistencia'),
    ]);

  const planById = new Map((plans || []).map((plan) => [Number(plan.id_PM), plan]));
  const latestMembershipByClient = new Map();
  (memberships || []).forEach((membership) => {
    if (!latestMembershipByClient.has(Number(membership.id_cliente))) {
      latestMembershipByClient.set(Number(membership.id_cliente), membership);
    }
  });

  const members = (clients || []).map((client) => {
    const membership = latestMembershipByClient.get(Number(client.id_cliente)) || {};
    return mapSupabaseClient(client, membership, planById.get(Number(membership.id_PM)) || {});
  });
  const memberByClientId = new Map(members.map((member) => [Number(member.id_cliente), member]));

  return {
    members,
    users: (users || []).map((user) => ({
      id_usuario: user.id_usuario,
      nombre: `Usuario ${user.id_usuario}`,
      correo: '',
      email: '',
      telefono: '',
      dni: user.DNI || '',
      rol: user.Rol || 'staff',
      estado: user.Estado,
      hasPassword: Boolean(user.Contraseña),
    })),
    inventory: (inventory || []).map(mapSupabaseInventoryItem),
    productos_tienda: (products || []).map(mapSupabaseStoreProduct),
    storeOrders: (sales || []).map((sale) => ({
      id: `pedido-${sale.id_venta}`,
      id_pedido: sale.id_venta,
      fecha_pedido: sale.Fecha_Venta,
      metodo_pago: sale.metodo_Pago || '',
      estado_pago: 'PAGADO',
      estado_pedido: 'COMPLETADO',
      subtotal: Number(sale.total_Venta || 0),
      igv: 0,
      total: Number(sale.total_Venta || 0),
      items: [],
    })),
    planCatalog: (plans || []).map((plan) => ({
      id: `pm-${plan.id_PM}`,
      id_pm: plan.id_PM,
      name: plan.Nombre_Plan,
      durationMonths: Number(String(plan.Duración || '').match(/\d+/)?.[0] || 1),
      price: Number(plan.Precio || 0),
      description: plan.Duración || '',
      active: true,
    })),
    routines: (routines || []).map((routine) => ({
      id_rutina: routine.id_rutina,
      nombre_rutina: routine.Nombre_rutina,
      zonas_musculares: routine.Zonas_musculares || '',
      color: routine.Color || 'Azul',
    })),
    schedule: (schedules || []).map((schedule) => ({
      id_horario: schedule.id_horario,
      id_cliente: schedule.id_cliente,
      id_rutina: schedule.id_rutina,
      dia_semana: schedule.Dia_semana,
      hora_inicio: schedule.Hora_inicio,
      hora_fin: schedule.Hora_fin,
    })),
    attendance: (attendance || []).map((entry) => mapSupabaseAttendance(entry, memberByClientId.get(Number(entry.id_cliente)))),
    serviceSchedules: [],
    enrollments: [],
  };
};

export const saveSupabaseClientWithMembership = async (payload, options = {}) => {
  assertSupabaseData();

  const { nombres, apellidos } = fullNameParts(payload.nombre || payload.name);
  const clientBody = {
    Nombres: nombres,
    Apellidos: apellidos,
    DNI: String(payload.dni || ''),
    Telefono: payload.telefono || payload.phone ? Number(payload.telefono || payload.phone) : null,
    Email: payload.correo || payload.email || '',
    Fecha_Registro: payload.fecha_registro || todayISO(),
    Estado: normalizeBoolStatus(payload.estado || options.clientStatus || 'ACTIVO'),
    Plan: payload.plan || 'MENSUAL',
    Correo: payload.correo || payload.email || '',
  };

  let client;
  if (payload.id_cliente) {
    client = await one(
      supabase.from(TABLES.clients).update(clientBody).eq('id_cliente', payload.id_cliente).select('*').single(),
      'Error al actualizar cliente',
    );
  } else {
    client = await one(
      supabase.from(TABLES.clients).insert(clientBody).select('*').single(),
      'Error al crear cliente',
    );
  }

  let membership = {};
  let plan = {};
  const planResult = await supabase
    .from(TABLES.plans)
    .select('*')
    .ilike('Nombre_Plan', payload.plan || 'MENSUAL')
    .maybeSingle();

  if (!planResult.error && planResult.data) {
    plan = planResult.data;
  }

  if (plan.id_PM || options.forceMembership) {
    const start = payload.membershipStart || payload.fecha_inicio || todayISO();
    const membershipBody = {
      Fecha_Inicio: start,
      Fecha_Fin: payload.membershipEnd || payload.fecha_fin || start,
      Estado: options.membershipStatus || payload.membershipStatus || 'PENDIENTE_PAGO',
      id_cliente: client.id_cliente,
      id_PM: plan.id_PM || null,
    };
    membership = await one(
      supabase.from(TABLES.memberships).insert(membershipBody).select('*').single(),
      'Error al crear membresia',
    );
  }

  return { cliente: client, membresia: membership, normalized: mapSupabaseClient(client, membership, plan) };
};

export const updateSupabaseMembershipStatus = async (idCliente, status = 'ACTIVA') => {
  assertSupabaseData();
  const currentMembership = await one(
    supabase
      .from(TABLES.memberships)
      .select('*')
      .eq('id_cliente', idCliente)
      .order('id_membresia', { ascending: false })
      .limit(1)
      .single(),
    'Error al buscar membresia',
  );
  const membership = await one(
    supabase
      .from(TABLES.memberships)
      .update({ Estado: status })
      .eq('id_membresia', currentMembership.id_membresia)
      .select('*')
      .single(),
    'Error al actualizar membresia',
  );
  const client = await one(
    supabase.from(TABLES.clients).update({ Estado: true }).eq('id_cliente', idCliente).select('*').single(),
    'Error al activar cliente',
  );
  return { cliente: client, membresia: membership, normalized: mapSupabaseClient(client, membership, {}) };
};

export const saveSupabaseInventoryItem = async (payload) => {
  assertSupabaseData();
  const body = {
    Nombre_item: payload.nombre_item || payload.name,
    Tipo: payload.tipo || payload.category || 'General',
    Cantidad_Stock_E: Number(payload.cantidad_stock ?? payload.quantity ?? 0),
    Estado: payload.estado || payload.status || 'Operativo',
    N_ACTIVO: payload.n_activo ? Number(payload.n_activo) : null,
  };
  const idItem = payload.id_item || (payload.id ? Number(String(payload.id).split('-').pop()) : null);
  const query = idItem
    ? supabase.from(TABLES.inventory).update(body).eq('id_item', idItem).select('*').single()
    : supabase.from(TABLES.inventory).insert(body).select('*').single();
  return mapSupabaseInventoryItem(await one(query, 'Error al guardar inventario'));
};

export const deleteSupabaseInventoryItem = async (id) => {
  assertSupabaseData();
  const idItem = Number(String(id).split('-').pop());
  throwIfError(await supabase.from(TABLES.inventory).delete().eq('id_item', idItem), 'Error al eliminar inventario');
};

export const saveSupabaseStoreProduct = async (payload) => {
  assertSupabaseData();
  const body = {
    nombre_Producto: payload.nombre || payload.nombre_producto || 'Sin nombre',
    categoria: payload.categoria || 'General',
    precio_Venta: Number(payload.precio ?? payload.precio_venta ?? 0),
    cantidad_stock: Number(payload.cantidad ?? payload.cantidad_stock ?? 0),
    stock_minimo: Number(payload.minimo ?? payload.stock_minimo ?? 5),
  };
  const query = payload.id_producto
    ? supabase.from(TABLES.storeProducts).update(body).eq('id_producto', payload.id_producto).select('*').single()
    : supabase.from(TABLES.storeProducts).insert(body).select('*').single();
  return mapSupabaseStoreProduct(await one(query, 'Error al guardar producto'));
};

export const deleteSupabaseStoreProduct = async (idProducto) => {
  assertSupabaseData();
  throwIfError(await supabase.from(TABLES.storeProducts).delete().eq('id_producto', idProducto), 'Error al eliminar producto');
};

export const saveSupabaseUser = async (payload) => {
  assertSupabaseData();
  const body = {
    DNI: payload.dni || payload.DNI || '',
    'Contraseña': payload.password || payload.contrasena || payload['Contraseña'] || '',
    Rol: payload.rol || payload.Rol || 'staff',
    Estado: payload.estado ?? payload.Estado ?? true,
  };
  const idUsuario = payload.id_usuario || null;
  const query = idUsuario
    ? supabase.from(TABLES.users).update(body).eq('id_usuario', idUsuario).select('*').single()
    : supabase.from(TABLES.users).insert(body).select('*').single();
  const user = await one(query, 'Error al guardar usuario');
  return {
    id_usuario: user.id_usuario,
    nombre: `Usuario ${user.id_usuario}`,
    correo: '',
    email: '',
    telefono: '',
    dni: user.DNI || '',
    rol: user.Rol || 'staff',
    estado: user.Estado,
    hasPassword: Boolean(user['Contraseña']),
  };
};

export const deleteSupabaseUser = async (idUsuario) => {
  assertSupabaseData();
  throwIfError(await supabase.from(TABLES.users).delete().eq('id_usuario', idUsuario), 'Error al eliminar usuario');
};

export const createSupabaseSale = async ({ items = [], metodo_pago = 'tarjeta' }) => {
  assertSupabaseData();
  const productIds = items.map((item) => Number(item.id_producto)).filter(Boolean);
  const products = await one(
    supabase.from(TABLES.storeProducts).select('*').in('id_producto', productIds),
    'Error al validar productos',
  );
  const byId = new Map((products || []).map((product) => [Number(product.id_producto), product]));
  const detailRows = [];
  let total = 0;

  for (const item of items) {
    const product = byId.get(Number(item.id_producto));
    if (!product) throw new Error(`Producto no encontrado: ${item.id_producto}`);
    const quantity = Math.max(1, Number(item.cantidad || 1));
    if (Number(product.cantidad_stock || 0) < quantity) throw new Error(`Stock insuficiente para ${product.nombre_Producto}`);
    const subtotal = Number(product.precio_Venta || 0) * quantity;
    total += subtotal;
    detailRows.push({
      Cantidad: quantity,
      Precio_Unitario: Number(product.precio_Venta || 0),
      Subtotal: subtotal,
      id_producto: product.id_producto,
    });
  }

  const sale = await one(
    supabase.from(TABLES.sales).insert({
      Fecha_Venta: todayISO(),
      total_Venta: total,
      metodo_Pago: metodo_pago,
    }).select('*').single(),
    'Error al registrar venta',
  );

  for (const detail of detailRows) {
    throwIfError(
      await supabase.from(TABLES.saleDetails).insert({ ...detail, id_venta: sale.id_venta }),
      'Error al registrar detalle de venta',
    );
    const product = byId.get(Number(detail.id_producto));
    throwIfError(
      await supabase
        .from(TABLES.storeProducts)
        .update({ cantidad_stock: Number(product.cantidad_stock || 0) - Number(detail.Cantidad || 0) })
        .eq('id_producto', detail.id_producto),
      'Error al actualizar stock',
    );
  }

  return {
    id_pedido: sale.id_venta,
    fecha_pedido: sale.Fecha_Venta,
    metodo_pago: sale.metodo_Pago,
    estado_pago: 'PAGADO',
    estado_pedido: 'COMPLETADO',
    subtotal: total,
    igv: 0,
    total,
    items: detailRows.map((detail) => ({
      id_producto: detail.id_producto,
      nombre_producto: byId.get(Number(detail.id_producto))?.nombre_Producto || '',
      cantidad: detail.Cantidad,
      precio_unitario: detail.Precio_Unitario,
      subtotal: detail.Subtotal,
    })),
  };
};

export const createSupabaseAttendance = async (payload) => {
  assertSupabaseData();
  const record = await one(
    supabase.from(TABLES.attendance).insert({
      id_cliente: Number(payload.id_cliente || payload.id_cliente_num || payload.memberCode),
      id_membresia: payload.id_membresia || payload.idMembresia || null,
      Fecha: payload.fecha || payload.date || todayISO(),
      Hora: payload.hora || payload.time || nowTime(),
      'Validación': payload.validacion ?? true,
    }).select('*').single(),
    'Error al registrar asistencia',
  );
  return mapSupabaseAttendance(record);
};

export const updateSupabaseAttendance = async (idAsistencia, payload) => {
  assertSupabaseData();
  const record = await one(
    supabase.from(TABLES.attendance).update({
      id_cliente: Number(payload.id_cliente || payload.memberCode),
      Fecha: payload.fecha || payload.date,
      Hora: payload.hora || payload.time,
      'Validación': payload.validacion ?? true,
    }).eq('id_asistencia', idAsistencia).select('*').single(),
    'Error al actualizar asistencia',
  );
  return mapSupabaseAttendance(record);
};

export const deleteSupabaseAttendance = async (idAsistencia) => {
  assertSupabaseData();
  throwIfError(await supabase.from(TABLES.attendance).delete().eq('id_asistencia', idAsistencia), 'Error al eliminar asistencia');
};
