<template>
  <div class="workspace-view space-y-6">
    <section class="ws-panel ws-hero">
      <div
        class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div>
          <p class="ws-eyebrow">Inventario</p>
          <h1 class="ws-title">Movimientos de stock</h1>
          <p class="mt-2 ws-soft">
            Controla el stock de tu tienda y consulta cada entrada, salida o
            ajuste.
          </p>
        </div>
        <RouterLink
          :to="{ name: 'Inventory' }"
          class="inline-flex w-fit items-center gap-2 rounded-2xl border ws-border px-4 py-2.5 text-sm font-bold ws-text transition ws-hover"
        >
          <ArrowLeft :size="16" />
          Volver a inventario
        </RouterLink>
      </div>

      <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border ws-border ws-inset p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] ws-muted">
              Movimientos ({{ periodLabel }})
            </p>
            <History :size="16" class="ws-muted" />
          </div>
          <p class="mt-2 text-2xl font-black ws-text">
            {{ periodMovements.length }}
          </p>
        </div>
        <div class="rounded-2xl border ws-border-success ws-tint-success p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] ws-success">
              Entradas
            </p>
            <ArrowDownToLine :size="16" class="ws-success" />
          </div>
          <p class="mt-2 text-2xl font-black ws-success">
            +{{ stats.entradas }}
          </p>
        </div>
        <div class="rounded-2xl border ws-border-danger ws-tint-danger p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] ws-danger">Salidas</p>
            <ArrowUpFromLine :size="16" class="ws-danger" />
          </div>
          <p class="mt-2 text-2xl font-black ws-danger">-{{ stats.salidas }}</p>
        </div>
        <div class="rounded-2xl border ws-border-info ws-tint-info p-4">
          <div class="flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.2em] ws-info">Ajustes</p>
            <SlidersHorizontal :size="16" class="ws-info" />
          </div>
          <p class="mt-2 text-2xl font-black ws-info">{{ stats.ajustes }}</p>
        </div>
      </div>
    </section>

    <transition name="fade">
      <p
        v-if="feedback"
        role="status"
        class="flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm"
        :class="feedbackClass"
      >
        <CircleCheck
          v-if="feedbackTone === 'success'"
          :size="16"
          class="shrink-0"
        />
        <CircleAlert v-else :size="16" class="shrink-0" />
        {{ feedback }}
      </p>
    </transition>

    <section class="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
      <form class="h-fit ws-panel" @submit.prevent="save">
        <p class="ws-eyebrow">Registro</p>
        <h2 class="mt-2 text-2xl font-black ws-text">Nuevo movimiento</h2>

        <p class="ws-muted text-sm mt-2">
          El stock se actualizará al registrar el movimiento.
        </p>
        <fieldset :disabled="isSaving" class="mt-5 space-y-4">
          <label class="block space-y-2">
            <span class="text-sm ws-soft">Artículo</span>
            <select
              v-model.number="form.id_item"
              class="ws-input"
              :class="{ 'ws-input--error': errors.id_item }"
            >
              <option :value="0">Selecciona un artículo...</option>
              <option
                v-for="item in inventory"
                :key="item.id"
                :value="itemId(item)"
              >
                {{ item.inventoryCode }} - {{ item.name }} ({{ item.quantity }}
                {{ item.unidad_venta || 'unidad' }})
              </option>
            </select>
            <p v-if="errors.id_item" class="text-xs font-semibold ws-danger">
              {{ errors.id_item }}
            </p>
          </label>

          <div class="space-y-2">
            <span class="block text-sm ws-soft">Tipo de movimiento</span>
            <div
              class="movement-type-grid"
              role="group"
              aria-label="Tipo de movimiento"
            >
              <button
                v-for="option in movementTypes"
                :key="option.value"
                :aria-pressed="form.tipo_movimiento === option.value"
                type="button"
                class="flex flex-col items-center gap-1.5 rounded-2xl border px-2 py-3 text-xs font-bold transition"
                :class="
                  form.tipo_movimiento === option.value
                    ? option.activeClass
                    : 'ws-border ws-inset ws-muted ws-hover'
                "
                @click="form.tipo_movimiento = option.value"
              >
                <component :is="option.icon" :size="18" />
                {{ option.label }}
              </button>
            </div>
          </div>

          <label class="block space-y-2">
            <span class="text-sm ws-soft">{{
              form.tipo_movimiento === 'ajuste'
                ? 'Cantidad final en stock'
                : 'Cantidad'
            }}</span>
            <div
              class="flex items-stretch overflow-hidden rounded-2xl border ws-border ws-inset"
              :class="{ 'ws-border-danger': errors.cantidad }"
            >
              <button
                type="button"
                class="px-4 text-lg font-black ws-soft transition ws-hover disabled:opacity-30"
                :disabled="form.cantidad <= 1"
                aria-label="Reducir cantidad"
                @click="stepCantidad(-1)"
              >
                -
              </button>
              <input
                v-model.number="form.cantidad"
                aria-label="Cantidad del movimiento"
                type="number"
                min="1"
                class="w-full border-x ws-border bg-transparent px-3 py-3 text-center ws-text outline-none"
              />
              <button
                type="button"
                class="px-4 text-lg font-black ws-soft transition ws-hover"
                aria-label="Aumentar cantidad"
                @click="stepCantidad(1)"
              >
                +
              </button>
            </div>
            <p v-if="errors.cantidad" class="text-xs font-semibold ws-danger">
              {{ errors.cantidad }}
            </p>
            <p v-else-if="resultingStock" class="text-xs ws-muted">
              {{ resultingStock }}
            </p>
          </label>

          <label class="block space-y-2">
            <span class="text-sm ws-soft">Fecha</span>
            <input
              v-model="form.fecha_movimiento"
              type="date"
              class="ws-input"
            />
          </label>

          <label class="block space-y-2">
            <span class="text-sm ws-soft"
              >Observación <span class="ws-muted">(opcional)</span></span
            >
            <textarea
              v-model="form.descripcion"
              rows="3"
              class="ws-input"
              placeholder="Motivo, proveedor, incidencia o venta manual"
            ></textarea>
          </label>
        </fieldset>

        <button
          type="submit"
          class="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl ws-primary px-4 py-3 font-black ws-onaccent transition ws-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isSaving"
        >
          <RefreshCw v-if="isSaving" :size="16" class="animate-spin" />
          {{ isSaving ? 'Registrando...' : 'Registrar movimiento' }}
        </button>
      </form>

      <div class="ws-panel">
        <div
          class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"
        >
          <div>
            <p class="ws-eyebrow">Historial</p>
            <h2 class="mt-2 text-2xl font-black ws-text">
              Historial de movimientos
            </h2>
          </div>
          <button
            type="button"
            class="inline-flex w-fit items-center gap-2 rounded-2xl border ws-border px-4 py-2.5 text-sm font-bold ws-text transition ws-hover disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!filteredMovements.length"
            @click="exportCsv"
          >
            <Download :size="16" />
            Exportar CSV
          </button>
        </div>

        <div class="mt-5 flex flex-col gap-3 lg:flex-row lg:items-end">
          <div class="ws-search">
            <Search
              :size="16"
              class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 ws-muted"
            />
            <input
              v-model="search"
              type="search"
              aria-label="Buscar movimientos"
              class="ws-input"
              placeholder="Artículo, tipo u observación"
            />
          </div>
          <label class="movement-date"
            ><span class="ws-field-label">Desde</span
            ><input
              v-model="dateFrom"
              type="date"
              class="ws-input"
              :max="dateTo || undefined"
          /></label>
          <label class="movement-date"
            ><span class="ws-field-label">Hasta</span
            ><input
              v-model="dateTo"
              type="date"
              class="ws-input"
              :min="dateFrom || undefined"
          /></label>
        </div>

        <div class="mt-3 flex flex-wrap gap-2">
          <button
            v-for="chip in typeChips"
            :key="chip.value"
            :aria-pressed="filterType === chip.value"
            type="button"
            class="rounded-full border px-3.5 py-1.5 text-xs font-bold transition"
            :class="
              filterType === chip.value
                ? chip.activeClass
                : 'ws-border ws-inset ws-muted ws-hover'
            "
            @click="filterType = chip.value"
          >
            {{ chip.label }} <span class="opacity-70">({{ chip.count }})</span>
          </button>
          <button
            v-if="hasActiveFilters"
            type="button"
            class="rounded-full px-3.5 py-1.5 text-xs font-bold ws-muted underline decoration-dotted underline-offset-4 ws-hover-text"
            @click="resetFilters"
          >
            Limpiar filtros
          </button>
        </div>

        <p class="ws-muted text-xs mt-4" role="status">
          {{ filteredMovements.length }} movimientos encontrados · Mostrando
          {{ visibleMovements.length }}
        </p>
        <div v-if="visibleMovements.length" class="mt-5">
          <div
            class="hidden overflow-hidden rounded-2xl border ws-border md:block"
          >
            <div class="overflow-x-auto">
              <table class="ws-table min-w-[700px]">
                <thead
                  class="ws-inset text-xs uppercase tracking-[0.16em] ws-muted"
                >
                  <tr>
                    <th class="px-4 py-3">Fecha</th>
                    <th class="px-4 py-3">Artículo</th>
                    <th class="px-4 py-3">Tipo</th>
                    <th class="px-4 py-3">Cantidad</th>
                    <th class="px-4 py-3">Usuario</th>
                    <th class="px-4 py-3">Observación</th>
                  </tr>
                </thead>
                <tbody class="divide-y ws-divide">
                  <tr
                    v-for="movement in visibleMovements"
                    :key="movement.id_mov"
                    class="transition ws-hover"
                  >
                    <td class="whitespace-nowrap px-4 py-3 ws-soft">
                      {{ formatDate(movement.fecha_movimiento) }}
                    </td>
                    <td class="px-4 py-3 font-bold ws-text">
                      {{ itemName(movement.id_item) }}
                    </td>
                    <td class="px-4 py-3">
                      <span
                        class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black"
                        :class="movementClass(movement.tipo_movimiento)"
                      >
                        <component
                          :is="movementIcon(movement.tipo_movimiento)"
                          :size="12"
                        />
                        {{ movementLabel(movement.tipo_movimiento) }}
                      </span>
                    </td>
                    <td
                      class="px-4 py-3 font-bold"
                      :class="quantityClass(movement.tipo_movimiento)"
                    >
                      {{ signedQuantity(movement) }}
                    </td>
                    <td class="px-4 py-3 ws-soft">
                      {{ userName(movement.id_usuario) }}
                    </td>
                    <td
                      class="max-w-xs break-words px-4 py-3 ws-muted"
                      :title="movement.descripcion"
                    >
                      {{ movement.descripcion || 'Sin observación' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <ul class="space-y-3 md:hidden">
            <li
              v-for="movement in visibleMovements"
              :key="movement.id_mov"
              class="rounded-2xl border ws-border ws-inset p-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-bold ws-text">
                    {{ itemName(movement.id_item) }}
                  </p>
                  <p class="mt-0.5 text-xs ws-muted">
                    {{ formatDate(movement.fecha_movimiento) }} -
                    {{ userName(movement.id_usuario) }}
                  </p>
                </div>
                <span
                  class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-black"
                  :class="movementClass(movement.tipo_movimiento)"
                >
                  <component
                    :is="movementIcon(movement.tipo_movimiento)"
                    :size="12"
                  />
                  {{ movementLabel(movement.tipo_movimiento) }}
                </span>
              </div>
              <p
                class="mt-2 text-lg font-black"
                :class="quantityClass(movement.tipo_movimiento)"
              >
                {{ signedQuantity(movement) }}
              </p>
              <p class="mt-1 text-sm ws-muted">
                {{ movement.descripcion || 'Sin observación' }}
              </p>
            </li>
          </ul>

          <button
            v-if="filteredMovements.length > visibleMovements.length"
            type="button"
            class="mt-4 w-full rounded-2xl border ws-border py-2.5 text-sm font-bold ws-soft transition ws-hover"
            @click="visibleCount += pageSize"
          >
            Ver más movimientos ({{
              filteredMovements.length - visibleMovements.length
            }}
            restantes)
          </button>
        </div>

        <div
          v-else-if="movements.length"
          class="mt-5 rounded-2xl border border-dashed ws-border p-8 text-center"
        >
          <SearchX :size="22" class="mx-auto ws-muted" />
          <p class="mt-3 text-sm font-bold ws-text">
            Sin resultados para estos filtros
          </p>
          <p class="mt-1 text-xs ws-muted">
            Prueba con otra búsqueda o ajusta el rango de fechas.
          </p>
          <button
            type="button"
            class="mt-3 text-xs font-bold ws-warning hover:underline"
            @click="resetFilters"
          >
            Limpiar filtros
          </button>
        </div>

        <div
          v-else
          class="mt-5 rounded-2xl border border-dashed ws-border p-8 text-center"
        >
          <PackageSearch :size="22" class="mx-auto ws-muted" />
          <p class="mt-3 text-sm font-bold ws-text">
            Aún no hay movimientos registrados
          </p>
          <p class="mt-1 text-xs ws-muted">
            Usa el formulario para registrar la primera entrada, salida o
            ajuste.
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  computed,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from 'vue';
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
const movements = computed(() =>
  [...(gymStore.inventoryMovements || [])].sort(
    (a, b) =>
      String(b.fecha_movimiento || '').localeCompare(
        String(a.fecha_movimiento || ''),
      ) || Number(b.id_mov) - Number(a.id_mov),
  ),
);

const form = reactive({
  id_item: 0,
  tipo_movimiento: 'entrada',
  cantidad: 1,
  fecha_movimiento: new Date().toISOString().slice(0, 10),
  descripcion: '',
});

const movementTypes = [
  {
    value: 'entrada',
    label: 'Entrada',
    icon: ArrowDownToLine,
    activeClass: 'ws-border-success ws-tint-success ws-success',
  },
  {
    value: 'salida',
    label: 'Salida',
    icon: ArrowUpFromLine,
    activeClass: 'ws-border-danger ws-tint-danger ws-danger',
  },
  {
    value: 'ajuste',
    label: 'Ajuste',
    icon: SlidersHorizontal,
    activeClass: 'ws-border-info ws-tint-info ws-info',
  },
];

const feedbackClass = computed(() =>
  feedbackTone.value === 'error'
    ? 'ws-border-danger ws-tint-danger ws-danger'
    : 'ws-border-success ws-tint-success ws-success',
);

/**
 * Devuelve el id numerico normalizado de un item de inventario.
 */
const itemId = (item) => Number(String(item.id).replace('item-', ''));

/**
 * Busca el nombre de un item por su id.
 */
const itemName = (idItem) =>
  inventory.value.find((item) => itemId(item) === Number(idItem))?.name ||
  `Item #${idItem}`;

/**
 * Busca el nombre de usuario que registro el movimiento.
 */
const userName = (idUsuario) => {
  if (!idUsuario) return 'Sistema';
  const match = gymStore.users?.find(
    (user) =>
      String(user.id_usuario) === String(idUsuario) ||
      String(user.id) === String(idUsuario),
  );
  return match?.nombre || `Usuario #${idUsuario}`;
};

/**
 * Formatea una fecha ISO a un formato legible corto.
 */
const formatDate = (value) => {
  if (!value) return 'Sin fecha';
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString('es-PE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

const movementLabel = (type) =>
  ({ entrada: 'Entrada', salida: 'Salida', ajuste: 'Ajuste' })[type] || type;
const movementIcon = (type) =>
  ({
    entrada: ArrowDownToLine,
    salida: ArrowUpFromLine,
    ajuste: SlidersHorizontal,
  })[type] || SlidersHorizontal;
const movementClass = (type) =>
  type === 'entrada'
    ? 'ws-tint-success ws-success'
    : type === 'salida'
      ? 'ws-tint-danger ws-danger'
      : 'ws-tint-info ws-info';
const quantityClass = (type) =>
  type === 'entrada'
    ? 'ws-success'
    : type === 'salida'
      ? 'ws-danger'
      : 'ws-info';
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
    if (
      query &&
      ![
        itemName(movement.id_item),
        movement.tipo_movimiento,
        movement.descripcion,
      ]
        .join(' ')
        .toLowerCase()
        .includes(query)
    )
      return false;
    if (dateFrom.value || dateTo.value) {
      if (!dateInRange(movement.fecha_movimiento)) return false;
    }
    return true;
  });
});

const typeChips = computed(() => [
  {
    value: 'todos',
    label: 'Todos',
    count: baseFiltered.value.length,
    activeClass: 'ws-border-warning ws-tint-warning ws-warning',
  },
  {
    value: 'entrada',
    label: 'Entradas',
    count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'entrada')
      .length,
    activeClass: 'ws-border-success ws-tint-success ws-success',
  },
  {
    value: 'salida',
    label: 'Salidas',
    count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'salida')
      .length,
    activeClass: 'ws-border-danger ws-tint-danger ws-danger',
  },
  {
    value: 'ajuste',
    label: 'Ajustes',
    count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'ajuste')
      .length,
    activeClass: 'ws-border-info ws-tint-info ws-info',
  },
]);

const filteredMovements = computed(() => {
  if (filterType.value === 'todos') return baseFiltered.value;
  return baseFiltered.value.filter(
    (movement) => movement.tipo_movimiento === filterType.value,
  );
});

const visibleMovements = computed(() =>
  filteredMovements.value.slice(0, visibleCount.value),
);
const hasActiveFilters = computed(() =>
  Boolean(
    search.value.trim() ||
    dateFrom.value ||
    dateTo.value ||
    filterType.value !== 'todos',
  ),
);

const periodLabel = computed(() =>
  dateFrom.value || dateTo.value ? 'en el rango' : 'totales',
);
const periodMovements = computed(() => baseFiltered.value);
const stats = computed(() => ({
  entradas: periodMovements.value
    .filter((m) => m.tipo_movimiento === 'entrada')
    .reduce((sum, m) => sum + Number(m.cantidad || 0), 0),
  salidas: periodMovements.value
    .filter((m) => m.tipo_movimiento === 'salida')
    .reduce((sum, m) => sum + Number(m.cantidad || 0), 0),
  ajustes: periodMovements.value.filter((m) => m.tipo_movimiento === 'ajuste')
    .length,
}));

const selectedItem = computed(() =>
  inventory.value.find((item) => itemId(item) === Number(form.id_item)),
);
const resultingStock = computed(() => {
  const item = selectedItem.value;
  if (!item || !form.cantidad) return '';
  const current = Number(item.quantity || 0);
  const unit = item.unidad_venta || 'unidad';
  if (form.tipo_movimiento === 'entrada')
    return `El stock quedará en ${current + Number(form.cantidad)} ${unit}.`;
  if (form.tipo_movimiento === 'salida') {
    const next = current - Number(form.cantidad);
    return next < 0
      ? `Atención: el stock actual es ${current} ${unit}.`
      : `El stock quedará en ${next} ${unit}.`;
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
  const header = [
    'Fecha',
    'Artículo',
    'Tipo',
    'Cantidad',
    'Usuario',
    'Observación',
  ];
  const rows = filteredMovements.value.map((movement) => [
    movement.fecha_movimiento || '',
    itemName(movement.id_item),
    movementLabel(movement.tipo_movimiento),
    movement.cantidad,
    userName(movement.id_usuario),
    (movement.descripcion || '').replace(/"/g, "'"),
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${cell}"`).join(','))
    .join('\n');
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
  errors.id_item = form.id_item ? '' : 'Selecciona un artículo de inventario.';
  errors.cantidad = form.cantidad > 0 ? '' : 'La cantidad debe ser mayor a 0.';
  return !errors.id_item && !errors.cantidad;
};

/**
 * Gestiona esta accion de la vista.
 */
const save = async () => {
  if (isSaving.value || !validate()) return;
  isSaving.value = true;
  try {
    await gymStore.registrarMovimientoToServer({
      ...form,
      id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1,
    });
    feedbackTone.value = 'success';
    feedback.value = 'Movimiento registrado y stock actualizado.';
    Object.assign(form, {
      id_item: 0,
      tipo_movimiento: 'entrada',
      cantidad: 1,
      fecha_movimiento: new Date().toISOString().slice(0, 10),
      descripcion: '',
    });
    visibleCount.value = pageSize;
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value =
      error instanceof Error
        ? error.message
        : 'No se pudo registrar el movimiento.';
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
  if (!value || feedbackTone.value === 'error') return;
  feedbackTimeout = setTimeout(() => {
    feedback.value = '';
  }, 5000);
});

onBeforeUnmount(() => clearTimeout(feedbackTimeout));
onMounted(() =>
  gymStore.fetchFromBackend?.({ section: 'inventory' }).catch(() => {
    feedbackTone.value = 'error';
    feedback.value =
      'No se pudo actualizar el inventario. Recarga la página para intentarlo de nuevo.';
  }),
);
</script>

<style scoped>
.movement-type-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
}
.movement-date {
  width: 100%;
}
@media (min-width: 1024px) {
  .movement-date {
    width: 155px;
    flex-shrink: 0;
  }
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
