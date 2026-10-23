import { refreshAfterMutation } from '../services/refreshAfterMutation.js';
import { bindSessionRepository } from '../services/sessionBoundary.js';
import { orderTotals, toCents } from '../../domain/utils/money.js';
/** Estado y operaciones del módulo store. */
import { normalizeStoreOrder, normalizeStoreProductFromBackend, nowISO } from '../../domain/utils/gymRules.js';
import { computed } from 'vue';

export const createStoreModule = (ctx, repository) => {
  const remote = bindSessionRepository(repository, () => ctx.authStore.token);
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
      imagen_url: payload.imagen_url || payload.imageUrl || '',
    };

    if (ctx.apiBase) {
      const body = {
        ...producto,
        id_producto: producto.id_producto || undefined,
      };

      const saved = await remote.upsertProductoTienda(body);

      const normalized = normalizeStoreProductFromBackend(saved);
      const id_producto = normalized.id_producto;

      const index = ctx.productos_tienda.value.findIndex((p) => p.id_producto === id_producto);
      if (index >= 0) {
        ctx.productos_tienda.value[index] = normalized;
      } else {
        ctx.productos_tienda.value.unshift(normalized);
      }

      // Un producto nuevo puede crear su reserva (vacia) en Inventario.
      await refreshAfterMutation(ctx, () => ctx.fetchFromBackend({ force: true }));
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
      minimo: Number(producto.stock_minimo || 0),
      estado: producto.estado,
      imagen_url: producto.imagen_url || '',
    };

    const index = ctx.productos_tienda.value.findIndex((p) => p.id_producto === id_producto);
    if (index >= 0) {
      ctx.productos_tienda.value[index] = normalized;
    } else {
      ctx.productos_tienda.value.unshift(normalized);
    }

    return normalized;
  };

  const deleteProductoTienda = async (id_producto) => {
    if (ctx.apiBase) {
      await remote.deleteProductoTienda(id_producto);
    }

    ctx.productos_tienda.value = ctx.productos_tienda.value.filter((p) => p.id_producto !== id_producto);
  };

  const addToCart = (producto, cantidad = 1) => {
    const existingItem = ctx.cart.value.find((item) => item.id_producto === producto.id_producto);

    if (existingItem) {
      existingItem.cantidad += cantidad;
    } else {
      ctx.cart.value.push({
        id_producto: producto.id_producto,
        nombre: producto.nombre,
        imagen_url: producto.imagen_url || '',
        precio: producto.precio,
        cantidad: Math.max(1, cantidad),
      });
    }
  };

  const removeFromCart = (id_producto) => {
    ctx.cart.value = ctx.cart.value.filter((item) => item.id_producto !== id_producto);
  };

  const updateCartQuantity = (id_producto, cantidad) => {
    const item = ctx.cart.value.find((item) => item.id_producto === id_producto);
    if (item) {
      item.cantidad = Math.max(1, cantidad);
    }
  };

  const clearCart = () => {
    ctx.cart.value = [];
  };

  const cartTotal = computed(() => orderTotals(ctx.cart.value));

  const mergeStoreOrder = (order) => {
    const normalized = normalizeStoreOrder(order);
    const index = ctx.storeOrders.value.findIndex((entry) => Number(entry.id_pedido) === Number(normalized.id_pedido));
    if (index >= 0) {
      ctx.storeOrders.value[index] = normalized;
    } else {
      ctx.storeOrders.value.unshift(normalized);
    }
    return normalized;
  };

  const refreshStoreProductsFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const list = await remote.refreshStoreProductsFromBackend();
    ctx.productos_tienda.value = list.map((product) => normalizeStoreProductFromBackend(product));
    return ctx.productos_tienda.value;
  };

  const refreshStoreOrdersFromBackend = async () => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const list = await remote.refreshStoreOrdersFromBackend();
    ctx.storeOrders.value = list.map((order) => normalizeStoreOrder(order));
    return ctx.storeOrders.value;
  };

  const updateStoreOrderStatus = async (idPedido, payload = {}) => {
    const body = {
      estado_pedido: String(payload.estado_pedido || payload.status || 'PENDIENTE').trim().toUpperCase(),
      observacion_admin: payload.observacion_admin || payload.note || '',
    };
    if (ctx.apiBase) {
      const response = await remote.updateStoreOrderStatus(idPedido, body);

      const saved = mergeStoreOrder(response);
      // Cancelar devuelve el stock a la Tienda.
      if (body.estado_pedido === 'CANCELADO') await refreshAfterMutation(ctx, () => ctx.fetchFromBackend({ force: true }));
      return saved;
    }
    const order = ctx.storeOrders.value.find((entry) => Number(entry.id_pedido) === Number(idPedido));
    if (!order) throw new Error('Pedido no encontrado');
    return mergeStoreOrder({ ...order, ...body, fecha_actualizacion: nowISO() });
  };

  const createStoreOrder = async (payload = {}) => {
    const items = Array.isArray(payload.items) && payload.items.length ? payload.items : ctx.cart.value;
    if (!items.length) {
      throw new Error('El carrito esta vacio');
    }

    const body = {
      id_cliente: payload.id_cliente || null,
      cliente_nombre: payload.cliente_nombre || payload.customerName || ctx.authStore.user?.name || 'Cliente',
      cliente_correo: payload.cliente_correo || payload.customerEmail || ctx.authStore.user?.email || '',
      cliente_dni: payload.cliente_dni || payload.dni || ctx.authStore.user?.dni || '',
      metodo_pago: payload.metodo_pago || 'tarjeta',
      referencia_pago: payload.referencia_pago || `WEB-${Date.now()}`,
      items: items.map((item) => ({
        id_producto: Number(item.id_producto),
        cantidad: Math.max(1, Number(item.cantidad || 1)),
      })),
    };

    if (ctx.apiBase) {
      const response = await remote.createStoreOrder(body);

      const saved = mergeStoreOrder(response);
      clearCart();
      await refreshAfterMutation(ctx, () => refreshStoreProductsFromBackend());
      return saved;
    }

    const orderItems = body.items.map((item) => {
      const product = ctx.productos_tienda.value.find((entry) => Number(entry.id_producto) === Number(item.id_producto));
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
        subtotal: toCents(product.precio || 0) * item.cantidad / 100,
      };
    });

    const totals = orderTotals(orderItems.map(item => ({ precio: item.precio_unitario, cantidad: item.cantidad })));
    const saved = mergeStoreOrder({
      id_pedido: Date.now(),
      ...body,
      fecha_pedido: nowISO(),
      estado_pago: 'PAGADO',
      estado_pedido: 'PENDIENTE',
      ...totals,
      items: orderItems,
    });
    clearCart();
    return saved;
  };

  const createStoreCheckout = async (payload = {}) => {
    const items = Array.isArray(payload.items) && payload.items.length ? payload.items : ctx.cart.value;
    if (!items.length) {
      throw new Error('El carrito esta vacio');
    }
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const body = {
      cliente_nombre: payload.cliente_nombre || payload.customerName || '',
      cliente_correo: payload.cliente_correo || payload.customerEmail || '',
      cliente_dni: payload.cliente_dni || payload.dni || '',
      items: items.map((item) => ({ id_producto: Number(item.id_producto), cantidad: Math.max(1, Number(item.cantidad ?? 1)) })),
    };
    const saved = await remote.createStoreCheckout(body);
    if (!saved?.payment?.checkout_url) {
      throw new Error('No se recibió el enlace de pago de Stripe.');
    }
    return saved;
  };

  const confirmStoreCheckoutReturn = async (sessionId) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const result = await remote.confirmStoreCheckoutReturn(sessionId);
    if (result.confirmed) {
      // El pago ya está registrado: el carrito debe quedar vacío y el stock mostrado debe actualizarse.
      clearCart();
      await refreshAfterMutation(ctx, () => refreshStoreProductsFromBackend());
    }
    return result;
  };

  const cancelStoreCheckout = async (idPedido) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');

    const result = await remote.cancelStoreCheckout(idPedido);
    const restored = [];
    const skipped = [];

    // El stock ya volvió: se recarga el catálogo para dejar el carrito con datos actuales.
    const refreshed = await refreshAfterMutation(ctx, () => refreshStoreProductsFromBackend());
    if (!refreshed) return { ...result, restored, skipped: result.items || [], refreshPending: true };

    if (result.cancelled && !result.already_cancelled) {
      clearCart();
      for (const line of result.items || []) {
        const product = ctx.productos_tienda.value.find((entry) => Number(entry.id_producto) === Number(line.id_producto));
        const requested = Number(line.cantidad || 0);
        const available = product && String(product.estado || 'Disponible') === 'Disponible' ? Number(product.cantidad || 0) : 0;
        const quantity = Math.min(requested, available);
        if (quantity > 0) {
          addToCart(product, quantity);
          restored.push({ id_producto: product.id_producto, nombre: product.nombre, cantidad: quantity });
        }
        if (quantity < requested) {
          skipped.push({
            id_producto: Number(line.id_producto),
            nombre: product?.nombre || `Producto #${line.id_producto}`,
            solicitado: requested,
            disponible: available,
          });
        }
      }
    }
    return { ...result, restored, skipped };
  };

  return { upsertProductoTienda, deleteProductoTienda, addToCart, removeFromCart, updateCartQuantity, clearCart, cartTotal, mergeStoreOrder, refreshStoreProductsFromBackend, refreshStoreOrdersFromBackend, updateStoreOrderStatus, createStoreOrder, createStoreCheckout, confirmStoreCheckoutReturn, cancelStoreCheckout };
};
