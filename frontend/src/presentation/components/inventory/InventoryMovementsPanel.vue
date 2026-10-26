<template>
  <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
        <h2 class="mt-2 text-2xl font-black text-white">Movimientos de inventario</h2>
        <p class="mt-1 text-sm text-slate-400">Entradas, salidas y ajustes. Una salida con destino Tienda repone el stock del producto.</p>
      </div>
      <button type="button" class="rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:scale-[1.02] hover:bg-amber-300" @click="openNew">
        + Registrar movimiento
      </button>
    </div>

    <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-[1.6fr_1fr_1fr_1fr_1fr]">
      <input v-model="search" class="field-input" placeholder="Buscar articulo o descripcion" />
      <select v-model="typeFilter" class="field-input">
        <option value="all">Todos los tipos</option>
        <option value="entrada">Entradas</option>
        <option value="salida">Salidas</option>
        <option value="ajuste">Ajustes</option>
      </select>
      <select v-model="destinationFilter" class="field-input">
        <option value="all">Todos los destinos</option>
        <option value="TIENDA">Tienda</option>
        <option value="VENTA">Venta</option>
        <option value="none">Sin destino</option>
      </select>
      <input v-model="dateFrom" type="date" class="field-input" title="Desde" />
      <input v-model="dateTo" type="date" class="field-input" title="Hasta" />
    </div>

    <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <p class="mt-4 text-xs text-slate-500">Mostrando {{ filteredMovements.length }} de {{ movements.length }} movimientos</p>

    <div v-if="filteredMovements.length" class="mt-3 overflow-hidden rounded-2xl border border-white/10">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="bg-slate-950/80 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <th class="px-4 py-3">Fecha</th>
              <th class="px-4 py-3">Articulo</th>
              <th class="px-4 py-3">Tipo</th>
              <th class="px-4 py-3">Cantidad</th>
              <th class="px-4 py-3">Destino</th>
              <th class="px-4 py-3">Descripcion</th>
              <th class="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="movement in filteredMovements" :key="movement.id_mov" class="transition hover:bg-white/[0.04]">
              <td class="whitespace-nowrap px-4 py-3 text-slate-300">{{ movement.fecha_movimiento || 'Sin fecha' }}</td>
              <td class="px-4 py-3 font-bold text-white">
                {{ itemName(movement.id_item) }}
                <span v-if="orderNumber(movement)" class="ml-2 rounded-full bg-sky-400/15 px-2 py-0.5 text-[11px] font-black text-sky-200">Pedido #{{ orderNumber(movement) }}</span>
                <span v-else-if="!movement.id_usuario" class="ml-2 rounded-full bg-slate-400/15 px-2 py-0.5 text-[11px] font-black text-slate-300">Automatico</span>
              </td>
              <td class="px-4 py-3"><span class="rounded-full px-3 py-1 text-xs font-black capitalize" :class="movementClass(movement.tipo_movimiento)">{{ movement.tipo_movimiento }}</span></td>
              <td class="px-4 py-3 font-bold text-amber-200">{{ signedQuantity(movement) }}</td>
              <td class="px-4 py-3">
                <span v-if="destinationOf(movement)" class="rounded-full px-3 py-1 text-xs font-black" :class="destinationClass(destinationOf(movement))">
                  {{ destinationLabel(destinationOf(movement)) }}
                </span>
                <span v-else class="text-xs text-slate-400">-</span>
              </td>
              <td class="max-w-md px-4 py-3 text-slate-400">{{ movement.descripcion || 'Sin descripcion' }}</td>
              <td class="px-4 py-3 text-right">
                <button type="button" class="rounded-xl border border-white/10 px-3 py-1.5 text-xs font-bold text-white transition hover:bg-white/10" @click="openEdit(movement)">
                  Editar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <p v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
      {{ movements.length ? 'Ningun movimiento coincide con los filtros.' : 'Sin movimientos registrados.' }}
    </p>

    <Teleport to="body">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm" @keydown.esc="closeModal">
        <form class="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl" @submit.prevent="save">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ editingMovement ? 'Edicion' : 'Registro' }}</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ editingMovement ? `Editar movimiento #${editingMovement.id_mov}` : 'Nuevo movimiento' }}</h2>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/10" @click="closeModal">
              Cerrar
            </button>
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Articulo</span>
              <select v-model.number="form.id_item" class="field-input" :disabled="lockedByOrder">
                <option :value="0">Selecciona un articulo</option>
                <option v-for="item in inventory" :key="item.id" :value="itemNumber(item)">
                  {{ item.inventoryCode }} - {{ item.name }} ({{ item.quantity }})
                </option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Tipo</span>
              <select v-model="form.tipo_movimiento" class="field-input" :disabled="lockedByOrder">
                <option value="entrada">Entrada</option>
                <option value="salida">Salida</option>
                <option value="ajuste">Ajuste exacto</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Cantidad</span>
              <input v-model.number="form.cantidad" type="number" min="1" class="field-input" :disabled="lockedByOrder" />
            </label>
            <label v-if="form.tipo_movimiento === 'salida'" class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Destino</span>
              <select v-if="!lockedByOrder" v-model="form.destino" class="field-input">
                <option value="">Sin destino (uso interno, merma, baja...)</option>
                <option value="TIENDA" :disabled="!linkedProduct">Tienda - reponer stock{{ linkedProduct ? '' : ' (sin producto enlazado)' }}</option>
              </select>
              <input v-else :value="destinationLabel(form.destino)" class="field-input" disabled />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Fecha</span>
              <input v-model="form.fecha_movimiento" type="date" class="field-input" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Descripcion</span>
              <textarea v-model="form.descripcion" rows="3" class="field-input" placeholder="Motivo, proveedor, incidencia o reposicion"></textarea>
            </label>
          </div>

          <p v-if="lockedByOrder" class="mt-4 rounded-2xl border border-sky-400/25 bg-sky-400/10 px-4 py-3 text-xs leading-5 text-sky-50">
            Movimiento de un pedido de Tienda: solo puedes cambiar la fecha y la descripcion. La referencia al pedido se conserva.
          </p>
          <div v-else-if="selectedItem" class="mt-4 space-y-1 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs leading-5 text-slate-300">
            <p>Inventario: <span class="font-bold">{{ selectedItem.quantity }}</span> &rarr; quedara en <span class="font-bold" :class="projectedStock < 0 ? 'text-rose-500' : ''">{{ projectedStock }}</span></p>
            <p v-if="linkedProduct && (isRestock || wasRestockOfSelected)">
              Tienda ({{ linkedProduct.nombre }}): <span class="font-bold">{{ linkedProduct.cantidad }}</span> &rarr; quedara en <span class="font-bold" :class="projectedStoreStock < 0 ? 'text-rose-500' : ''">{{ projectedStoreStock }}</span>
            </p>
            <p v-if="editingMovement">Al guardar se revierte el efecto anterior del movimiento y se aplica el nuevo.</p>
            <p v-if="projectedStock < 0" class="font-bold text-rose-500">No hay stock suficiente en Inventario.</p>
            <p v-if="projectedStoreStock < 0" class="font-bold text-rose-500">La Tienda ya vendio esas unidades; no puedes reducir la reposicion.</p>
          </div>

          <p v-if="modalError" class="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">{{ modalError }}</p>

          <button type="submit" class="mt-5 w-full rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300 disabled:opacity-60" :disabled="isSaving">
            {{ isSaving ? 'Guardando...' : editingMovement ? 'Guardar cambios' : 'Registrar movimiento' }}
          </button>
        </form>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { limaDate } from '../../../domain/utils/dates.js';
import { computed, reactive, ref } from 'vue';
import { useAuthStore } from '../../../application/stores/authStore';
import { useGymStore } from '../../../application/stores/gymStore';

// Mismo criterio que el backend para reconocer los movimientos generados por pedidos.
const ORDER_MOVEMENT = /^(?:Venta pedido|Devolución por cancelación del pedido) #(\d+)/;

const authStore = useAuthStore();
const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const modalError = ref('');
const isModalOpen = ref(false);
const isSaving = ref(false);
const search = ref('');
const typeFilter = ref('all');
const destinationFilter = ref('all');
const dateFrom = ref('');
const dateTo = ref('');
const editingMovement = ref(null);
const inventory = computed(() => gymStore.inventory);
const products = computed(() => gymStore.productos_tienda || []);
const movements = computed(() => gymStore.inventoryMovements || []);
const feedbackClass = computed(() => feedbackTone.value === 'error'
  ? 'border-rose-400/20 bg-rose-400/10 text-rose-50'
  : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const today = () => limaDate();
const emptyForm = () => ({ id_item: 0, tipo_movimiento: 'entrada', cantidad: 1, destino: '', fecha_movimiento: today(), descripcion: '' });
const form = reactive(emptyForm());

const itemNumber = (item) => Number(String(item.id).replace('item-', ''));
const orderNumber = (movement) => String(movement?.descripcion || '').match(ORDER_MOVEMENT)?.[1] || '';
// Los movimientos de pedidos de la etapa de stock compartido tienen destino VENTA.
const destinationOf = (movement) => String(movement?.destino || '').toUpperCase() || (orderNumber(movement) ? 'VENTA' : '');
const lockedByOrder = computed(() => Boolean(editingMovement.value && destinationOf(editingMovement.value) === 'VENTA'));
const selectedItem = computed(() => inventory.value.find((item) => itemNumber(item) === Number(form.id_item)) || null);
const productForItem = (idItem) => products.value.find((product) => Number(product.id_item) === Number(idItem)) || null;
const linkedProduct = computed(() => productForItem(form.id_item));
const isRestock = computed(() => form.tipo_movimiento === 'salida' && form.destino === 'TIENDA');
const wasRestockOfSelected = computed(() => {
  const original = editingMovement.value;
  return Boolean(original && Number(original.id_item) === Number(form.id_item) && original.tipo_movimiento === 'salida' && destinationOf(original) === 'TIENDA');
});

const effect = (tipo, cantidad) => (tipo === 'entrada' ? cantidad : -cantidad);
const projectedStock = computed(() => {
  const actual = Number(selectedItem.value?.quantity || 0);
  const cantidad = Math.max(1, Number(form.cantidad || 1));
  if (form.tipo_movimiento === 'ajuste') return cantidad;
  const original = editingMovement.value;
  // Al editar sobre el mismo articulo primero se revierte el efecto del movimiento original.
  const base = original && Number(original.id_item) === Number(form.id_item) && original.tipo_movimiento !== 'ajuste'
    ? actual - effect(original.tipo_movimiento, Number(original.cantidad || 0))
    : actual;
  return base + effect(form.tipo_movimiento, cantidad);
});
const projectedStoreStock = computed(() => {
  if (!linkedProduct.value) return 0;
  const original = editingMovement.value;
  const base = Number(linkedProduct.value.cantidad || 0) - (wasRestockOfSelected.value ? Number(original.cantidad || 0) : 0);
  return base + (isRestock.value ? Math.max(1, Number(form.cantidad || 1)) : 0);
});

/**
 * Gestiona esta acción de la vista.
 */
const itemName = (idItem) => inventory.value.find((item) => itemNumber(item) === Number(idItem))?.name || `Item #${idItem}`;
const signedQuantity = (movement) => {
  if (movement.tipo_movimiento === 'entrada') return `+${movement.cantidad}`;
  if (movement.tipo_movimiento === 'salida') return `-${movement.cantidad}`;
  return `= ${movement.cantidad}`;
};
const movementClass = (type) => {
  if (type === 'entrada') return 'bg-emerald-400/15 text-emerald-200';
  if (type === 'salida') return 'bg-rose-400/15 text-rose-200';
  return 'bg-cyan-400/15 text-cyan-200';
};
const destinationLabel = (destino) => (destino === 'TIENDA' ? 'Tienda' : destino === 'VENTA' ? 'Venta' : 'Sin destino');
const destinationClass = (destino) => (destino === 'TIENDA'
  ? 'bg-blue-400/15 text-blue-200'
  : 'bg-green-400/15 text-green-200');

const filteredMovements = computed(() => {
  const query = search.value.trim().toLowerCase();
  return movements.value.filter((movement) => {
    const destino = destinationOf(movement);
    const fecha = String(movement.fecha_movimiento || '');
    return (!query || [itemName(movement.id_item), movement.descripcion].join(' ').toLowerCase().includes(query))
      && (typeFilter.value === 'all' || movement.tipo_movimiento === typeFilter.value)
      && (destinationFilter.value === 'all' || (destinationFilter.value === 'none' ? !destino : destino === destinationFilter.value))
      && (!dateFrom.value || fecha >= dateFrom.value)
      && (!dateTo.value || fecha <= dateTo.value);
  });
});

/**
 * Abre el modal para registrar un movimiento nuevo.
 */
const openNew = () => {
  editingMovement.value = null;
  Object.assign(form, emptyForm());
  modalError.value = '';
  isModalOpen.value = true;
};

/**
 * Abre el modal con un movimiento cargado para corregirlo.
 */
const openEdit = (movement) => {
  editingMovement.value = { ...movement };
  Object.assign(form, {
    id_item: Number(movement.id_item),
    tipo_movimiento: movement.tipo_movimiento,
    cantidad: Number(movement.cantidad || 1),
    destino: destinationOf(movement),
    fecha_movimiento: movement.fecha_movimiento || today(),
    descripcion: movement.descripcion || '',
  });
  modalError.value = '';
  isModalOpen.value = true;
};

const closeModal = () => {
  if (isSaving.value) return;
  isModalOpen.value = false;
  editingMovement.value = null;
};

/**
 * Gestiona esta acción de la vista.
 */
const save = async () => {
  modalError.value = '';
  try {
    if (!form.id_item) throw new Error('Selecciona un articulo de inventario.');
    if (!lockedByOrder.value && projectedStock.value < 0) throw new Error('No hay stock suficiente en Inventario para este movimiento.');
    if (!lockedByOrder.value && projectedStoreStock.value < 0) throw new Error('La Tienda ya vendio esas unidades; no puedes reducir la reposicion.');
    const destino = form.tipo_movimiento === 'salida' ? form.destino : '';
    isSaving.value = true;
    if (editingMovement.value) {
      const payload = lockedByOrder.value
        ? { fecha_movimiento: form.fecha_movimiento, descripcion: form.descripcion }
        : { ...form, destino };
      await gymStore.updateInventoryMovement(editingMovement.value.id_mov, payload);
      feedback.value = 'Movimiento actualizado y stock recalculado.';
    } else {
      await gymStore.registrarMovimientoToServer({
        ...form,
        destino: destino || null,
        id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1,
      });
      feedback.value = destino === 'TIENDA' ? 'Reposicion registrada: el stock paso de Inventario a Tienda.' : 'Movimiento registrado y stock actualizado.';
    }
    feedbackTone.value = 'success';
    isSaving.value = false;
    closeModal();
  } catch (error) {
    isSaving.value = false;
    modalError.value = error instanceof Error ? error.message : 'No se pudo guardar el movimiento.';
  }
};
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input:disabled { opacity: .6; cursor: not-allowed; }
.field-input::placeholder { color: #64748b; }
</style>
