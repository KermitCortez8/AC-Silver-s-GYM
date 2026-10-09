<template>
  <div class="space-y-6">
    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <section class="grid gap-5 xl:grid-cols-[420px_1fr]">
      <form class="h-fit rounded-2xl border border-white/10 bg-white/5 p-6" @submit.prevent="save">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ editingMovement ? 'Edicion' : 'Registro' }}</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ editingMovement ? `Editar movimiento #${editingMovement.id_mov}` : 'Nuevo movimiento' }}</h2>
        <div class="mt-5 space-y-4">
          <select v-model.number="form.id_item" class="field-input" :disabled="lockedByOrder">
            <option :value="0">Selecciona item</option>
            <option v-for="item in inventory" :key="item.id" :value="itemNumber(item)">
              {{ item.inventoryCode }} - {{ item.name }} ({{ item.quantity }})
            </option>
          </select>
          <select v-model="form.tipo_movimiento" class="field-input" :disabled="lockedByOrder">
            <option value="entrada">Entrada</option>
            <option value="salida">Salida</option>
            <option value="ajuste">Ajuste exacto</option>
          </select>
          <input v-model.number="form.cantidad" type="number" min="1" class="field-input" placeholder="Cantidad" :disabled="lockedByOrder" />
          <input v-model="form.fecha_movimiento" type="date" class="field-input" />
          <textarea v-model="form.descripcion" rows="3" class="field-input" placeholder="Motivo, proveedor, incidencia o venta manual"></textarea>
          <p v-if="lockedByOrder" class="rounded-2xl border border-sky-400/25 bg-sky-400/10 px-4 py-3 text-xs leading-5 text-sky-50">
            Movimiento generado por el pedido #{{ orderNumber(editingMovement) }}: solo puedes cambiar la fecha y la descripcion. La referencia al pedido se conserva.
          </p>
          <div v-if="selectedItem && !lockedByOrder" class="rounded-2xl border px-4 py-3 text-xs leading-5" :class="isSelectedTienda ? 'border-amber-400/25 bg-amber-400/10 text-amber-50' : 'border-white/10 bg-white/5 text-slate-300'">
            <p v-if="isSelectedTienda" class="font-bold">Este articulo se vende en Tienda: el cambio afectara el stock de Inventario y de Tienda.</p>
            <p>Stock actual: <span class="font-bold">{{ selectedItem.quantity }}</span> &rarr; quedara en <span class="font-bold" :class="projectedStock < 0 ? 'text-rose-300' : ''">{{ projectedStock }}</span></p>
            <p v-if="editingMovement" class="mt-1">Al guardar se revierte el efecto anterior del movimiento y se aplica el nuevo.</p>
            <p v-if="projectedStock < 0" class="mt-1 font-bold text-rose-300">No hay stock suficiente para este movimiento.</p>
          </div>
        </div>
        <button class="mt-5 w-full rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950">
          {{ editingMovement ? 'Guardar cambios' : 'Registrar movimiento' }}
        </button>
        <button v-if="editingMovement" type="button" class="mt-2 w-full rounded-2xl border border-white/10 px-4 py-3 text-sm font-bold text-white hover:bg-white/5" @click="resetForm">
          Cancelar edicion
        </button>
      </form>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
        <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Ultimos movimientos</h2>
          </div>
          <input v-model="search" class="field-input md:max-w-xs" placeholder="Buscar item, tipo o descripcion" />
        </div>

        <div v-if="filteredMovements.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10">
          <div class="overflow-x-auto">
            <table class="w-full min-w-[860px] text-left text-sm">
              <thead class="bg-slate-950/80 text-xs uppercase tracking-[0.16em] text-slate-400">
                <tr>
                  <th class="px-4 py-3">Fecha</th>
                  <th class="px-4 py-3">Item</th>
                  <th class="px-4 py-3">Tipo</th>
                  <th class="px-4 py-3">Cantidad</th>
                  <th class="px-4 py-3">Descripcion</th>
                  <th class="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/10">
                <tr v-for="movement in pageItems" :key="movement.id_mov" :class="editingMovement?.id_mov === movement.id_mov ? 'bg-amber-400/5' : ''">
                  <td class="px-4 py-3 text-slate-300">{{ movement.fecha_movimiento || 'Sin fecha' }}</td>
                  <td class="px-4 py-3 font-bold text-white">
                    {{ itemName(movement.id_item) }}
                    <span v-if="orderNumber(movement)" class="ml-2 rounded-full bg-sky-400/15 px-2 py-0.5 text-[11px] font-black text-sky-200">Pedido #{{ orderNumber(movement) }}</span>
                    <span v-else-if="!movement.id_usuario" class="ml-2 rounded-full bg-slate-400/15 px-2 py-0.5 text-[11px] font-black text-slate-300">Automatico</span>
                  </td>
                  <td class="px-4 py-3"><span class="rounded-full px-3 py-1 text-xs font-black" :class="movementClass(movement.tipo_movimiento)">{{ movement.tipo_movimiento }}</span></td>
                  <td class="px-4 py-3 text-amber-200">{{ movement.cantidad }}</td>
                  <td class="px-4 py-3 text-slate-400">{{ movement.descripcion || 'Sin descripcion' }}</td>
                  <td class="px-4 py-3 text-right">
                    <button type="button" class="rounded-xl border border-white/10 px-3 py-1.5 text-xs font-bold text-white transition hover:bg-white/5" @click="editMovement(movement)">
                      Editar
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">Sin movimientos registrados.</p>
        <TablePagination v-model:page="page" :page-count="pageCount" :total="filteredMovements.length" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { useAuthStore } from '../../stores/authStore';
import TablePagination from '../TablePagination.vue';
import { useTablePagination } from '../../composables/useTablePagination.js';
import { useGymStore } from '../../stores/gymStore';

// Mismo criterio que el backend para reconocer los movimientos generados por pedidos.
const ORDER_MOVEMENT = /^(?:Venta pedido|Devolución por cancelación del pedido) #(\d+)/;

const authStore = useAuthStore();
const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const search = ref('');
const editingMovement = ref(null);
const inventory = computed(() => gymStore.inventory);
const movements = computed(() => gymStore.inventoryMovements || []);
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const emptyForm = () => ({ id_item: 0, tipo_movimiento: 'entrada', cantidad: 1, fecha_movimiento: new Date().toISOString().slice(0, 10), descripcion: '' });
const form = reactive(emptyForm());

const itemNumber = (item) => Number(String(item.id).replace('item-', ''));
const itemsById = computed(() => new Map(inventory.value.map((item) => [itemNumber(item), item])));
const orderNumber = (movement) => String(movement?.descripcion || '').match(ORDER_MOVEMENT)?.[1] || '';
const lockedByOrder = computed(() => Boolean(editingMovement.value && orderNumber(editingMovement.value)));
const selectedItem = computed(() => itemsById.value.get(Number(form.id_item)) || null);
const isSelectedTienda = computed(() => String(selectedItem.value?.category || '').trim().toLowerCase() === 'tienda');

const effect = (tipo, cantidad) => (tipo === 'entrada' ? cantidad : -cantidad);
const projectedStock = computed(() => {
  const actual = Number(selectedItem.value?.quantity || 0);
  const cantidad = Math.max(1, Number(form.cantidad || 1));
  if (form.tipo_movimiento === 'ajuste') return cantidad;
  const original = editingMovement.value;
  // Al editar sobre el mismo item primero se revierte el efecto del movimiento original.
  const base = original && Number(original.id_item) === Number(form.id_item) && original.tipo_movimiento !== 'ajuste'
    ? actual - effect(original.tipo_movimiento, Number(original.cantidad || 0))
    : actual;
  return base + effect(form.tipo_movimiento, cantidad);
});

/**
 * Gestiona esta acción de la vista.
 */
const itemName = (idItem) => itemsById.value.get(Number(idItem))?.name || `Item #${idItem}`;
/**
 * Gestiona esta acción de la vista.
 */
const movementClass = (type) => type === 'entrada' ? 'bg-emerald-400/15 text-emerald-200' : type === 'salida' ? 'bg-rose-400/15 text-rose-200' : 'bg-cyan-400/15 text-cyan-200';
const filteredMovements = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return movements.value;
  return movements.value.filter((movement) => [itemName(movement.id_item), movement.tipo_movimiento, movement.descripcion].join(' ').toLowerCase().includes(query));
});
const { page, pageCount, pageItems } = useTablePagination(filteredMovements);

/**
 * Vuelve el formulario al registro de un movimiento nuevo.
 */
const resetForm = () => {
  editingMovement.value = null;
  Object.assign(form, emptyForm());
};

/**
 * Carga un movimiento en el formulario para corregirlo.
 */
const editMovement = (movement) => {
  editingMovement.value = { ...movement };
  Object.assign(form, {
    id_item: Number(movement.id_item),
    tipo_movimiento: movement.tipo_movimiento,
    cantidad: Number(movement.cantidad || 1),
    fecha_movimiento: movement.fecha_movimiento || new Date().toISOString().slice(0, 10),
    descripcion: movement.descripcion || '',
  });
  feedback.value = '';
};

/**
 * Gestiona esta acción de la vista.
 */
const save = async () => {
  try {
    if (!form.id_item) throw new Error('Selecciona un item de inventario.');
    if (!lockedByOrder.value && projectedStock.value < 0) throw new Error('No hay stock suficiente para este movimiento.');
    if (editingMovement.value) {
      const payload = lockedByOrder.value
        ? { fecha_movimiento: form.fecha_movimiento, descripcion: form.descripcion }
        : { ...form };
      await gymStore.updateInventoryMovement(editingMovement.value.id_mov, payload);
      feedback.value = 'Movimiento actualizado y stock recalculado.';
    } else {
      await gymStore.registrarMovimientoToServer({ ...form, id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1 });
      feedback.value = 'Movimiento registrado y stock actualizado.';
    }
    feedbackTone.value = 'success';
    resetForm();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar el movimiento.';
  }
};
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input:disabled { opacity: .6; cursor: not-allowed; }
.field-input::placeholder { color: #64748b; }
</style>
