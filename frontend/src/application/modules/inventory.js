import { requireList, requireRecord } from '../services/responseValidation.js';
import { parseQuantity } from '../../domain/utils/quantities.js';
import { refreshAfterMutation } from '../services/refreshAfterMutation.js';
import { bindSessionRepository } from '../services/sessionBoundary.js';
/** Estado y operaciones del módulo inventory. */
import { generateInventoryCode, requireNumericId } from '../../domain/utils/gymRules.js';
import { isUnitCategory } from '../../domain/utils/inventoryUnits.js';
import { computed } from 'vue';

export const createInventoryModule = (ctx, repository) => {
  const remote = bindSessionRepository(repository, () => ctx.authStore.token, ctx.pinia);
  // Después de guardar se recarga solo lo que la operación pudo cambiar (ver SYNC_SECTIONS).
  const refreshSection = (section) => () => ctx.fetchFromBackend({ section, force: true });
  const isStoreCategory = (category) => String(category || '').trim().toLowerCase() === 'tienda';
  const itemById = (idItem) => ctx.inventory.value.find((entry) => entry.id === `item-${idItem}`);
  // Sección para un movimiento: Tienda toca productos; equipos con unidades tocan unidades.
  const movementSection = ({ tipo, destino, idItem }) => {
    if (String(destino || '').toUpperCase() === 'TIENDA') return 'inventoryStore';
    if (tipo === 'traslado') return 'inventoryUnitsHistory';
    return itemById(idItem)?.byUnit ? 'inventory' : 'inventoryHistory';
  };
  const lowStockInventory = computed(() =>
    ctx.inventory.value.filter((item) => !item.archived && item.quantity <= item.minQuantity),
  );

  const upsertInventoryItem = (payload) => {
    payload = { ...payload, quantity: parseQuantity(payload.quantity ?? 0), minQuantity: parseQuantity(payload.minQuantity ?? payload.stock_minimo ?? 1) };
    if (ctx.apiBase) {
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
        requireRecord(res, 'id_item');
        const id_item = requireNumericId(res.id_item, 'un artículo');
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
        const index = ctx.inventory.value.findIndex((entry) => entry.id === item.id);
        if (index >= 0) ctx.inventory.value[index] = item; else ctx.inventory.value.unshift(item);
        // El alta registra su entrada en MOV_INV; un ítem Tienda crea su producto y un equipo sus unidades.
        const section = isStoreCategory(item.category) ? 'inventoryStore' : isUnitCategory(item.category) ? 'inventory' : 'inventoryHistory';
        return refreshAfterMutation(ctx, refreshSection(section)).then(() => item);
      });
    }

    const existingItem = ctx.inventory.value.find((entry) => entry.id === payload.id);
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

    const index = ctx.inventory.value.findIndex((entry) => entry.id === item.id);
    if (index >= 0) {
      ctx.inventory.value[index] = item;
    } else {
      ctx.inventory.value.unshift(item);
    }
    return item;
  };

  const deleteInventoryItem = async (id) => {
    if (ctx.apiBase && /^item-\d+$/.test(id)) {
      const id_item = Number(id.split('-')[1]);
      const result = await remote.deleteInventoryItem(id_item);

      // Con historial o producto en tienda el backend no borra: lo archiva y deja de mostrarse.
      if (result?.accion === 'archivado') {
        const item = ctx.inventory.value.find((entry) => entry.id === id);
        if (item) Object.assign(item, { archived: true, status: result.item?.estado || item.status });
        // Archivar un ítem Tienda también archiva su producto.
        await refreshAfterMutation(ctx, refreshSection(isStoreCategory(item?.category) ? 'stockCatalog' : 'inventoryItems'));
        return result;
      }
    }
    ctx.inventory.value = ctx.inventory.value.filter((item) => item.id !== id);
    return null;
  };

  const refreshInventoryMovementsFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const response = await remote.refreshInventoryMovementsFromBackend();

    ctx.inventoryMovements.value = requireList(response, 'id_mov');
    return ctx.inventoryMovements.value;
  };

  const upsertInventoryToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return await remote.upsertInventoryToServer(payload);
  };

  const registrarMovimientoToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.registrarMovimientoToServer({ ...payload, cantidad: parseQuantity(payload.cantidad ?? 1, { min: 1 }) });
    requireRecord(saved);
    requireRecord(saved.movimiento, 'id_mov');
    // Un traslado de varias unidades devuelve un movimiento por unidad.
    ctx.inventoryMovements.value.unshift(...(Array.isArray(saved.movimientos) ? saved.movimientos : [saved.movimiento]));
    await refreshAfterMutation(ctx, refreshSection(movementSection({ tipo: payload.tipo_movimiento, destino: payload.destino, idItem: payload.id_item })));
    return saved;
  };

  const updateInventoryMovement = async (idMov, payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const body = payload.cantidad === undefined ? payload : { ...payload, cantidad: parseQuantity(payload.cantidad, { min: 1 }) };
    const previous = ctx.inventoryMovements.value.find((entry) => Number(entry.id_mov) === Number(idMov));
    const saved = await remote.updateInventoryMovement(idMov, body);
    requireRecord(saved);
    requireRecord(saved.movimiento, 'id_mov');
    // Si antes o después era una reposición, también cambió el stock de la Tienda.
    const touchedStore = [previous?.destino, saved.movimiento.destino, body.destino].some((value) => String(value || '').toUpperCase() === 'TIENDA');
    await refreshAfterMutation(ctx, refreshSection(touchedStore ? 'inventoryStore' : movementSection({ idItem: saved.movimiento.id_item })));
    return saved;
  };

  const updateInventoryUnit = async (idUnidad, payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const previous = (ctx.inventoryUnits?.value || []).find((entry) => Number(entry.id_unidad) === Number(idUnidad));
    const saved = requireRecord(await remote.updateInventoryUnit(idUnidad, payload), 'id_unidad');
    // Cambiar la ubicación registra un traslado; el estado solo cambia la unidad y su artículo.
    const moved = !previous || (payload.ubicacion !== undefined && payload.ubicacion !== previous.ubicacion);
    await refreshAfterMutation(ctx, refreshSection(moved ? 'inventory' : 'inventoryUnitState'));
    return saved;
  };

  // Dar de baja una unidad registra una salida de esa unidad; su historial se conserva.
  const retireInventoryUnit = async (idUnidad, motivo = '') => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.retireInventoryUnit(idUnidad, { motivo });
    requireRecord(saved);
    requireRecord(saved.movimiento, 'id_mov');
    await refreshAfterMutation(ctx, refreshSection('inventory'));
    return saved;
  };

  // Restablecer devuelve a servicio la misma unidad con una entrada de 1 en Movimientos.
  const restoreInventoryUnit = async (idUnidad, motivo = '') => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const saved = await remote.restoreInventoryUnit(idUnidad, { motivo });
    requireRecord(saved);
    requireRecord(saved.movimiento, 'id_mov');
    await refreshAfterMutation(ctx, refreshSection('inventory'));
    return saved;
  };

  return { lowStockInventory, upsertInventoryItem, deleteInventoryItem, refreshInventoryMovementsFromBackend, upsertInventoryToServer, registrarMovimientoToServer, updateInventoryMovement, updateInventoryUnit, retireInventoryUnit, restoreInventoryUnit };
};
