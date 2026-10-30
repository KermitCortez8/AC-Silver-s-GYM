<template>
  <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
        <h2 class="mt-2 text-2xl font-black text-white">Movimientos de inventario</h2>
        <p class="mt-1 text-sm text-slate-400">Entradas, salidas y ajustes del stock de cada artículo.</p>
      </div>
      <button type="button" class="rounded-2xl bg-orange-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-orange-500/20 transition hover:scale-[1.02] hover:bg-orange-300" @click="openNew">
        + Registrar movimiento
      </button>
    </div>

    <div class="mt-4 grid gap-3 sm:grid-cols-3">
      <button
        v-for="card in typeCards"
        :key="card.value"
        type="button"
        class="flex items-center gap-3 rounded-2xl border-l-4 bg-slate-900/80 px-4 py-3 text-left transition hover:bg-slate-800/80"
        :class="[card.border, typeFilter === card.value ? 'ring-2 ring-blue-400/60' : '']"
        :aria-pressed="typeFilter === card.value"
        :title="typeFilter === card.value ? 'Quitar filtro' : `Ver solo ${card.label.toLowerCase()}`"
        @click="typeFilter = typeFilter === card.value ? 'all' : card.value; page = 1"
      >
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="card.iconClass">
          <component :is="card.icon" :size="20" stroke-width="2.5" />
        </span>
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-slate-400">{{ card.label }}</p>
          <p class="text-2xl font-black text-white">{{ countByType[card.value] }}</p>
        </div>
      </button>
    </div>

    <div class="inv-info mt-4">
      <Info :size="16" aria-hidden="true" />
      <p>Una <span class="font-bold">salida con destino Tienda</span> repone el stock del producto en la Tienda. Los movimientos de pedidos de Tienda se generan solos.</p>
    </div>

    <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-[1.6fr_1fr_1fr_1fr_1fr]">
      <TableSearch
        v-model="search"
        label="Buscar movimientos por artículo o descripción"
        placeholder="Buscar por artículo o descripción"
        @update:model-value="page = 1"
      />
      <select v-model="typeFilter" class="field-input" aria-label="Filtrar por tipo" @change="page = 1">
        <option value="all">Todos los tipos</option>
        <option value="entrada">Entradas</option>
        <option value="salida">Salidas</option>
        <option value="ajuste">Ajustes</option>
      </select>
      <select v-model="destinationFilter" class="field-input" aria-label="Filtrar por destino" @change="page = 1">
        <option value="all">Todos los destinos</option>
        <option value="TIENDA">Tienda</option>
        <option value="VENTA">Venta</option>
        <option value="none">Sin destino</option>
      </select>
      <input v-model="dateFrom" type="date" class="field-input" title="Desde" aria-label="Desde" @change="page = 1" />
      <input v-model="dateTo" type="date" class="field-input" title="Hasta" aria-label="Hasta" @change="page = 1" />
    </div>

    <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <div v-if="filteredMovements.length" class="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <SortableTh class="px-4 py-3" label="Fecha" column="fecha" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              <SortableTh class="px-4 py-3" label="Artículo" column="articulo" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              <th class="px-4 py-3">Tipo</th>
              <SortableTh class="px-4 py-3" label="Cantidad" column="cantidad" numeric :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
              <th class="px-4 py-3">Destino</th>
              <th class="px-4 py-3">Descripción</th>
              <th class="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="movement in pagedMovements" :key="movement.id_mov" class="transition hover:bg-white/[0.04]">
              <td class="whitespace-nowrap px-4 py-3 text-slate-300">{{ movement.fecha_movimiento || 'Sin fecha' }}</td>
              <td class="px-4 py-3 font-bold text-white">
                {{ itemName(movement.id_item) }}
                <span v-if="orderNumber(movement)" class="ml-2 rounded-full bg-sky-400/15 px-2 py-0.5 text-[11px] font-black text-sky-200">Pedido #{{ orderNumber(movement) }}</span>
                <span v-else-if="!movement.id_usuario" class="ml-2 rounded-full bg-slate-400/15 px-2 py-0.5 text-[11px] font-black text-slate-300">Automático</span>
              </td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black capitalize" :class="movementClass(movement.tipo_movimiento)">
                  <component :is="typeIcon(movement.tipo_movimiento)" :size="13" aria-hidden="true" />
                  {{ movement.tipo_movimiento }}
                </span>
              </td>
              <td class="px-4 py-3 font-black" :class="quantityClass(movement.tipo_movimiento)">{{ signedQuantity(movement) }}</td>
              <td class="px-4 py-3">
                <span v-if="destinationOf(movement)" class="rounded-full px-3 py-1 text-xs font-black" :class="destinationClass(destinationOf(movement))">
                  {{ destinationLabel(destinationOf(movement)) }}
                </span>
                <span v-else class="text-xs text-slate-400">-</span>
              </td>
              <td class="max-w-md px-4 py-3 text-slate-400">{{ movement.descripcion || 'Sin descripción' }}</td>
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
    <TablePager
      v-model:page="page"
      v-model:pageSize="pageSize"
      :total="filteredMovements.length"
      item-label="movimientos"
    />
    <p v-if="!filteredMovements.length" class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
      {{ movements.length ? 'Ningún movimiento coincide con los filtros.' : 'Sin movimientos registrados.' }}
    </p>

    <ResourceModal
      :open="isModalOpen"
      :icon="ArrowLeftRight"
      :eyebrow="editingMovement ? 'Inventario · Edición' : 'Inventario · Registro'"
      :title="editingMovement ? `Editar movimiento #${editingMovement.id_mov}` : 'Nuevo movimiento'"
      subtitle="Entradas, salidas y ajustes recalculan el stock al guardar."
      size="md"
      :busy="isSaving"
      @close="closeModal"
      @submit="save"
    >
      <div v-if="formErrors.length" role="alert" class="inv-error">
        <AlertCircle :size="16" aria-hidden="true" />
        <p>{{ missingFieldsMessage(formErrors) }}</p>
      </div>

      <fieldset class="rm-section">
        <legend class="sr-only">Artículo y tipo</legend>
        <p class="rm-section-title"><Package :size="14" aria-hidden="true" /> Artículo y tipo</p>
        <div class="grid gap-4">
          <label class="space-y-2">
            <span class="inv-label inv-required">Artículo</span>
            <select v-model.number="form.id_item" class="field-input" :class="{ 'is-invalid': formErrors.includes('Artículo') }" :disabled="lockedByOrder" @change="formErrors = formErrors.filter((label) => label !== 'Artículo')">
              <option :value="0">Selecciona un artículo</option>
              <option v-for="item in activeInventory" :key="item.id" :value="itemNumber(item)">
                {{ item.inventoryCode }} - {{ item.name }} ({{ item.quantity }})
              </option>
            </select>
          </label>
          <div role="radiogroup" aria-label="Tipo de movimiento" class="space-y-2">
            <span class="inv-label">Tipo</span>
            <div class="flex gap-2">
              <label
                v-for="option in movementTypes"
                :key="option.value"
                class="rm-choice"
                :class="[`rm-choice--${option.value}`, { 'is-active': form.tipo_movimiento === option.value }]"
              >
                <input v-model="form.tipo_movimiento" type="radio" name="tipo_movimiento" :value="option.value" class="sr-only" :disabled="lockedByOrder" />
                <component :is="option.icon" :size="18" aria-hidden="true" />
                {{ option.label }}
              </label>
            </div>
          </div>
        </div>
      </fieldset>

      <fieldset class="rm-section">
        <legend class="sr-only">Detalle</legend>
        <p class="rm-section-title"><CalendarDays :size="14" aria-hidden="true" /> Detalle</p>
        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="inv-label inv-required">{{ form.tipo_movimiento === 'ajuste' ? 'Stock exacto' : 'Cantidad' }}</span>
            <QuantityInput
              v-model="form.cantidad"
              class="field-input"
              :class="{ 'is-invalid': formErrors.includes('Cantidad') }"
              :disabled="lockedByOrder"
            />
            <p v-if="quantityWarning" class="inv-field-error">{{ quantityWarning }}</p>
          </label>
          <label class="space-y-2">
            <span class="inv-label">Fecha</span>
            <input v-model="form.fecha_movimiento" type="date" class="field-input" />
          </label>
          <label v-if="form.tipo_movimiento === 'salida'" class="space-y-2 sm:col-span-2">
            <span class="inv-label">Destino</span>
            <select v-if="!lockedByOrder" v-model="form.destino" class="field-input">
              <option value="">Sin destino (uso interno, merma, baja...)</option>
              <option value="TIENDA" :disabled="!linkedProduct">Tienda - reponer stock{{ linkedProduct ? '' : ' (sin producto enlazado)' }}</option>
            </select>
            <input v-else :value="destinationLabel(form.destino)" class="field-input" disabled />
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="inv-label">Descripción</span>
            <textarea v-model="form.descripcion" rows="3" class="field-input" placeholder="Motivo, proveedor, incidencia o reposición"></textarea>
          </label>
        </div>
      </fieldset>

      <p v-if="lockedByOrder" class="inv-info">
        <Info :size="16" aria-hidden="true" />
        Movimiento de un pedido de Tienda: solo puedes cambiar la fecha y la descripción. La referencia al pedido se conserva.
      </p>
      <div v-else-if="selectedItem" class="space-y-2 rounded-2xl border border-amber-400/25 bg-amber-400/10 px-4 py-3 text-xs leading-5 text-amber-50">
        <p class="rm-section-title" style="margin-bottom: 0.25rem"><TrendingUp :size="14" aria-hidden="true" /> Vista previa del stock</p>
        <p class="flex flex-wrap items-center gap-2">
          <span class="font-semibold">Inventario</span>
          <span class="rounded-lg bg-white/10 px-2 py-0.5 font-bold">{{ selectedItem.quantity }}</span>
          <ArrowRight :size="14" aria-hidden="true" />
          <span class="rounded-lg px-2 py-0.5 font-black" :class="projectedStock < 0 ? 'bg-rose-400/15 text-rose-200' : 'bg-emerald-400/15 text-emerald-200'">{{ projectedStock }}</span>
        </p>
        <p v-if="linkedProduct && (isRestock || wasRestockOfSelected)" class="flex flex-wrap items-center gap-2">
          <span class="font-semibold">Tienda ({{ linkedProduct.nombre }})</span>
          <span class="rounded-lg bg-white/10 px-2 py-0.5 font-bold">{{ linkedProduct.cantidad }}</span>
          <ArrowRight :size="14" aria-hidden="true" />
          <span class="rounded-lg px-2 py-0.5 font-black" :class="projectedStoreStock < 0 ? 'bg-rose-400/15 text-rose-200' : 'bg-emerald-400/15 text-emerald-200'">{{ projectedStoreStock }}</span>
        </p>
        <p v-if="editingMovement">Al guardar se revierte el efecto anterior del movimiento y se aplica el nuevo.</p>
        <p v-if="projectedStock < 0" class="font-bold text-rose-200">No hay stock suficiente en Inventario.</p>
        <p v-if="projectedStoreStock < 0" class="font-bold text-rose-200">La Tienda ya vendió esas unidades; no puedes reducir la reposición.</p>
      </div>

      <p v-if="modalError" role="alert" class="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">{{ modalError }}</p>

      <template #footer>
        <button type="button" class="rm-btn-secondary" :disabled="isSaving" @click="closeModal">Cancelar</button>
        <button type="submit" class="rounded-2xl bg-amber-400 px-5 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300 disabled:opacity-60" :disabled="isSaving">
          {{ isSaving ? 'Guardando...' : editingMovement ? 'Guardar cambios' : 'Registrar movimiento' }}
        </button>
      </template>
    </ResourceModal>
  </section>
</template>

<script setup>
import QuantityInput from "../QuantityInput.vue";
import { feedbackClass as noticeClassFor } from "../../utils/feedback.js";
import { parseQuantity } from '../../../domain/utils/quantities.js';
import { limaDate } from '../../../domain/utils/dates.js';
import { computed, reactive, ref } from 'vue';
import { AlertCircle, ArrowDownToLine, ArrowLeftRight, ArrowRight, ArrowUpFromLine, CalendarDays, Equal, Info, Package, SlidersHorizontal, TrendingUp } from 'lucide-vue-next';
import ResourceModal from '../ResourceModal.vue';
import SortableTh from '../common/SortableTh.vue';
import TablePager from '../common/TablePager.vue';
import TableSearch from '../common/TableSearch.vue';
import { DEFAULT_PAGE_SIZE, matchesSearch, missingFields, missingFieldsMessage, sortRows } from '../../../domain/utils/inputRules.js';
import { useAuthStore } from '../../../application/stores/authStore';
import { useGymStore } from '../../../application/stores/gymStore';

const movementTypes = [
  { value: 'entrada', label: 'Entrada', icon: ArrowDownToLine },
  { value: 'salida', label: 'Salida', icon: ArrowUpFromLine },
  { value: 'ajuste', label: 'Ajuste exacto', icon: Equal },
];

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
const activeInventory = computed(() => inventory.value.filter((item) => !item.archived));
const products = computed(() => gymStore.productos_tienda || []);
const movements = computed(() => gymStore.inventoryMovements || []);
const feedbackClass = computed(() => noticeClassFor(feedbackTone.value));
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

const typeIcon = (type) => movementTypes.find((option) => option.value === type)?.icon || SlidersHorizontal;
const quantityClass = (type) => {
  if (type === 'entrada') return 'text-emerald-300';
  if (type === 'salida') return 'text-rose-300';
  return 'text-cyan-200';
};
const typeCards = [
  { value: 'entrada', label: 'Entradas', icon: ArrowDownToLine, border: 'border-l-emerald-400', iconClass: 'bg-emerald-100 text-emerald-600' },
  { value: 'salida', label: 'Salidas', icon: ArrowUpFromLine, border: 'border-l-rose-400', iconClass: 'bg-rose-100 text-rose-600' },
  { value: 'ajuste', label: 'Ajustes', icon: Equal, border: 'border-l-cyan-400', iconClass: 'bg-cyan-100 text-cyan-700' },
];
const countByType = computed(() => movements.value.reduce((counts, movement) => {
  counts[movement.tipo_movimiento] = (counts[movement.tipo_movimiento] || 0) + 1;
  return counts;
}, { entrada: 0, salida: 0, ajuste: 0 }));

// El buscador solo mira el nombre del articulo y la descripcion.
const filteredMovements = computed(() => {
  return movements.value.filter((movement) => {
    const destino = destinationOf(movement);
    const fecha = String(movement.fecha_movimiento || '');
    return matchesSearch(search.value, [itemName(movement.id_item), movement.descripcion])
      && (typeFilter.value === 'all' || movement.tipo_movimiento === typeFilter.value)
      && (destinationFilter.value === 'all' || (destinationFilter.value === 'none' ? !destino : destino === destinationFilter.value))
      && (!dateFrom.value || fecha >= dateFrom.value)
      && (!dateTo.value || fecha <= dateTo.value);
  });
});

// Orden por columna y paginacion con filas por pagina.
const sortKey = ref('');
const sortDir = ref('asc');
const SORT_COLUMNS = {
  fecha: { accessor: (movement) => movement.fecha_movimiento, type: 'text' },
  articulo: { accessor: (movement) => itemName(movement.id_item), type: 'text' },
  cantidad: { accessor: (movement) => movement.cantidad, type: 'number' },
};
const toggleSort = (column) => {
  sortDir.value = sortKey.value === column && sortDir.value === 'asc' ? 'desc' : 'asc';
  sortKey.value = column;
  page.value = 1;
};
const page = ref(1);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const pagedMovements = computed(() => {
  const column = SORT_COLUMNS[sortKey.value];
  const rows = column ? sortRows(filteredMovements.value, column.accessor, sortDir.value, column.type) : filteredMovements.value;
  return rows.slice((page.value - 1) * pageSize.value, page.value * pageSize.value);
});

// Validacion del formulario: campos obligatorios y cantidad entera.
const formErrors = ref([]);
const quantityWarning = ref('');

/**
 * Abre el modal para registrar un movimiento nuevo.
 */
const openNew = () => {
  editingMovement.value = null;
  Object.assign(form, emptyForm());
  modalError.value = '';
  formErrors.value = [];
  quantityWarning.value = '';
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
  formErrors.value = [];
  quantityWarning.value = '';
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
  if (isSaving.value) return;
  modalError.value = '';
  formErrors.value = missingFields(form, [
    { key: 'id_item', label: 'Artículo', isEmpty: (value) => !Number(value) },
    { key: 'cantidad', label: 'Cantidad', isEmpty: (value) => !(Number(value) >= 1) },
  ]);
  if (formErrors.value.length) {
    modalError.value = missingFieldsMessage(formErrors.value);
    return;
  }
  try {
    const cantidad = lockedByOrder.value ? undefined : parseQuantity(form.cantidad, { min: 1 });
    if (!form.id_item) throw new Error('Selecciona un artículo de inventario.');
    if (!lockedByOrder.value && projectedStock.value < 0) throw new Error('No hay stock suficiente en Inventario para este movimiento.');
    if (!lockedByOrder.value && projectedStoreStock.value < 0) throw new Error('La Tienda ya vendió esas unidades; no puedes reducir la reposición.');
    const destino = form.tipo_movimiento === 'salida' ? form.destino : '';
    isSaving.value = true;
    if (editingMovement.value) {
      const payload = lockedByOrder.value
        ? { fecha_movimiento: form.fecha_movimiento, descripcion: form.descripcion }
        : { ...form, cantidad, destino };
      await gymStore.updateInventoryMovement(editingMovement.value.id_mov, payload);
      feedback.value = 'Movimiento actualizado y stock recalculado.';
    } else {
      await gymStore.registrarMovimientoToServer({
        ...form,
        cantidad,
        destino: destino || null,
        id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1,
      });
      feedback.value = destino === 'TIENDA' ? 'Reposición registrada: el stock pasó de Inventario a Tienda.' : 'Movimiento registrado y stock actualizado.';
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
