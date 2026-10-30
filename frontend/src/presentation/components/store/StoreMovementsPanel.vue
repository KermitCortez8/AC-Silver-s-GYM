<template>
  <div class="space-y-6">
    <!-- Tarjetas del mes elegido en el filtro (o de todo el historial con "Todos los meses") -->
    <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-blue-400 bg-slate-900/80 px-4 py-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
          <Activity :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Ventas · {{ periodLabel }}</p>
          <p class="text-2xl font-black text-white">{{ activeMovements.length }}</p>
        </div>
      </div>
      <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-rose-400 bg-slate-900/80 px-4 py-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
          <ShoppingBag :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Unidades vendidas · {{ periodLabel }}</p>
          <p class="text-2xl font-black text-white">{{ soldUnits }}</p>
        </div>
      </div>
      <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-emerald-400 bg-slate-900/80 px-4 py-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600">
          <DollarSign :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Monto vendido · {{ periodLabel }}</p>
          <p class="text-2xl font-black text-white">S/. {{ soldAmount.toFixed(2) }}</p>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
          <h2 class="mt-2 text-2xl font-black text-white">Ventas</h2>
          <p class="mt-1 text-sm text-slate-400">Cada producto vendido en un pedido descuenta stock de la tienda.</p>
        </div>
        <button
          type="button"
          class="inline-flex items-center gap-2 self-start rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-50 sm:self-auto"
          :disabled="!filteredMovements.length || isExporting"
          @click="exportToExcel"
        >
          <FileSpreadsheet :size="18" aria-hidden="true" />
          {{ isExporting ? 'Exportando...' : 'Exportar a Excel' }}
        </button>
      </div>

      <!-- Buscador (solo nombre del producto) y filtros -->
      <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-[1.5fr_1fr_1fr_1fr]">
        <TableSearch
          v-model="search"
          label="Buscar ventas por nombre de producto"
          placeholder="Buscar por nombre de producto"
          @update:model-value="paginaActual = 1"
        />
        <select v-model="monthFilter" class="inv-input" aria-label="Filtrar por mes" @change="paginaActual = 1">
          <option :value="ALL_MONTHS">Todos los meses</option>
          <option v-for="month in monthOptions" :key="month.value" :value="month.value">{{ month.label }}</option>
        </select>
        <select v-model="orderFilter" class="inv-input" aria-label="Filtrar por pedido" @change="paginaActual = 1">
          <option value="">Todos los pedidos</option>
          <option v-for="order in orderOptions" :key="order" :value="order">Pedido #{{ order }}</option>
        </select>
        <select v-model="clientFilter" class="inv-input" aria-label="Filtrar por cliente" @change="paginaActual = 1">
          <option value="">Todos los clientes</option>
          <option v-for="client in clientOptions" :key="client" :value="client">{{ client }}</option>
        </select>
      </div>

      <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
        <p>{{ filteredMovements.length }} ventas · S/. {{ filteredAmount.toFixed(2) }} en el filtro</p>
        <button v-if="hasFilters" type="button" class="inv-btn-ghost" @click="clearFilters">Limpiar filtros</button>
      </div>
      <p v-if="exportNotice" role="status" class="inv-info mt-3">
        <Info :size="16" aria-hidden="true" />
        {{ exportNotice }}
      </p>

      <div v-if="filteredMovements.length" class="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[820px] text-left text-sm">
            <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-5 py-4 font-bold">Fecha</th>
                <th class="px-4 py-4 font-bold">Producto</th>
                <th class="px-4 py-4 font-bold">Cantidad</th>
                <th class="px-4 py-4 font-bold">Subtotal</th>
                <th class="px-4 py-4 font-bold">Pedido</th>
                <th class="px-4 py-4 font-bold">Cliente</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="movement in paginatedMovements" :key="movement.key" class="transition hover:bg-white/[0.04]" :class="movement.isCancelled ? 'opacity-60' : ''">
                <td class="px-5 py-4 align-top text-slate-300">{{ formatDate(movement.fecha) }}</td>
                <td class="px-4 py-4 align-top font-bold text-white">{{ movement.producto }}</td>
                <td class="px-4 py-4 align-top font-bold text-rose-300">-{{ movement.cantidad }}</td>
                <td class="px-4 py-4 align-top font-black text-emerald-300">S/. {{ movement.subtotal.toFixed(2) }}</td>
                <td class="px-4 py-4 align-top">
                  <p class="font-bold text-white">#{{ movement.idPedido }}</p>
                  <span class="mt-1 inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-black" :class="orderStatusClass(movement.estado)">{{ movement.estado }}</span>
                </td>
                <td class="px-4 py-4 align-top">
                  <p :class="movement.cliente ? 'font-semibold text-white' : 'italic text-slate-500'">{{ movement.cliente || NO_CLIENT }}</p>
                  <p v-if="movement.clienteDni" class="mt-1 text-xs text-slate-400">DNI: {{ movement.clienteDni }}</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <TablePager
        v-model:page="paginaActual"
        v-model:pageSize="porPagina"
        :total="filteredMovements.length"
        item-label="ventas"
      />

      <!-- Empty state -->
      <div v-if="!filteredMovements.length" class="mt-6 rounded-2xl border border-dashed border-white/10 px-6 py-14 text-center">
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-slate-900">
          <svg class="h-6 w-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 3H8l-2 4h12l-2-4z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-slate-300">{{ hasFilters ? 'Sin resultados' : `Sin ventas en ${periodLabel}` }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ hasFilters ? 'Prueba con otros filtros o termino de busqueda.' : 'No se han registrado ventas en la tienda todavia.' }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { Activity, DollarSign, FileSpreadsheet, Info, ShoppingBag } from 'lucide-vue-next';
import TablePager from '../common/TablePager.vue';
import TableSearch from '../common/TableSearch.vue';
import { limaDate } from '../../../domain/utils/dates.js';
import { DEFAULT_PAGE_SIZE, matchesSearch } from '../../../domain/utils/inputRules.js';
import { useGymStore } from '../../../application/stores/gymStore';

const NO_CLIENT = 'Sin registrar';
const gymStore = useGymStore();
const search = ref('');
// Por defecto se ve el mes en curso (hora de Lima); "Todos los meses" muestra el historial completo.
const ALL_MONTHS = 'all';
const currentMonth = limaDate().slice(0, 7);
const monthFilter = ref(currentMonth);
const orderFilter = ref('');
const clientFilter = ref('');

/**
 * Obtiene el cliente del pedido, completando sus datos con la lista de clientes.
 */
const orderClient = (order) => {
  const dni = String(order.cliente_dni || '').trim();
  const member = (gymStore.members || []).find((entry) =>
    (order.id_cliente && Number(entry.id_cliente) === Number(order.id_cliente)) || (dni && entry.dni === dni));
  const savedName = order.cliente_nombre && order.cliente_nombre !== 'Cliente' ? order.cliente_nombre : '';
  return { name: member?.name || savedName, dni: dni || member?.dni || '' };
};

// Mes civil del gimnasio (America/Lima) de una fecha de pedido, como "AAAA-MM".
const monthKey = (value) => (value ? limaDate(new Date(value)).slice(0, 7) : '');
const monthLabel = (key) => new Intl.DateTimeFormat('es-PE', { month: 'long', year: 'numeric', timeZone: 'UTC' })
  .format(new Date(`${key}-15T12:00:00Z`));

const movements = computed(() =>
  (gymStore.storeOrders || [])
    .flatMap((order) => {
      const client = orderClient(order);
      return (order.items || []).map((item, index) => ({
        key: `${order.id_pedido}-${item.id_producto}-${index}`,
        fecha: order.fecha_pedido,
        mes: monthKey(order.fecha_pedido),
        producto: item.nombre_producto || `Producto #${item.id_producto}`,
        cantidad: Number(item.cantidad || 0),
        subtotal: Number(item.subtotal || 0),
        idPedido: order.id_pedido,
        estado: String(order.estado_pedido || 'PENDIENTE').toUpperCase(),
        isCancelled: String(order.estado_pedido || '').toUpperCase() === 'CANCELADO',
        cliente: client.name,
        clienteDni: client.dni,
      }));
    })
    .sort((a, b) => String(b.fecha || '').localeCompare(String(a.fecha || ''))),
);
// Las tarjetas responden solo al mes elegido.
const isInMonth = (movement) => monthFilter.value === ALL_MONTHS || movement.mes === monthFilter.value;
const activeMovements = computed(() => movements.value.filter((movement) => !movement.isCancelled && isInMonth(movement)));
const soldUnits = computed(() => activeMovements.value.reduce((sum, movement) => sum + movement.cantidad, 0));
const soldAmount = computed(() => activeMovements.value.reduce((sum, movement) => sum + movement.subtotal, 0));

// Opciones de los desplegables a partir de las ventas existentes.
const monthOptions = computed(() => [...new Set([currentMonth, ...movements.value.map((movement) => movement.mes).filter(Boolean)])]
  .sort((a, b) => b.localeCompare(a))
  .map((value) => ({ value, label: monthLabel(value) })));
const orderOptions = computed(() => [...new Set(movements.value.map((movement) => movement.idPedido))]
  .sort((a, b) => Number(b) - Number(a)));
const clientOptions = computed(() => [...new Set(movements.value.map((movement) => movement.cliente || NO_CLIENT))]
  .sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' })));

// El buscador solo mira el nombre del producto; mes, pedido y cliente se filtran con sus desplegables.
const filteredMovements = computed(() => movements.value.filter((movement) =>
  matchesSearch(search.value, [movement.producto])
  && isInMonth(movement)
  && (!orderFilter.value || String(movement.idPedido) === String(orderFilter.value))
  && (!clientFilter.value || (movement.cliente || NO_CLIENT) === clientFilter.value)));
const filteredAmount = computed(() => filteredMovements.value
  .filter((movement) => !movement.isCancelled)
  .reduce((sum, movement) => sum + movement.subtotal, 0));
const hasFilters = computed(() => Boolean(search.value || monthFilter.value !== currentMonth || orderFilter.value || clientFilter.value));
const periodLabel = computed(() => (monthFilter.value === ALL_MONTHS ? 'historico' : monthLabel(monthFilter.value)));

const clearFilters = () => {
  search.value = '';
  monthFilter.value = currentMonth;
  orderFilter.value = '';
  clientFilter.value = '';
  paginaActual.value = 1;
};

// Paginación
const paginaActual = ref(1);
const porPagina = ref(DEFAULT_PAGE_SIZE);
const paginatedMovements = computed(() => filteredMovements.value.slice((paginaActual.value - 1) * porPagina.value, paginaActual.value * porPagina.value));

/**
 * Formatea el valor para mostrarlo.
 */
const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  return new Date(value).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Lima' });
};

/**
 * Exporta a Excel solo las ventas que se ven: las del mes elegido y los demas filtros.
 */
const isExporting = ref(false);
const exportNotice = ref('');
const exportToExcel = async () => {
  if (isExporting.value || !filteredMovements.value.length) return;
  isExporting.value = true;
  try {
    const XLSX = await import('xlsx');
    const sheet = XLSX.utils.json_to_sheet(filteredMovements.value.map((movement) => ({
      Fecha: formatDate(movement.fecha),
      Mes: movement.mes ? monthLabel(movement.mes) : '',
      Producto: movement.producto,
      Cantidad: movement.cantidad,
      'Subtotal (S/.)': Number(movement.subtotal.toFixed(2)),
      Pedido: movement.idPedido,
      Estado: movement.estado,
      Cliente: movement.cliente || NO_CLIENT,
      DNI: movement.clienteDni || '',
    })));
    sheet['!cols'] = [22, 16, 32, 10, 14, 10, 14, 28, 12].map((wch) => ({ wch }));
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, sheet, 'Ventas');
    XLSX.writeFile(workbook, `ventas-tienda-${monthFilter.value === ALL_MONTHS ? 'historico' : monthFilter.value}.xlsx`);
    exportNotice.value = `Se exportaron ${filteredMovements.value.length} ventas de ${periodLabel.value}.`;
  } catch (error) {
    exportNotice.value = error instanceof Error ? `No se pudo exportar: ${error.message}` : 'No se pudo exportar.';
  } finally {
    isExporting.value = false;
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const orderStatusClass = (status) => {
  if (status === 'ENTREGADO' || status === 'COMPLETADO') return 'ws-tint-success ws-success border ws-border-success';
  if (status === 'CANCELADO') return 'ws-tint-danger ws-danger border ws-border-danger';
  if (status === 'CONFIRMADO') return 'ws-tint-info ws-info border ws-border-info';
  return 'ws-tint-warning ws-warning border ws-border-warning';
};
</script>
