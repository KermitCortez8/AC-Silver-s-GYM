<template>
  <div class="orders-theme space-y-6">
    <section class="ord-hero">
      <div class="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div class="flex items-start gap-4">
          <span class="ord-hero-icon"><ClipboardList :size="24" aria-hidden="true" /></span>
          <div>
            <p class="ord-eyebrow">Tienda &middot; Pedidos</p>
            <h1 class="ord-title">Pedidos de tienda</h1>
            <p class="ord-subtitle">Compras pagadas desde la tienda del cliente: confirma, entrega o cancela cada pedido.</p>
          </div>
        </div>
        <button type="button" class="ord-btn-secondary" @click="refresh()">
          <RefreshCw :size="16" aria-hidden="true" /> Actualizar
        </button>
      </div>
    </section>

    <section class="grid gap-3 sm:grid-cols-3">
      <article class="ord-stat">
        <span class="ord-stat-icon"><ClipboardList :size="20" aria-hidden="true" /></span>
        <div>
          <p class="ord-stat-label">Pedidos</p>
          <p class="ord-stat-value">{{ orders.length }}</p>
        </div>
      </article>
      <article class="ord-stat ord-stat--accent">
        <span class="ord-stat-icon"><Clock :size="20" aria-hidden="true" /></span>
        <div>
          <p class="ord-stat-label">Pendientes</p>
          <p class="ord-stat-value">{{ pendingOrders.length }}</p>
        </div>
      </article>
      <article class="ord-stat">
        <span class="ord-stat-icon"><Wallet :size="20" aria-hidden="true" /></span>
        <div>
          <p class="ord-stat-label">Ventas</p>
          <p class="ord-stat-value">S/. {{ totalSales.toFixed(2) }}</p>
        </div>
      </article>
    </section>

    <section class="ord-panel">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="ord-eyebrow">Historial</p>
          <h2 class="ord-panel-title">Pedidos registrados</h2>
        </div>
        <label class="ord-search w-full lg:max-w-md">
          <span class="sr-only">Buscar pedidos</span>
          <Search :size="16" class="ord-search-icon" aria-hidden="true" />
          <SearchInput v-model="search" class="ord-input" placeholder="Cliente, DNI, pedido o producto" />
        </label>
      </div>

      <p v-if="feedback" role="alert" class="ord-error mt-4">{{ feedback }}</p>

      <div v-if="filteredOrders.length" class="mt-5 space-y-4">
        <article v-for="order in paginatedOrders" :key="order.id_pedido" class="ord-card" :class="{ 'ord-card--cancelled': isCancelled(order) }">
          <div class="ord-card-head">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="ord-card-title">Pedido #{{ order.id_pedido }}</h3>
                <span class="ord-pill ord-pill--paid">{{ order.estado_pago }}</span>
                <span class="ord-pill" :class="statusPillClass(order.estado_pedido)">{{ order.estado_pedido }}</span>
              </div>
              <p class="ord-client">{{ clientOf(order).name || 'Sin registrar' }} &middot; {{ clientOf(order).email || 'Sin correo' }}</p>
              <p class="ord-meta">DNI: {{ clientOf(order).dni || 'No registrado' }} &middot; {{ formatDate(order.fecha_pedido) }}</p>
            </div>
            <div class="ord-total">
              <p class="ord-total-label">Total</p>
              <p class="ord-total-value">S/. {{ Number(order.total || 0).toFixed(2) }}</p>
            </div>
          </div>

          <div class="ord-items">
            <div class="ord-items-head">
              <span>Producto</span>
              <span>Cantidad</span>
              <span>Precio</span>
              <span class="text-right">Subtotal</span>
            </div>
            <div v-for="item in order.items" :key="`${order.id_pedido}-${item.id_producto}`" class="ord-item-row">
              <span class="ord-item-name">{{ item.nombre_producto }}</span>
              <span>{{ item.cantidad }}</span>
              <span>S/. {{ Number(item.precio_unitario || 0).toFixed(2) }}</span>
              <span class="ord-item-subtotal">S/. {{ Number(item.subtotal || 0).toFixed(2) }}</span>
            </div>
          </div>

          <div class="ord-manage">
            <label class="space-y-1.5">
              <span class="ord-field-label">Estado</span>
              <select v-model="ensureDraft(order).estado_pedido" class="ord-input" :disabled="isCancelled(order)">
                <option>PENDIENTE</option>
                <option>CONFIRMADO</option>
                <option>ENTREGADO</option>
                <option :disabled="!canCancel(order)">CANCELADO</option>
              </select>
              <span v-if="isCancelled(order)" class="ord-hint">Pedido cancelado: su stock ya fue devuelto.</span>
              <span v-else-if="!canCancel(order)" class="ord-hint">Solo se cancelan pedidos PENDIENTE.</span>
            </label>
            <label class="space-y-1.5">
              <span class="ord-field-label">Observacion</span>
              <input v-model="ensureDraft(order).observacion_admin" class="ord-input" placeholder="Entrega, recojo, incidencia o anulacion" />
            </label>
            <button type="button" class="ord-btn-primary" :disabled="savingOrders.has(order.id_pedido)" @click="updateOrder(order)">
              <Save :size="16" aria-hidden="true" /> {{ savingOrders.has(order.id_pedido) ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </article>
      </div>

      <!-- Paginacion: 10 pedidos por pagina por defecto. -->
      <div class="inv-store-theme">
        <TablePager
          v-model:page="paginaActual"
          v-model:pageSize="porPagina"
          :sizes="ORDER_PAGE_SIZES"
          :total="filteredOrders.length"
          item-label="pedidos"
        />
      </div>

      <div v-if="!filteredOrders.length" class="ord-empty">
        <ClipboardList :size="28" aria-hidden="true" />
        <p>{{ search ? 'Ningun pedido coincide con la busqueda.' : 'No hay pedidos para mostrar.' }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import SearchInput from "../components/SearchInput.vue";
import TablePager from "../components/common/TablePager.vue";
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { ClipboardList, Clock, RefreshCw, Save, Search, Wallet } from 'lucide-vue-next';
import { useGymStore } from '../../application/stores/gymStore';

const gymStore = useGymStore();
const search = ref('');
const feedback = ref('');
const savingOrders = reactive(new Set());
const orderDrafts = reactive({});

const orderStatus = (order) => String(order.estado_pedido || '').toUpperCase();
const isCancelled = (order) => orderStatus(order) === 'CANCELADO';
const canCancel = (order) => ['PENDIENTE', 'CANCELADO'].includes(orderStatus(order));

/**
 * Un pedido con tarjeta que aún no se cobró (o se abandonó) no se muestra: solo cuentan los pagados.
 */
const isPaid = (order) => String(order.estado_pago || 'PAGADO').toUpperCase() === 'PAGADO';

/**
 * Obtiene el cliente del pedido por su id_cliente (o DNI), con los datos del pedido como respaldo.
 */
const clientOf = (order) => {
  const dni = String(order.cliente_dni || '').trim();
  const member = (gymStore.members || []).find((entry) =>
    (order.id_cliente && Number(entry.id_cliente) === Number(order.id_cliente)) || (dni && entry.dni === dni));
  const savedName = order.cliente_nombre && order.cliente_nombre !== 'Cliente' ? order.cliente_nombre : '';
  return {
    name: member?.name || savedName,
    email: member?.email || order.cliente_correo || '',
    dni: dni || member?.dni || '',
  };
};

const orders = computed(() => (gymStore.storeOrders || [])
  .filter(isPaid)
  .sort((a, b) => String(b.fecha_pedido || '').localeCompare(String(a.fecha_pedido || ''))));
const pendingOrders = computed(() => orders.value.filter((order) => orderStatus(order) === 'PENDIENTE'));
// Las ventas son los pedidos cobrados que no se cancelaron.
const totalSales = computed(() => orders.value
  .filter((order) => !isCancelled(order))
  .reduce((sum, order) => sum + Number(order.total || 0), 0));

const normalizedSearch = computed(() => search.value.trim().toLowerCase());
const filteredOrders = computed(() => {
  if (!normalizedSearch.value) return orders.value;

  return orders.value.filter((order) => {
    const client = clientOf(order);
    return [
      order.id_pedido,
      client.name,
      client.email,
      client.dni,
      order.estado_pago,
      order.estado_pedido,
      ...(order.items || []).map((item) => item.nombre_producto),
    ]
      .join(' ')
      .toLowerCase()
      .includes(normalizedSearch.value);
  });
});

// Paginacion sobre la lista filtrada; vuelve a la primera pagina al buscar.
const paginaActual = ref(1);
// Pedidos muestra 10 por pagina (Inventario y Tienda usan 8).
const ORDER_PAGE_SIZES = [5, 8, 10, 50];
const porPagina = ref(ORDER_PAGE_SIZES[0]);
const paginatedOrders = computed(() => filteredOrders.value
  .slice((paginaActual.value - 1) * porPagina.value, paginaActual.value * porPagina.value));
watch(search, () => { paginaActual.value = 1; });
watch(() => filteredOrders.value.length, (total) => {
  const pages = Math.max(1, Math.ceil(total / porPagina.value));
  if (paginaActual.value > pages) paginaActual.value = pages;
});

// Color de la etiqueta segun el estado del pedido.
const statusPillClass = (status) => ({
  PENDIENTE: 'ord-pill--pending',
  CONFIRMADO: 'ord-pill--confirmed',
  ENTREGADO: 'ord-pill--delivered',
  CANCELADO: 'ord-pill--cancelled',
}[String(status || '').toUpperCase()] || 'ord-pill--pending');

/**
 * Gestiona esta acción de la vista.
 */
const ensureDraft = (order) => {
  if (!orderDrafts[order.id_pedido]) {
    orderDrafts[order.id_pedido] = {
      estado_pedido: order.estado_pedido || 'PENDIENTE',
      observacion_admin: order.observacion_admin || '',
    };
  }
  return orderDrafts[order.id_pedido];
};

watch(orders, (list) => {
  list.forEach((order) => {
    if (!orderDrafts[order.id_pedido]) {
      orderDrafts[order.id_pedido] = {
        estado_pedido: order.estado_pedido || 'PENDIENTE',
        observacion_admin: order.observacion_admin || '',
      };
    }
  });
}, { immediate: true });

/**
 * Formatea el valor para mostrarlo.
 */
const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  return new Date(value).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' });
};

/**
 * Actualiza los datos actuales.
 */
const refresh = async (force = true) => {
  feedback.value = '';
  try {
    await gymStore.fetchFromBackend({ section: 'orders', force });
  } catch (error) {
    feedback.value = error instanceof Error ? error.message : 'No se pudieron cargar los pedidos.';
  }
};

const updateOrder = async (order) => {
  if (savingOrders.has(order.id_pedido)) return;
  feedback.value = '';
  const draft = ensureDraft(order);
  if (draft.estado_pedido === 'CANCELADO' && !isCancelled(order)) {
    const unidades = (order.items || []).reduce((sum, item) => sum + Number(item.cantidad || 0), 0);
    const detalle = (order.items || []).map((item) => `- ${item.nombre_producto}: ${item.cantidad}`).join('\n');
    const ok = window.confirm(
      `Cancelar el pedido #${order.id_pedido}?\n\nSe devolveran ${unidades} unidades al stock de la Tienda:\n${detalle}\n\nUn pedido cancelado ya no puede cambiar de estado.`,
    );
    if (!ok) {
      draft.estado_pedido = order.estado_pedido || 'PENDIENTE';
      return;
    }
  }
  savingOrders.add(order.id_pedido);
  try {
    await gymStore.updateStoreOrderStatus(order.id_pedido, { ...draft });
  } catch (error) {
    feedback.value = error instanceof Error ? error.message : 'No se pudo actualizar el pedido.';
  } finally { savingOrders.delete(order.id_pedido); }
};

onMounted(() => refresh(false));
</script>
