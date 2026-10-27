<template>
  <div class="space-y-6">
    <section class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border-l-4 border-l-blue-400 bg-slate-900/80 px-5 py-4">
        <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Enviado a Tienda</p>
        <p class="mt-1 text-3xl font-black text-white">{{ totals.sent }}</p>
        <p class="text-xs text-slate-500">unidades repuestas desde Inventario</p>
      </article>
      <article class="rounded-2xl border-l-4 border-l-green-400 bg-slate-900/80 px-5 py-4">
        <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Vendido</p>
        <p class="mt-1 text-3xl font-black text-white">{{ totals.sold }}</p>
        <p class="text-xs text-slate-500">unidades en pedidos no cancelados</p>
      </article>
      <article class="rounded-2xl border-l-4 border-l-orange-400 bg-slate-900/80 px-5 py-4">
        <p class="text-xs font-bold uppercase tracking-wide text-slate-400">En Tienda ahora</p>
        <p class="mt-1 text-3xl font-black text-white">{{ totals.inStore }}</p>
        <p class="text-xs text-slate-500">reserva en Inventario: {{ totals.reserve }}</p>
      </article>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Destino</p>
          <h2 class="mt-2 text-2xl font-black text-white">Que paso con los articulos de Tienda</h2>
          <p class="mt-1 text-sm text-slate-400">Cuanto salio de Inventario hacia Tienda y cuanto se vendio. Las fechas filtran reposiciones y ventas.</p>
        </div>
        <div class="grid gap-3 sm:grid-cols-3 lg:w-[620px]">
          <SearchInput v-model="search" class="field-input" placeholder="Artículo o producto vinculado" />
          <input v-model="dateFrom" type="date" class="field-input" title="Desde" />
          <input v-model="dateTo" type="date" class="field-input" title="Hasta" />
        </div>
      </div>

      <div v-if="filteredRows.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[860px] text-left text-sm">
            <thead class="bg-slate-950/80 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-4 py-3">Articulo</th>
                <th class="px-4 py-3 text-right">Reserva Inventario</th>
                <th class="px-4 py-3 text-right">Enviado a Tienda</th>
                <th class="px-4 py-3 text-right">Vendido</th>
                <th class="px-4 py-3 text-right">En Tienda</th>
                <th class="px-4 py-3">Ultima reposicion</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="row in filteredRows" :key="row.idItem" class="transition hover:bg-white/[0.04]">
                <td class="px-4 py-3">
                  <p class="font-bold text-white">{{ row.name }}</p>
                  <p class="text-xs text-slate-500">{{ row.productName ? `Producto: ${row.productName}` : 'Sin producto en Tienda' }}</p>
                </td>
                <td class="px-4 py-3 text-right font-bold text-slate-200">{{ row.reserve }}</td>
                <td class="px-4 py-3 text-right font-bold text-blue-300">{{ row.sent }}</td>
                <td class="px-4 py-3 text-right font-bold text-green-300">{{ row.sold }}</td>
                <td class="px-4 py-3 text-right">
                  <span class="font-bold" :class="row.isLow ? 'text-rose-500' : 'text-white'">{{ row.inStore }}</span>
                  <span v-if="row.isLow" class="ml-2 rounded-full bg-orange-100 px-2 py-0.5 text-[11px] font-black text-orange-800">Reponer</span>
                </td>
                <td class="px-4 py-3 text-slate-400">{{ row.lastRestock || 'Nunca' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <p v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
        No hay articulos Tipo Tienda para mostrar.
      </p>
    </section>
  </div>
</template>

<script setup>
import SearchInput from "../SearchInput.vue";
import { computed, ref } from 'vue';
import { useGymStore } from '../../../application/stores/gymStore';

const gymStore = useGymStore();
const search = ref('');
const dateFrom = ref('');
const dateTo = ref('');

const itemNumber = (item) => Number(String(item.id).replace('item-', ''));
const inRange = (date) => {
  const day = String(date || '').slice(0, 10);
  return (!dateFrom.value || day >= dateFrom.value) && (!dateTo.value || day <= dateTo.value);
};

// Reposiciones: salidas de MOV_INV con destino TIENDA, agrupadas por articulo.
const restocks = computed(() => {
  const byItem = new Map();
  (gymStore.inventoryMovements || []).forEach((movement) => {
    if (movement.tipo_movimiento !== 'salida' || String(movement.destino || '').toUpperCase() !== 'TIENDA') return;
    if (!inRange(movement.fecha_movimiento)) return;
    const entry = byItem.get(Number(movement.id_item)) || { units: 0, last: '' };
    entry.units += Number(movement.cantidad || 0);
    if (String(movement.fecha_movimiento || '') > entry.last) entry.last = String(movement.fecha_movimiento);
    byItem.set(Number(movement.id_item), entry);
  });
  return byItem;
});

// Ventas: lineas de pedidos no cancelados, agrupadas por producto.
const sales = computed(() => {
  const byProduct = new Map();
  (gymStore.storeOrders || []).forEach((order) => {
    if (String(order.estado_pedido || '').toUpperCase() === 'CANCELADO' || !inRange(order.fecha_pedido)) return;
    (order.items || []).forEach((line) => {
      const id = Number(line.id_producto);
      byProduct.set(id, (byProduct.get(id) || 0) + Number(line.cantidad || 0));
    });
  });
  return byProduct;
});

const rows = computed(() => (gymStore.inventory || [])
  .filter((item) => String(item.category || '').trim().toLowerCase() === 'tienda')
  .map((item) => {
    const idItem = itemNumber(item);
    const product = (gymStore.productos_tienda || []).find((entry) => Number(entry.id_item) === idItem);
    const restock = restocks.value.get(idItem);
    const inStore = Number(product?.cantidad || 0);
    return {
      idItem,
      name: item.name,
      productName: product?.nombre || '',
      reserve: Number(item.quantity || 0),
      sent: restock?.units || 0,
      sold: product ? sales.value.get(Number(product.id_producto)) || 0 : 0,
      inStore,
      isLow: Boolean(product) && inStore <= Number(product.minimo || 0),
      lastRestock: restock?.last || '',
    };
  })
  .sort((a, b) => b.sent + b.sold - (a.sent + a.sold) || a.name.localeCompare(b.name)));

const filteredRows = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return rows.value;
  return rows.value.filter((row) => `${row.name} ${row.productName}`.toLowerCase().includes(query));
});

const totals = computed(() => filteredRows.value.reduce((sum, row) => ({
  sent: sum.sent + row.sent,
  sold: sum.sold + row.sold,
  inStore: sum.inStore + row.inStore,
  reserve: sum.reserve + row.reserve,
}), { sent: 0, sold: 0, inStore: 0, reserve: 0 }));
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input::placeholder { color: #64748b; }
</style>
