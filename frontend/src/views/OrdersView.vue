<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Pedidos</p>
          <h1 class="mt-2 text-3xl font-black text-white">Pedidos de tienda</h1>
          <p class="mt-2 text-slate-300">Compras generadas desde la tienda del cliente.</p>
        </div>
        <button class="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/10" @click="refresh">
          Actualizar
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

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
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
        <article v-for="order in filteredOrders" :key="order.id_pedido" class="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-xl font-black text-white">Pedido #{{ order.id_pedido }}</h3>
                <span class="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-black text-emerald-100">{{ order.estado_pago }}</span>
                <span class="rounded-full bg-amber-400/15 px-3 py-1 text-xs font-black text-amber-100">{{ order.estado_pedido }}</span>
              </div>
              <p class="mt-2 text-sm text-slate-300">{{ order.cliente_nombre }} - {{ order.cliente_correo || 'Sin correo' }}</p>
              <p class="mt-1 text-xs text-slate-500">DNI: {{ order.cliente_dni || 'No registrado' }} | {{ formatDate(order.fecha_pedido) }}</p>
            </div>

            <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-right">
              <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Total</p>
              <p class="mt-1 text-2xl font-black text-amber-300">S/. {{ Number(order.total || 0).toFixed(2) }}</p>
            </div>
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
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const search = ref('');
const feedback = ref('');

const orders = computed(() => [...gymStore.storeOrders].sort((a, b) => String(b.fecha_pedido || '').localeCompare(String(a.fecha_pedido || ''))));
const pendingOrders = computed(() => orders.value.filter((order) => String(order.estado_pedido || '').toUpperCase() === 'PENDIENTE'));
const totalSales = computed(() => orders.value.reduce((sum, order) => sum + Number(order.total || 0), 0));

const normalizedSearch = computed(() => search.value.trim().toLowerCase());
const filteredOrders = computed(() => {
  if (!normalizedSearch.value) return orders.value;

  return orders.value.filter((order) =>
    [
      order.id_pedido,
      order.cliente_nombre,
      order.cliente_correo,
      order.cliente_dni,
      order.estado_pago,
      order.estado_pedido,
      ...(order.items || []).map((item) => item.nombre_producto),
    ]
      .join(' ')
      .toLowerCase()
      .includes(normalizedSearch.value),
  );
});

const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  return new Date(value).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' });
};

const refresh = async () => {
  feedback.value = '';
  try {
    await gymStore.refreshStoreOrdersFromBackend?.();
  } catch (error) {
    feedback.value = error instanceof Error ? error.message : 'No se pudieron cargar los pedidos.';
  }
};

onMounted(refresh);
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
