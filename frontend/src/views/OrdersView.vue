<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Pedidos</p>
          <h1 class="mt-2 text-3xl font-black text-white">Pedidos de tienda</h1>
          <p class="mt-2 text-slate-300">Compras generadas desde la tienda del cliente.</p>
        </div>
        <button class="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50" :disabled="isRefreshing" @click="refresh()">
          {{ isRefreshing ? 'Actualizando…' : 'Actualizar' }}
        </button>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
        <p class="text-sm text-slate-400">Pedidos</p>
        <p class="mt-2 text-3xl font-black text-white">{{ orders.length }}</p>
      </article>
      <article class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
        <p class="text-sm text-slate-400">Pendientes</p>
        <p class="mt-2 text-3xl font-black text-amber-300">{{ pendingOrders.length }}</p>
      </article>
      <article class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
        <p class="text-sm text-slate-400">Ventas</p>
        <p class="mt-2 text-3xl font-black text-emerald-300">S/. {{ totalSales.toFixed(2) }}</p>
      </article>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
          <h2 class="mt-2 text-2xl font-black text-white">Pedidos registrados</h2>
        </div>
        <label class="w-full space-y-2 lg:max-w-md">
          <span class="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Buscar</span>
          <input v-model="search" class="field-input" placeholder="Cliente, DNI, pedido o producto" />
        </label>
      </div>

      <p v-if="feedback" class="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">
        {{ feedback }}
      </p>

      <div v-if="filteredOrders.length" class="mt-5 space-y-4">
        <article v-for="order in pageItems" :key="order.id_pedido" class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-xl font-black text-white">Pedido #{{ order.id_pedido }}</h3>
                <span class="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-black text-emerald-100">{{ order.estado_pago }}</span>
                <span class="rounded-full bg-amber-400/15 px-3 py-1 text-xs font-black text-amber-100">{{ order.estado_pedido }}</span>
              </div>
              <p class="mt-2 text-sm text-slate-300">{{ clientOf(order).name || 'Sin registrar' }} - {{ clientOf(order).email || 'Sin correo' }}</p>
              <p class="mt-1 text-xs text-slate-500">DNI: {{ clientOf(order).dni || 'No registrado' }} | {{ formatDate(order.fecha_pedido) }}</p>
            </div>

            <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-right">
              <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Total</p>
              <p class="mt-1 text-2xl font-black text-amber-300">S/. {{ Number(order.total || 0).toFixed(2) }}</p>
            </div>
          </div>

          <div class="mt-4 grid gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 md:grid-cols-[180px_1fr_auto] md:items-end">
            <label class="space-y-2">
              <span class="text-xs uppercase tracking-[0.2em] text-slate-500">Estado</span>
              <select v-model="ensureDraft(order).estado_pedido" class="field-input" :disabled="isCancelled(order) || savingOrders.has(order.id_pedido)">
                <option>PENDIENTE</option>
                <option>CONFIRMADO</option>
                <option>ENTREGADO</option>
                <option :disabled="!canCancel(order)">CANCELADO</option>
              </select>
              <span v-if="isCancelled(order)" class="block text-[11px] text-slate-500">Pedido cancelado: su stock ya fue devuelto.</span>
              <span v-else-if="!canCancel(order)" class="block text-[11px] text-slate-500">Solo se cancelan pedidos PENDIENTE.</span>
            </label>
            <label class="space-y-2">
              <span class="text-xs uppercase tracking-[0.2em] text-slate-500">Observacion</span>
              <input v-model="ensureDraft(order).observacion_admin" class="field-input" :disabled="savingOrders.has(order.id_pedido)" placeholder="Entrega, recojo, incidencia o anulacion" />
            </label>
            <button class="rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950 disabled:cursor-not-allowed disabled:opacity-50" :disabled="savingOrders.has(order.id_pedido)" @click="updateOrder(order)">
              {{ savingOrders.has(order.id_pedido) ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>

          <div class="mt-5 overflow-hidden rounded-2xl border border-white/10">
            <div class="hidden grid-cols-[1fr_120px_130px_130px] bg-slate-900/80 px-4 py-3 text-xs uppercase tracking-[0.2em] text-slate-500 md:grid">
              <span>Producto</span>
              <span>Cantidad</span>
              <span>Precio</span>
              <span class="text-right">Subtotal</span>
            </div>
            <div class="divide-y divide-white/10">
              <div v-for="item in order.items" :key="`${order.id_pedido}-${item.id_producto}`" class="grid gap-2 px-4 py-3 text-sm text-slate-300 md:grid-cols-[1fr_120px_130px_130px]">
                <span class="font-bold text-white">{{ item.nombre_producto }}</span>
                <span>{{ item.cantidad }}</span>
                <span>S/. {{ Number(item.precio_unitario || 0).toFixed(2) }}</span>
                <span class="font-bold text-white md:text-right">S/. {{ Number(item.subtotal || 0).toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </article>
      </div>

      <p v-else class="mt-6 rounded-2xl border border-dashed border-white/10 p-10 text-center text-sm text-slate-400">
        No hay pedidos para mostrar.
      </p>
      <TablePagination v-model:page="page" :page-count="pageCount" :total="filteredOrders.length" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import TablePagination from '../components/TablePagination.vue';
import { useTablePagination } from '../composables/useTablePagination.js';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const search = ref('');
const feedback = ref('');
const orderDrafts = reactive({});
const isRefreshing = ref(false);
const savingOrders = reactive(new Set());
const clientsById = computed(() => new Map((gymStore.members || []).map((member) => [Number(member.id_cliente), member])));
const clientsByDni = computed(() => new Map((gymStore.members || []).filter((member) => member.dni).map((member) => [member.dni, member])));

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
  const member = (order.id_cliente && clientsById.value.get(Number(order.id_cliente))) || (dni && clientsByDni.value.get(dni));
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
// Los nombres y textos de búsqueda se preparan al cambiar los datos, no por tecla.
const searchableOrders = computed(() => orders.value.map((order) => {
  const client = clientOf(order);
  return {
    order,
    text: [
      order.id_pedido, client.name, client.email, client.dni,
      order.estado_pago, order.estado_pedido,
      ...(order.items || []).map((item) => item.nombre_producto),
    ].join(' ').toLowerCase(),
  };
}));
const filteredOrders = computed(() => {
  if (!normalizedSearch.value) return orders.value;
  return searchableOrders.value.filter(({ text }) => text.includes(normalizedSearch.value)).map(({ order }) => order);
});
const { page, pageCount, pageItems } = useTablePagination(filteredOrders, 10);

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

/**
 * Formatea el valor para mostrarlo.
 */
const dateFormatter = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' });
const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Sin fecha' : dateFormatter.format(date);
};

/**
 * Actualiza los datos actuales.
 */
const refresh = async (force = true) => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  feedback.value = '';
  try {
    await gymStore.fetchFromBackend({ section: 'orders', force });
  } catch (error) {
    feedback.value = error instanceof Error ? error.message : 'No se pudieron cargar los pedidos.';
  } finally {
    isRefreshing.value = false;
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
      `Cancelar el pedido #${order.id_pedido}?\n\nSe devolveran ${unidades} unidades al stock compartido de Inventario y Tienda:\n${detalle}\n\nUn pedido cancelado ya no puede cambiar de estado.`,
    );
    if (!ok) {
      draft.estado_pedido = order.estado_pedido || 'PENDIENTE';
      return;
    }
  }
  savingOrders.add(order.id_pedido);
  try {
    await gymStore.updateStoreOrderStatus(order.id_pedido, draft);
  } catch (error) {
    feedback.value = error instanceof Error ? error.message : 'No se pudo actualizar el pedido.';
  } finally {
    savingOrders.delete(order.id_pedido);
  }
};

onMounted(() => refresh(false));
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  background: rgba(2, 6, 23, 0.72);
  padding: 0.75rem 1rem;
  color: white;
  outline: none;
}

.field-input::placeholder {
  color: #64748b;
}
</style>
