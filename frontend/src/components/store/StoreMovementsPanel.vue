<template>
  <div class="space-y-6">
    <section class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
        <p class="text-sm text-slate-400">Movimientos</p>
        <p class="mt-2 text-3xl font-black text-white">{{ activeMovements.length }}</p>
      </article>
      <article class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
        <p class="text-sm text-slate-400">Unidades vendidas</p>
        <p class="mt-2 text-3xl font-black text-rose-200">{{ soldUnits }}</p>
      </article>
      <article class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
        <p class="text-sm text-slate-400">Monto vendido</p>
        <p class="mt-2 text-3xl font-black text-emerald-300">S/. {{ soldAmount.toFixed(2) }}</p>
      </article>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
          <h2 class="mt-2 text-2xl font-black text-white">Salidas por ventas</h2>
          <p class="mt-1 text-sm text-slate-400">Cada producto vendido en un pedido descuenta stock de la tienda.</p>
        </div>
        <input v-model="search" class="field-input md:max-w-xs" placeholder="Buscar producto, cliente o pedido" />
      </div>

      <div v-if="filteredMovements.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[820px] text-left text-sm">
            <thead class="bg-slate-950/80 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3">Producto</th>
                <th class="px-4 py-3">Cantidad</th>
                <th class="px-4 py-3">Subtotal</th>
                <th class="px-4 py-3">Pedido</th>
                <th class="px-4 py-3">Cliente</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="movement in filteredMovements" :key="movement.key" :class="movement.isCancelled ? 'opacity-60' : ''">
                <td class="px-4 py-3 text-slate-300">{{ formatDate(movement.fecha) }}</td>
                <td class="px-4 py-3 font-bold text-white">{{ movement.producto }}</td>
                <td class="px-4 py-3 text-amber-200">-{{ movement.cantidad }}</td>
                <td class="px-4 py-3 text-emerald-300">S/. {{ movement.subtotal.toFixed(2) }}</td>
                <td class="px-4 py-3">
                  <p class="font-bold text-white">#{{ movement.idPedido }}</p>
                  <span class="mt-1 inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-black" :class="orderStatusClass(movement.estado)">{{ movement.estado }}</span>
                </td>
                <td class="px-4 py-3">
                  <p :class="movement.cliente ? 'font-semibold text-white' : 'italic text-slate-500'">{{ movement.cliente || 'Sin registrar' }}</p>
                  <p v-if="movement.clienteDni" class="mt-1 text-xs text-slate-400">DNI: {{ movement.clienteDni }}</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <p v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">Sin ventas registradas en la tienda.</p>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
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
  if (status === 'ENTREGADO') return 'bg-emerald-400/15 text-emerald-200';
  if (status === 'CANCELADO') return 'bg-slate-400/15 text-slate-300';
  if (status === 'CONFIRMADO') return 'bg-cyan-400/15 text-cyan-200';
  return 'bg-amber-400/15 text-amber-200';
};
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input::placeholder { color: #64748b; }
</style>
