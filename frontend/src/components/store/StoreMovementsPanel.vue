<template>
  <div class="space-y-6">
    <!-- Stats cards con iconos (estilo Inventario/Tienda) -->
    <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-blue-400 bg-slate-900/80 px-4 py-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
          <Activity :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Movimientos</p>
          <p class="text-2xl font-black text-white">{{ activeMovements.length }}</p>
        </div>
      </div>
      <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-rose-400 bg-slate-900/80 px-4 py-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
          <ShoppingBag :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Unidades vendidas</p>
          <p class="text-2xl font-black text-white">{{ soldUnits }}</p>
        </div>
      </div>
      <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-emerald-400 bg-slate-900/80 px-4 py-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600">
          <DollarSign :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Monto vendido</p>
          <p class="text-2xl font-black text-white">S/. {{ soldAmount.toFixed(2) }}</p>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
          <h2 class="mt-2 text-2xl font-black text-white">Salidas por ventas</h2>
          <p class="mt-1 text-sm text-slate-400">Cada producto vendido en un pedido descuenta stock de la tienda.</p>
        </div>
      </div>

      <!-- Buscador en fila (estilo Inventario) -->
      <div class="mt-4 grid gap-3 sm:max-w-md">
        <div class="flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3">
          <Search :size="16" class="shrink-0 text-slate-500" />
          <input v-model="search" @input="paginaActual = 1" class="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500" placeholder="Buscar producto, cliente o pedido..." />
        </div>
      </div>

      <p class="mt-3 text-xs text-slate-500">Mostrando {{ paginatedMovements.length }} de {{ filteredMovements.length }} movimientos</p>

      <div v-if="filteredMovements.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
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
                <td class="px-4 py-4 align-top font-bold text-amber-200">-{{ movement.cantidad }}</td>
                <td class="px-4 py-4 align-top font-black text-emerald-300">S/. {{ movement.subtotal.toFixed(2) }}</td>
                <td class="px-4 py-4 align-top">
                  <p class="font-bold text-white">#{{ movement.idPedido }}</p>
                  <span class="mt-1 inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-black" :class="orderStatusClass(movement.estado)">{{ movement.estado }}</span>
                </td>
                <td class="px-4 py-4 align-top">
                  <p :class="movement.cliente ? 'font-semibold text-white' : 'italic text-slate-500'">{{ movement.cliente || 'Sin registrar' }}</p>
                  <p v-if="movement.clienteDni" class="mt-1 text-xs text-slate-400">DNI: {{ movement.clienteDni }}</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Paginación -->
      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-between text-sm text-slate-400">
        <p>Mostrando {{ paginaInicio + 1 }} a {{ paginaFin }} de <span class="font-bold text-white">{{ filteredMovements.length }}</span> movimientos</p>
        <div class="flex items-center gap-2">
          <button
            class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-30"
            :disabled="paginaActual === 1"
            @click="paginaActual--"
          >Anterior</button>
          <button
            v-for="p in totalPages"
            :key="p"
            class="h-9 w-9 rounded-xl border text-sm font-bold transition"
            :class="p === paginaActual
              ? 'border-rose-500/40 bg-rose-600/20 text-rose-300'
              : 'border-white/10 text-white hover:bg-white/5'"
            @click="paginaActual = p"
          >{{ p }}</button>
          <button
            class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-30"
            :disabled="paginaActual === totalPages"
            @click="paginaActual++"
          >Siguiente</button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!filteredMovements.length" class="mt-6 rounded-2xl border border-dashed border-white/10 px-6 py-14 text-center">
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-slate-900">
          <svg class="h-6 w-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 3H8l-2 4h12l-2-4z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-slate-300">{{ search ? 'Sin resultados' : 'Sin ventas registradas' }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ search ? 'Prueba con otro termino de busqueda.' : 'No se han registrado ventas en la tienda todavia.' }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { Activity, ShoppingBag, DollarSign, Search } from 'lucide-vue-next';
import { useGymStore } from '../../stores/gymStore';

const gymStore = useGymStore();
const search = ref('');

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

const movements = computed(() =>
  (gymStore.storeOrders || [])
    .flatMap((order) => {
      const client = orderClient(order);
      return (order.items || []).map((item, index) => ({
        key: `${order.id_pedido}-${item.id_producto}-${index}`,
        fecha: order.fecha_pedido,
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
const activeMovements = computed(() => movements.value.filter((movement) => !movement.isCancelled));
const soldUnits = computed(() => activeMovements.value.reduce((sum, movement) => sum + movement.cantidad, 0));
const soldAmount = computed(() => activeMovements.value.reduce((sum, movement) => sum + movement.subtotal, 0));

const filteredMovements = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return movements.value;
  return movements.value.filter((movement) => [movement.producto, movement.cliente, movement.clienteDni, movement.idPedido, movement.estado].join(' ').toLowerCase().includes(query));
});

// Paginación
const paginaActual = ref(1);
const porPagina = 7;
const totalPages = computed(() => Math.ceil(filteredMovements.value.length / porPagina));
const paginaInicio = computed(() => (paginaActual.value - 1) * porPagina);
const paginaFin = computed(() => Math.min(paginaInicio.value + porPagina, filteredMovements.value.length));
const paginatedMovements = computed(() => filteredMovements.value.slice(paginaInicio.value, paginaFin.value));

/**
 * Formatea el valor para mostrarlo.
 */
const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  return new Date(value).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' });
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

<style scoped>
</style>
