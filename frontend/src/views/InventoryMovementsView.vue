<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Inventario</p>
          <h1 class="mt-2 text-3xl font-black text-white">Movimientos de stock</h1>
          <p class="mt-2 text-slate-300">Registra entradas, salidas y ajustes con trazabilidad operativa.</p>
        </div>
        <RouterLink
          :to="{ name: 'Inventory' }"
          class="inline-flex w-fit items-center gap-2 rounded-2xl border border-white/10 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-white/5"
        >
          <ArrowLeft :size="16" />
          Volver a inventario
        </RouterLink>
      </div>

      <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Movimientos ({{ periodLabel }})</p>
            <History :size="16" class="text-slate-500" />
          </div>
          <p class="mt-2 text-2xl font-black text-white">{{ periodMovements.length }}</p>
        </div>
        <div class="rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] text-emerald-200/80">Entradas</p>
            <ArrowDownToLine :size="16" class="text-emerald-300" />
          </div>
          <p class="mt-2 text-2xl font-black text-emerald-200">+{{ stats.entradas }}</p>
        </div>
        <div class="rounded-2xl border border-rose-400/20 bg-rose-400/5 p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] text-rose-200/80">Salidas</p>
            <ArrowUpFromLine :size="16" class="text-rose-300" />
          </div>
          <p class="mt-2 text-2xl font-black text-rose-200">-{{ stats.salidas }}</p>
        </div>
        <div class="rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] text-cyan-200/80">Ajustes</p>
            <SlidersHorizontal :size="16" class="text-cyan-300" />
          </div>
          <p class="mt-2 text-2xl font-black text-cyan-200">{{ stats.ajustes }}</p>
        </div>
      </div>
    </section>

    <transition name="fade">
      <p v-if="feedback" class="flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">
        <CircleCheck v-if="feedbackTone === 'success'" :size="16" class="shrink-0" />
        <CircleAlert v-else :size="16" class="shrink-0" />
        {{ feedback }}
      </p>
    </transition>

    <section class="grid gap-5 xl:grid-cols-[400px_1fr]">
      <form class="h-fit rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="save">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Registro</p>
        <h2 class="mt-2 text-2xl font-black text-white">Nuevo movimiento</h2>

        <div class="mt-5 space-y-4">
          <label class="block space-y-2">
            <span class="text-sm text-slate-300">Articulo</span>
            <select v-model.number="form.id_item" class="field-input" :class="{ 'field-input--error': errors.id_item }">
              <option :value="0">Selecciona un item...</option>
              <option v-for="item in inventory" :key="item.id" :value="itemId(item)">
                {{ item.inventoryCode }} - {{ item.name }} ({{ item.quantity }} {{ item.unidad_venta || 'unidad' }})
              </option>
            </select>
            <p v-if="errors.id_item" class="text-xs font-semibold text-rose-300">{{ errors.id_item }}</p>
          </label>

          <div class="space-y-2">
            <span class="block text-sm text-slate-300">Tipo de movimiento</span>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="option in movementTypes"
                :key="option.value"
                type="button"
                class="flex flex-col items-center gap-1.5 rounded-2xl border px-2 py-3 text-xs font-bold transition"
                :class="form.tipo_movimiento === option.value ? option.activeClass : 'border-white/10 bg-slate-900/60 text-slate-400 hover:bg-white/5'"
                @click="form.tipo_movimiento = option.value"
              >
                <component :is="option.icon" :size="18" />
                {{ option.label }}
              </button>
            </div>
          </div>

          <label class="block space-y-2">
            <span class="text-sm text-slate-300">{{ form.tipo_movimiento === 'ajuste' ? 'Cantidad final en stock' : 'Cantidad' }}</span>
            <div class="flex items-stretch overflow-hidden rounded-2xl border border-white/10 bg-slate-950/72" :class="{ 'border-rose-400/60': errors.cantidad }">
              <button type="button" class="px-4 text-lg font-black text-slate-300 transition hover:bg-white/5 disabled:opacity-30" :disabled="form.cantidad <= 1" @click="stepCantidad(-1)">-</button>
              <input v-model.number="form.cantidad" type="number" min="1" class="w-full border-x border-white/10 bg-transparent px-3 py-3 text-center text-white outline-none" />
              <button type="button" class="px-4 text-lg font-black text-slate-300 transition hover:bg-white/5" @click="stepCantidad(1)">+</button>
            </div>
            <p v-if="errors.cantidad" class="text-xs font-semibold text-rose-300">{{ errors.cantidad }}</p>
            <p v-else-if="resultingStock" class="text-xs text-slate-400">{{ resultingStock }}</p>
          </label>

          <label class="block space-y-2">
            <span class="text-sm text-slate-300">Fecha</span>
            <input v-model="form.fecha_movimiento" type="date" class="field-input" />
          </label>

          <label class="block space-y-2">
            <span class="text-sm text-slate-300">Observacion <span class="text-slate-500">(opcional)</span></span>
            <textarea v-model="form.descripcion" rows="3" class="field-input" placeholder="Motivo, proveedor, incidencia o venta manual"></textarea>
          </label>
        </div>

        <button type="submit" class="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60" :disabled="isSaving">
          <RefreshCw v-if="isSaving" :size="16" class="animate-spin" />
          {{ isSaving ? 'Registrando...' : 'Registrar movimiento' }}
        </button>
      </form>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Ultimos movimientos</h2>
          </div>
          <button
            type="button"
            class="inline-flex w-fit items-center gap-2 rounded-2xl border border-white/10 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!filteredMovements.length"
            @click="exportCsv"
          >
            <Download :size="16" />
            Exportar CSV
          </button>
        </div>

        <div class="mt-5 flex flex-col gap-3 lg:flex-row lg:items-center">
          <div class="relative flex-1">
            <Search :size="16" class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input v-model="search" class="field-input pl-11" placeholder="Buscar por item, tipo o descripcion" />
          </div>
          <input v-model="dateFrom" type="date" class="field-input lg:w-44" title="Desde" />
          <input v-model="dateTo" type="date" class="field-input lg:w-44" title="Hasta" />
        </div>

        <div class="mt-3 flex flex-wrap gap-2">
          <button
            v-for="chip in typeChips"
            :key="chip.value"
            type="button"
            class="rounded-full border px-3.5 py-1.5 text-xs font-bold transition"
            :class="filterType === chip.value ? chip.activeClass : 'border-white/10 bg-slate-900/60 text-slate-400 hover:bg-white/5'"
            @click="filterType = chip.value"
          >
            {{ chip.label }} <span class="opacity-70">({{ chip.count }})</span>
          </button>
          <button
            v-if="hasActiveFilters"
            type="button"
            class="rounded-full px-3.5 py-1.5 text-xs font-bold text-slate-400 underline decoration-dotted underline-offset-4 hover:text-white"
            @click="resetFilters"
          >
            Limpiar filtros
          </button>
        </div>

        <div v-if="visibleMovements.length" class="mt-5">
          <div class="hidden overflow-hidden rounded-2xl border border-white/10 md:block">
            <div class="overflow-x-auto">
              <table class="w-full min-w-[820px] text-left text-sm">
                <thead class="bg-slate-950/80 text-xs uppercase tracking-[0.16em] text-slate-400">
                  <tr>
                    <th class="px-4 py-3">Fecha</th>
                    <th class="px-4 py-3">Articulo</th>
                    <th class="px-4 py-3">Tipo</th>
                    <th class="px-4 py-3">Cantidad</th>
                    <th class="px-4 py-3">Usuario</th>
                    <th class="px-4 py-3">Observacion</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-white/10">
                  <tr v-for="movement in visibleMovements" :key="movement.id_mov" class="transition hover:bg-white/[0.03]">
                    <td class="whitespace-nowrap px-4 py-3 text-slate-300">{{ formatDate(movement.fecha_movimiento) }}</td>
                    <td class="px-4 py-3 font-bold text-white">{{ itemName(movement.id_item) }}</td>
                    <td class="px-4 py-3">
                      <span class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black" :class="movementClass(movement.tipo_movimiento)">
                        <component :is="movementIcon(movement.tipo_movimiento)" :size="12" />
                        {{ movementLabel(movement.tipo_movimiento) }}
                      </span>
                    </td>
                    <td class="px-4 py-3 font-bold" :class="quantityClass(movement.tipo_movimiento)">{{ signedQuantity(movement) }}</td>
                    <td class="px-4 py-3 text-slate-300">{{ userName(movement.id_usuario) }}</td>
                    <td class="max-w-xs truncate px-4 py-3 text-slate-400" :title="movement.descripcion">{{ movement.descripcion || 'Sin observacion' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <ul class="space-y-3 md:hidden">
            <li v-for="movement in visibleMovements" :key="movement.id_mov" class="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-bold text-white">{{ itemName(movement.id_item) }}</p>
                  <p class="mt-0.5 text-xs text-slate-400">{{ formatDate(movement.fecha_movimiento) }} - {{ userName(movement.id_usuario) }}</p>
                </div>
                <span class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black" :class="movementClass(movement.tipo_movimiento)">
                  <component :is="movementIcon(movement.tipo_movimiento)" :size="12" />
                  {{ movementLabel(movement.tipo_movimiento) }}
                </span>
              </div>
              <p class="mt-2 text-lg font-black" :class="quantityClass(movement.tipo_movimiento)">{{ signedQuantity(movement) }}</p>
              <p class="mt-1 text-sm text-slate-400">{{ movement.descripcion || 'Sin observacion' }}</p>
            </li>
          </ul>

          <button
            v-if="filteredMovements.length > visibleMovements.length"
            type="button"
            class="mt-4 w-full rounded-2xl border border-white/10 py-2.5 text-sm font-bold text-slate-300 transition hover:bg-white/5"
            @click="visibleCount += pageSize"
          >
            Ver mas movimientos ({{ filteredMovements.length - visibleMovements.length }} restantes)
          </button>
        </div>

        <div v-else-if="movements.length" class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center">
          <SearchX :size="22" class="mx-auto text-slate-500" />
          <p class="mt-3 text-sm font-bold text-white">Sin resultados para estos filtros</p>
          <p class="mt-1 text-xs text-slate-400">Prueba con otra busqueda o ajusta el rango de fechas.</p>
          <button type="button" class="mt-3 text-xs font-bold text-amber-300 hover:underline" @click="resetFilters">Limpiar filtros</button>
        </div>

        <div v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center">
          <PackageSearch :size="22" class="mx-auto text-slate-500" />
          <p class="mt-3 text-sm font-bold text-white">Aun no hay movimientos registrados</p>
          <p class="mt-1 text-xs text-slate-400">Usa el formulario para registrar la primera entrada, salida o ajuste.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';
import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowUpFromLine,
  CircleAlert,
  CircleCheck,
  Download,
  History,
  PackageSearch,
  RefreshCw,
  Search,
  SearchX,
  SlidersHorizontal,
} from 'lucide-vue-next';
import { useAuthStore } from '../stores/authStore';
import { useGymStore } from '../stores/gymStore';

const authStore = useAuthStore();
const gymStore = useGymStore();

const feedback = ref('');
const feedbackTone = ref('success');
const isSaving = ref(false);
const search = ref('');
const dateFrom = ref('');
const dateTo = ref('');
const filterType = ref('todos');
const visibleCount = ref(8);
const pageSize = 8;
const errors = reactive({ id_item: '', cantidad: '' });

const inventory = computed(() => gymStore.inventory);
const movements = computed(() => gymStore.inventoryMovements || []);

const form = reactive({
  id_item: 0,
  tipo_movimiento: 'entrada',
  cantidad: 1,
  fecha_movimiento: new Date().toISOString().slice(0, 10),
  descripcion: '',
});

const movementTypes = [
  { value: 'entrada', label: 'Entrada', icon: ArrowDownToLine, activeClass: 'border-emerald-400/40 bg-emerald-400/10 text-emerald-200' },
  { value: 'salida', label: 'Salida', icon: ArrowUpFromLine, activeClass: 'border-rose-400/40 bg-rose-400/10 text-rose-200' },
  { value: 'ajuste', label: 'Ajuste', icon: SlidersHorizontal, activeClass: 'border-cyan-400/40 bg-cyan-400/10 text-cyan-200' },
];

const feedbackClass = computed(() =>
  feedbackTone.value === 'error'
    ? 'border-rose-400/20 bg-rose-400/10 text-rose-50'
    : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50',
);

/**
 * Devuelve el id numerico normalizado de un item de inventario.
 */
const itemId = (item) => Number(String(item.id).replace('item-', ''));

/**
 * Busca el nombre de un item por su id.
 */
const itemName = (idItem) => inventory.value.find((item) => itemId(item) === Number(idItem))?.name || `Item #${idItem}`;

/**
 * Busca el nombre de usuario que registro el movimiento.
 */
const userName = (idUsuario) => {
  if (!idUsuario) return 'Sistema';
  const match = gymStore.users?.find((user) => String(user.id_usuario) === String(idUsuario) || String(user.id) === String(idUsuario));
  return match?.nombre || `Usuario #${idUsuario}`;
};

/**
 * Formatea una fecha ISO a un formato legible corto.
 */
const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' });
};

const movementLabel = (type) => ({ entrada: 'Entrada', salida: 'Salida', ajuste: 'Ajuste' }[type] || type);
const movementIcon = (type) => ({ entrada: ArrowDownToLine, salida: ArrowUpFromLine, ajuste: SlidersHorizontal }[type] || SlidersHorizontal);
const movementClass = (type) =>
  type === 'entrada'
    ? 'bg-emerald-400/15 text-emerald-200'
    : type === 'salida'
      ? 'bg-rose-400/15 text-rose-200'
      : 'bg-cyan-400/15 text-cyan-200';
const quantityClass = (type) => (type === 'entrada' ? 'text-emerald-300' : type === 'salida' ? 'text-rose-300' : 'text-cyan-300');
const signedQuantity = (movement) => {
  if (movement.tipo_movimiento === 'salida') return `-${movement.cantidad}`;
  if (movement.tipo_movimiento === 'entrada') return `+${movement.cantidad}`;
  return `= ${movement.cantidad}`;
};

const dateInRange = (value) => {
  if (!value) return !dateFrom.value && !dateTo.value ? true : false;
  if (dateFrom.value && value < dateFrom.value) return false;
  if (dateTo.value && value > dateTo.value) return false;
  return true;
};

const baseFiltered = computed(() => {
  const query = search.value.trim().toLowerCase();
  return movements.value.filter((movement) => {
    if (query && ![itemName(movement.id_item), movement.tipo_movimiento, movement.descripcion].join(' ').toLowerCase().includes(query)) return false;
    if (dateFrom.value || dateTo.value) {
      if (!dateInRange(movement.fecha_movimiento)) return false;
    }
    return true;
  });
});

const typeChips = computed(() => [
  { value: 'todos', label: 'Todos', count: baseFiltered.value.length, activeClass: 'border-amber-400/50 bg-amber-400/10 text-amber-200' },
  { value: 'entrada', label: 'Entradas', count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'entrada').length, activeClass: 'border-emerald-400/50 bg-emerald-400/10 text-emerald-200' },
  { value: 'salida', label: 'Salidas', count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'salida').length, activeClass: 'border-rose-400/50 bg-rose-400/10 text-rose-200' },
  { value: 'ajuste', label: 'Ajustes', count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'ajuste').length, activeClass: 'border-cyan-400/50 bg-cyan-400/10 text-cyan-200' },
]);

const filteredMovements = computed(() => {
  if (filterType.value === 'todos') return baseFiltered.value;
  return baseFiltered.value.filter((movement) => movement.tipo_movimiento === filterType.value);
});

const visibleMovements = computed(() => filteredMovements.value.slice(0, visibleCount.value));
const hasActiveFilters = computed(() => Boolean(search.value.trim() || dateFrom.value || dateTo.value || filterType.value !== 'todos'));

const periodLabel = computed(() => (dateFrom.value || dateTo.value ? 'en el rango' : 'totales'));
const periodMovements = computed(() => baseFiltered.value);
const stats = computed(() => ({
  entradas: periodMovements.value.filter((m) => m.tipo_movimiento === 'entrada').reduce((sum, m) => sum + Number(m.cantidad || 0), 0),
  salidas: periodMovements.value.filter((m) => m.tipo_movimiento === 'salida').reduce((sum, m) => sum + Number(m.cantidad || 0), 0),
  ajustes: periodMovements.value.filter((m) => m.tipo_movimiento === 'ajuste').length,
}));

const selectedItem = computed(() => inventory.value.find((item) => itemId(item) === Number(form.id_item)));
const resultingStock = computed(() => {
  const item = selectedItem.value;
  if (!item || !form.cantidad) return '';
  const current = Number(item.quantity || 0);
  const unit = item.unidad_venta || 'unidad';
  if (form.tipo_movimiento === 'entrada') return `Stock quedara en ${current + Number(form.cantidad)} ${unit}.`;
  if (form.tipo_movimiento === 'salida') {
    const next = current - Number(form.cantidad);
    return next < 0 ? `Atencion: el stock actual es ${current} ${unit}.` : `Stock quedara en ${next} ${unit}.`;
  }
  return `Stock actual: ${current} ${unit}.`;
});

/**
 * Incrementa o decrementa la cantidad del formulario.
 */
const stepCantidad = (delta) => {
  form.cantidad = Math.max(1, Number(form.cantidad || 0) + delta);
};

/**
 * Limpia los filtros de busqueda, fecha y tipo.
 */
const resetFilters = () => {
  search.value = '';
  dateFrom.value = '';
  dateTo.value = '';
  filterType.value = 'todos';
};

/**
 * Descarga los movimientos filtrados como archivo CSV.
 */
const exportCsv = () => {
  const header = ['Fecha', 'Articulo', 'Tipo', 'Cantidad', 'Usuario', 'Observacion'];
  const rows = filteredMovements.value.map((movement) => [
    movement.fecha_movimiento || '',
    itemName(movement.id_item),
    movementLabel(movement.tipo_movimiento),
    movement.cantidad,
    userName(movement.id_usuario),
    (movement.descripcion || '').replace(/"/g, "'"),
  ]);
  const csv = [header, ...rows].map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `movimientos-inventario-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
};

/**
 * Valida el formulario antes de enviarlo.
 */
const validate = () => {
  errors.id_item = form.id_item ? '' : 'Selecciona un item de inventario.';
  errors.cantidad = form.cantidad > 0 ? '' : 'La cantidad debe ser mayor a 0.';
  return !errors.id_item && !errors.cantidad;
};

/**
 * Gestiona esta accion de la vista.
 */
const save = async () => {
  if (!validate()) return;
  isSaving.value = true;
  try {
    await gymStore.registrarMovimientoToServer({ ...form, id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1 });
    feedbackTone.value = 'success';
    feedback.value = 'Movimiento registrado y stock actualizado.';
    Object.assign(form, { id_item: 0, tipo_movimiento: 'entrada', cantidad: 1, fecha_movimiento: new Date().toISOString().slice(0, 10), descripcion: '' });
    visibleCount.value = pageSize;
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo registrar el movimiento.';
  } finally {
    isSaving.value = false;
  }
};

watch([search, dateFrom, dateTo, filterType], () => {
  visibleCount.value = pageSize;
});

let feedbackTimeout = null;
watch(feedback, (value) => {
  if (feedbackTimeout) clearTimeout(feedbackTimeout);
  if (!value) return;
  feedbackTimeout = setTimeout(() => {
    feedback.value = '';
  }, 5000);
});

onMounted(() => gymStore.fetchFromBackend?.().catch(() => {}));
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
.field-input--error {
  border-color: rgba(251, 113, 133, 0.6);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
