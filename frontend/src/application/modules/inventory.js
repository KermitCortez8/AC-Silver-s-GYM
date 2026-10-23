/** Estado y operaciones del módulo inventory. */
import { generateInventoryCode } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';
import { backendRequest } from '../services/backendGateway.js';

export const createInventoryModule = (ctx) => {
  const lowStockInventory = computed(() =>
    ctx.inventory.value.filter((item) => item.quantity <= item.minQuantity),
  );

  const upsertInventoryItem = (payload) => {
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
        const index = ctx.inventory.value.findIndex((entry) => entry.id === item.id);
        if (index >= 0) ctx.inventory.value[index] = item; else ctx.inventory.value.unshift(item);
        // El alta registra su entrada en MOV_INV y un item Tipo Tienda crea su producto.
        return ctx.fetchFromBackend({ force: true }).catch(() => {}).then(() => item);
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
      const response = await backendRequest(`${ctx.apiBase}/inventario/${id_item}`, { method: 'DELETE', headers: ctx._authHeaders() });
      if (!response.ok) throw new Error(await ctx.readBackendError(response, 'No se pudo eliminar el articulo'));
      // Con historial o producto en tienda el backend no borra: lo marca como Descontinuado.
      const result = response.status === 204 ? null : await response.json();
      if (result?.accion === 'descontinuado') {
        const item = ctx.inventory.value.find((entry) => entry.id === id);
        if (item) item.status = result.item?.estado || 'Descontinuado';
        await ctx.fetchFromBackend({ force: true }).catch(() => {});
        return result;
      }
    }
    ctx.inventory.value = ctx.inventory.value.filter((item) => item.id !== id);
    return null;
  };

  const refreshInventoryMovementsFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const response = await backendRequest(`${ctx.apiBase}/inventario/movimientos`, { headers: ctx._authHeaders() });
    if (!response.ok) throw new Error(await ctx.readBackendError(response, 'Error al cargar movimientos'));
    ctx.inventoryMovements.value = await response.json();
    return ctx.inventoryMovements.value;
  };

  const upsertInventoryToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/inventario`, { method: 'POST', headers: ctx._authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error('Error al guardar inventario');
    return res.json();
  };

  const registrarMovimientoToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/inventario/movimientos`, { method: 'POST', headers: ctx._authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error(await ctx.readBackendError(res, 'Error al crear movimiento de inventario'));
    const saved = await res.json();
    if (saved?.movimiento) ctx.inventoryMovements.value.unshift(saved.movimiento);
    await ctx.fetchFromBackend({ force: true }).catch(() => { });
    return saved;
  };

  const updateInventoryMovement = async (idMov, payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/inventario/movimientos/${idMov}`, { method: 'PUT', headers: ctx._authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error(await ctx.readBackendError(res, 'No se pudo actualizar el movimiento'));
    const saved = await res.json();
    await ctx.fetchFromBackend({ force: true }).catch(() => {});
    return saved;
  };

  return { lowStockInventory, upsertInventoryItem, deleteInventoryItem, refreshInventoryMovementsFromBackend, upsertInventoryToServer, registrarMovimientoToServer, updateInventoryMovement };
};
