<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Inventario</p>
      <h1 class="mt-2 text-3xl font-black text-white">Movimientos de stock</h1>
      <p class="mt-2 text-slate-300">Registra entradas, salidas y ajustes con trazabilidad operativa.</p>
    </section>

    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <section class="grid gap-5 xl:grid-cols-[420px_1fr]">
      <form class="h-fit rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="save">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Registro</p>
        <h2 class="mt-2 text-2xl font-black text-white">Nuevo movimiento</h2>
        <div class="mt-5 space-y-4">
          <select v-model.number="form.id_item" class="field-input">
            <option :value="0">Selecciona item</option>
            <option v-for="item in inventory" :key="item.id" :value="Number(String(item.id).replace('item-', ''))">
              {{ item.inventoryCode }} - {{ item.name }} ({{ item.quantity }})
            </option>
          </select>
          <select v-model="form.tipo_movimiento" class="field-input">
            <option value="entrada">Entrada</option>
            <option value="salida">Salida</option>
            <option value="ajuste">Ajuste exacto</option>
          </select>
          <input v-model.number="form.cantidad" type="number" min="1" class="field-input" placeholder="Cantidad" />
          <input v-model="form.fecha_movimiento" type="date" class="field-input" />
          <textarea v-model="form.descripcion" rows="3" class="field-input" placeholder="Motivo, proveedor, incidencia o venta manual"></textarea>
        </div>
        <button class="mt-5 w-full rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950">Registrar movimiento</button>
      </form>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Ultimos movimientos</h2>
          </div>
          <input v-model="search" class="field-input md:max-w-xs" placeholder="Buscar item, tipo o descripcion" />
        </div>

        <div v-if="filteredMovements.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10">
          <div class="overflow-x-auto">
            <table class="w-full min-w-[760px] text-left text-sm">
              <thead class="bg-slate-950/80 text-xs uppercase tracking-[0.16em] text-slate-400">
                <tr>
                  <th class="px-4 py-3">Fecha</th>
                  <th class="px-4 py-3">Item</th>
                  <th class="px-4 py-3">Tipo</th>
                  <th class="px-4 py-3">Cantidad</th>
                  <th class="px-4 py-3">Descripcion</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/10">
                <tr v-for="movement in filteredMovements" :key="movement.id_mov">
                  <td class="px-4 py-3 text-slate-300">{{ movement.fecha_movimiento || 'Sin fecha' }}</td>
                  <td class="px-4 py-3 font-bold text-white">{{ itemName(movement.id_item) }}</td>
                  <td class="px-4 py-3"><span class="rounded-full px-3 py-1 text-xs font-black" :class="movementClass(movement.tipo_movimiento)">{{ movement.tipo_movimiento }}</span></td>
                  <td class="px-4 py-3 text-amber-200">{{ movement.cantidad }}</td>
                  <td class="px-4 py-3 text-slate-400">{{ movement.descripcion || 'Sin descripcion' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">Sin movimientos registrados.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useAuthStore } from '../stores/authStore';
import { useGymStore } from '../stores/gymStore';

const authStore = useAuthStore();
const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const search = ref('');
const inventory = computed(() => gymStore.inventory);
const movements = computed(() => gymStore.inventoryMovements || []);
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const form = reactive({ id_item: 0, tipo_movimiento: 'entrada', cantidad: 1, fecha_movimiento: new Date().toISOString().slice(0, 10), descripcion: '' });

const itemName = (idItem) => inventory.value.find((item) => Number(String(item.id).replace('item-', '')) === Number(idItem))?.name || `Item #${idItem}`;
const movementClass = (type) => type === 'entrada' ? 'bg-emerald-400/15 text-emerald-200' : type === 'salida' ? 'bg-rose-400/15 text-rose-200' : 'bg-cyan-400/15 text-cyan-200';
const filteredMovements = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return movements.value;
  return movements.value.filter((movement) => [itemName(movement.id_item), movement.tipo_movimiento, movement.descripcion].join(' ').toLowerCase().includes(query));
});

const save = async () => {
  try {
    if (!form.id_item) throw new Error('Selecciona un item de inventario.');
    await gymStore.registrarMovimientoToServer({ ...form, id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1 });
    feedbackTone.value = 'success';
    feedback.value = 'Movimiento registrado y stock actualizado.';
    Object.assign(form, { id_item: 0, tipo_movimiento: 'entrada', cantidad: 1, fecha_movimiento: new Date().toISOString().slice(0, 10), descripcion: '' });
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo registrar el movimiento.';
  }
};

onMounted(() => gymStore.fetchFromBackend?.().catch(() => {}));
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input::placeholder { color: #64748b; }
</style>
