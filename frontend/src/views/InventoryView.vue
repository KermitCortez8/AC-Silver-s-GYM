<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.3em] text-amber-300">Recursos &middot; Gestion de inventario</p>
          <h1 class="mt-2 text-3xl font-black text-white">Inventario</h1>
          <p class="mt-2 text-slate-300">Controla stock, ubicacion, estado operativo y observaciones de cada recurso del gimnasio.</p>
        </div>

        <button v-if="activeTab === 'articulos'" class="rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:scale-[1.02] hover:bg-amber-300" @click="openNewItem">
          + Ingresar Nuevo Articulo
        </button>
      </div>

      <nav class="mt-5 flex gap-2 border-t border-white/10 pt-5" aria-label="Secciones de inventario">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="rounded-xl px-4 py-2 text-sm font-bold transition"
          :class="activeTab === tab.value ? 'bg-amber-400 text-slate-950' : 'border border-white/10 text-slate-300 hover:bg-white/5'"
          :aria-current="activeTab === tab.value ? 'page' : undefined"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </nav>
    </section>

    <InventoryMovementsPanel v-if="activeTab === 'movimientos'" />

    <section v-else class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
          <h2 class="mt-2 text-2xl font-black text-white">Listado de inventario</h2>
        </div>
      </div>

      <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-blue-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <Package :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Total registrados</p>
            <p class="text-2xl font-black text-white">{{ inventory.length }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-green-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-600">
            <CheckCircle2 :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Disponibilidad operativa</p>
            <p class="text-2xl font-black text-white">{{ operationalPercent }}%</p>
          </div>
        </div>
        <button
          type="button"
          class="flex items-center gap-3 rounded-2xl border-l-4 border-l-yellow-400 bg-slate-900/80 px-4 py-3 text-left transition hover:bg-slate-800/80"
          :class="isLowStockFilter ? 'ring-2 ring-yellow-400/70' : ''"
          :aria-pressed="isLowStockFilter"
          :title="isLowStockFilter ? 'Quitar filtro de stock bajo' : 'Ver solo articulos en stock bajo'"
          @click="toggleLowStockFilter"
        >
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-yellow-100 text-yellow-700">
            <TrendingDown :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Stock bajo (Tienda)</p>
            <p class="text-2xl font-black text-white">{{ lowStock.length }}</p>
          </div>
        </button>
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-violet-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
            <Wrench :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">En mantenimiento</p>
            <p class="text-2xl font-black text-white">{{ maintenanceItems }}</p>
          </div>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap gap-2.5">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
          :class="selectedCategory === 'all' ? 'border-amber-400 bg-amber-400 text-slate-950' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
          @click="selectedCategory = 'all'; paginaActual = 1"
        >
          Todas las categorias <span :class="selectedCategory === 'all' ? 'text-slate-900/70' : 'text-slate-500'">{{ inventory.length }}</span>
        </button>
        <button
          v-for="entry in categorySummary"
          :key="entry.name"
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
          :class="selectedCategory === entry.name ? 'border-amber-400 bg-amber-400 text-slate-950' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
          @click="selectedCategory = entry.name; paginaActual = 1"
        >
          <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: categoryDotColor(entry.name) }"></span>
          {{ entry.name }} <span :class="selectedCategory === entry.name ? 'text-slate-900/70' : 'text-slate-500'">{{ entry.count }}</span>
        </button>
      </div>

      <p class="mt-3 text-xs text-slate-500">Mostrando {{ filteredInventory.length }} de {{ inventory.length }} articulos</p>

      <div class="mt-3 grid gap-3 sm:grid-cols-[1.5fr_1fr_1fr]">
        <div class="flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3">
          <Search :size="16" class="shrink-0 text-slate-500" />
          <input v-model="searchQuery" class="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500" placeholder="Buscar por codigo, nombre o marca..." @input="paginaActual = 1" />
        </div>
        <select v-model="selectedLocation" class="field-input" @change="paginaActual = 1">
          <option value="all">Todas las ubicaciones</option>
          <option v-for="loc in locationOptions" :key="loc" :value="loc">{{ loc }}</option>
        </select>
        <select v-model="selectedStatus" class="field-input" @change="paginaActual = 1">
          <option value="all">Todos los estados</option>
          <option>Operativo</option>
          <option>Disponible</option>
          <option>En mantenimiento</option>
          <option>Fuera de servicio</option>
          <option>Dado de baja</option>
          <option>Stock bajo</option>
          <option>Agotado</option>
          <option>Descontinuado</option>
        </select>
      </div>

      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <div v-if="filteredInventory.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[1120px] text-left text-sm">
            <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-5 py-4 font-bold">Articulo</th>
                <th class="px-4 py-4 font-bold">Categoria</th>
                <th class="px-4 py-4 font-bold">Ubicacion</th>
                <th class="px-4 py-4 font-bold">Stock</th>
                <th class="px-4 py-4 font-bold">Estado</th>
                <th class="px-5 py-4 text-right font-bold">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="item in inventoryPaginado" :key="item.id" class="transition hover:bg-white/[0.04]">
                <td class="max-w-sm px-5 py-4 align-top">
                  <div class="flex items-start gap-3">
                    <span class="mt-0.5 rounded-lg bg-amber-400/10 px-2.5 py-1 text-xs font-bold text-amber-200">
                      {{ item.inventoryCode }}
                    </span>
                    <div class="min-w-0">
                      <p class="font-bold text-white">{{ item.name }}</p>
                      <p class="mt-1 text-xs text-amber-100/80">N. Activo: {{ item.n_activo || 'Auto' }}</p>
                      <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{{ item.observations || 'Sin observaciones' }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-200">
                    <span class="h-1.5 w-1.5 shrink-0 rounded-full" :style="{ background: categoryDotColor(item.category) }"></span>
                    {{ item.category || 'General' }}
                  </span>
                </td>
                <td class="px-4 py-4 align-top text-slate-300">{{ item.location || 'Sin ubicacion' }}</td>
                <td class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isLowStock(item) ? 'text-rose-300' : 'text-white'">
                    {{ item.quantity }} {{ item.unidad_venta || 'unidad' }}
                  </p>
                  <div class="mt-1.5 h-1.5 w-24 overflow-hidden rounded-full bg-white/10">
                    <div class="h-full rounded-full transition-all" :class="isLowStock(item) ? 'bg-rose-500' : 'bg-green-500'" :style="{ width: stockBarPercent(item) + '%' }"></div>
                  </div>
                  <p class="mt-1 text-xs text-slate-400">Minimo: {{ item.minQuantity || 0 }}</p>
                </td>
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold" :class="inventoryStatusClass(item.status)">
                    {{ item.status }}
                  </span>
                </td>
                <td class="px-5 py-4 align-top">
                  <div class="flex justify-end gap-2">
                    <button class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5" @click="editItem(item)">
                      Editar
                    </button>
                    <button class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 transition hover:bg-rose-400/10" @click="deleteItem(item.id)">
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Paginacion -->
      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-between text-sm text-slate-400">
        <p>Mostrando {{ paginaInicio + 1 }} a {{ paginaFin }} de <span class="font-bold text-white">{{ filteredInventory.length }}</span> articulos</p>
        <div class="flex items-center gap-2">
          <button
            class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="paginaActual === 1"
            @click="paginaActual--"
          >Anterior</button>
          <button
            v-for="p in totalPages"
            :key="p"
            class="h-9 w-9 rounded-xl border text-sm font-bold transition"
            :class="p === paginaActual
              ? 'border-amber-400/40 bg-amber-400/20 text-amber-300'
              : 'border-white/10 text-white hover:bg-white/5'"
            @click="paginaActual = p"
          >{{ p }}</button>
          <button
            class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="paginaActual === totalPages"
            @click="paginaActual++"
          >Siguiente</button>
        </div>
      </div>

      <p v-if="!filteredInventory.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
        {{ inventory.length ? 'Ningun articulo coincide con los filtros aplicados.' : 'No hay articulos en inventario. Usa "Ingresar Nuevo Articulo" para registrar el primero.' }}
      </p>
    </section>

    <Teleport to="body">
      <div v-if="isEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <form class="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl" @submit.prevent="handleSubmit">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Articulo</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar articulo' : 'Nuevo articulo' }}</h2>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeEditor">
              Cerrar
            </button>
          </div>

          <div class="mt-4 flex items-center gap-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-50">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-400 text-slate-950">
              <Tag :size="20" stroke-width="2.5" />
            </span>
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.35em] text-amber-200">Identificador unico</p>
              <p class="mt-1 font-semibold text-white">{{ currentInventoryCode }}</p>
            </div>
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Nombre</span>
              <input v-model="form.name" class="field-input" placeholder="Nombre del articulo" />
            </label>
            <label class="space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Categoria (Tipo)</span>
              <input v-model="form.category" class="field-input" list="inventory-types" placeholder="Tienda, Equipo de fuerza..." />
              <datalist id="inventory-types">
                <option value="Tienda" />
                <option v-for="entry in categorySummary" :key="entry.name" :value="entry.name" />
              </datalist>
            </label>
            <label class="space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">{{ editingId ? 'Stock actual' : 'Stock inicial' }}</span>
              <div v-if="!editingId" class="flex items-center gap-2">
                <button type="button" class="field-input flex shrink-0 items-center justify-center text-lg font-bold" style="width: 2.75rem; padding: 0" @click="form.quantity = Math.max(0, form.quantity - 1)">−</button>
                <input v-model.number="form.quantity" type="number" min="0" class="field-input flex-1 text-center" />
                <button type="button" class="field-input flex shrink-0 items-center justify-center text-lg font-bold" style="width: 2.75rem; padding: 0" @click="form.quantity = form.quantity + 1">+</button>
              </div>
              <input v-else :value="form.quantity" type="number" class="field-input cursor-not-allowed text-center opacity-70" readonly />
            </label>
            <div class="rounded-2xl border border-amber-400/25 bg-amber-400/10 px-4 py-3 text-xs leading-5 text-amber-50 sm:col-span-2">
              <template v-if="editingId">
                El stock no se edita aqui. Para cambiarlo registra una entrada, salida o ajuste en la pestaña Movimientos.
                <span v-if="isTiendaForm" class="font-bold">Este articulo se vende en Tienda: el cambio afectara el stock de Inventario y de Tienda.</span>
              </template>
              <template v-else>
                El stock inicial se registra como una entrada en Movimientos.
                <span v-if="isTiendaForm" class="font-bold">Al ser Tipo "Tienda" se creara su producto en la tienda, oculto hasta que le asignes precio.</span>
              </template>
            </div>
            <label class="space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Unidad de venta</span>
              <input v-model="form.unidad_venta" class="field-input" placeholder="unidad, botella, paquete..." />
            </label>
            <label class="space-y-2">
              <span class="flex items-center justify-between text-xs font-bold uppercase tracking-wide text-slate-400">
                Stock minimo
                <span v-if="form.quantity <= form.minQuantity" class="rounded-full border border-yellow-400/40 bg-yellow-100 px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-yellow-800">Alerta activa</span>
              </span>
              <input v-model.number="form.minQuantity" type="number" min="0" class="field-input" />
              <span class="block text-[11px] text-slate-500">
                {{ isTiendaForm ? 'Se guarda en el producto de Tienda y se usa en ambas vistas.' : 'Solo se guarda para articulos Tipo Tienda.' }}
              </span>
            </label>
            <label class="space-y-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Ubicacion</span>
              <input v-model="form.location" class="field-input" placeholder="Sala 1" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Estado</span>
              <template v-if="isTiendaForm">
                <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-200">
                  <input v-model="isDiscontinuedForm" type="checkbox" class="h-4 w-4 accent-amber-400" />
                  Marcar como Descontinuado
                </label>
                <span class="block text-[11px] text-slate-500">
                  Los articulos de Tienda cambian solos a Disponible, Stock bajo o Agotado segun su stock y el minimo de su producto.
                </span>
              </template>
              <select v-else v-model="form.status" class="field-input">
                <option>Operativo</option>
                <option>En mantenimiento</option>
                <option>Fuera de servicio</option>
                <option>Dado de baja</option>
                <option>Disponible</option>
                <option>Stock bajo</option>
                <option>Agotado</option>
                <option>Descontinuado</option>
              </select>
              <span class="mt-1 inline-flex w-fit rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wide" :class="inventoryStatusClass(statusPreview)">
                {{ statusPreview }}
              </span>
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-xs font-bold uppercase tracking-wide text-slate-400">Observaciones</span>
              <textarea v-model="form.observations" rows="3" class="field-input" placeholder="Estado del equipo, mantenimiento pendiente, incidencias..."></textarea>
            </label>
          </div>

          <button type="submit" class="mt-6 w-full rounded-2xl bg-amber-400 px-4 py-3 text-base font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:scale-[1.01] hover:bg-amber-300">
            {{ editingId ? 'Guardar cambios' : 'Agregar articulo' }}
          </button>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { CheckCircle2, Package, Search, Tag, TrendingDown, Wrench } from 'lucide-vue-next';
import InventoryMovementsPanel from '../components/inventory/InventoryMovementsPanel.vue';
import { useGymStore } from '../stores/gymStore';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();
const tabs = [
  { value: 'articulos', label: 'Articulos' },
  { value: 'movimientos', label: 'Movimientos' },
];
const activeTab = computed({
  get: () => (route.query.tab === 'movimientos' ? 'movimientos' : 'articulos'),
  set: (tab) => router.replace({ query: { ...route.query, tab } }),
});
const inventory = computed(() => gymStore.inventory);
// Productos de Tienda cuya cantidad llego o bajo su stock minimo (TIENDA_PRODUCTOS.stock_minimo), mismo criterio que la vista Tienda.
// Articulos de Tienda con estado automatico "Stock bajo" (sin contar los agotados).
const lowStock = computed(() => inventory.value.filter((item) => item.status === 'Stock bajo'));
const maintenanceItems = computed(() => inventory.value.filter((item) => item.status === 'En mantenimiento').length);

// Filtros de la tabla (solo lectura, no afectan el store).
const searchQuery = ref('');
const selectedCategory = ref('all');
const selectedLocation = ref('all');
const selectedStatus = ref('all');
const isLowStockFilter = computed(() => selectedStatus.value === 'Stock bajo');

/**
 * Activa o quita el filtro de articulos en stock bajo desde la tarjeta.
 */
const toggleLowStockFilter = () => {
  if (isLowStockFilter.value) {
    selectedStatus.value = 'all';
    return;
  }
  selectedStatus.value = 'Stock bajo';
  selectedCategory.value = 'all';
};

const locationOptions = computed(() => {
  const set = new Set(inventory.value.map((item) => item.location).filter(Boolean));
  return Array.from(set);
});

const filteredInventory = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  return inventory.value.filter((item) => {
    const matchesQuery =
      !query ||
      item.name?.toLowerCase().includes(query) ||
      item.inventoryCode?.toLowerCase().includes(query) ||
      item.category?.toLowerCase().includes(query);
    const matchesCategory = selectedCategory.value === 'all' || (item.category || 'General') === selectedCategory.value;
    const matchesLocation = selectedLocation.value === 'all' || item.location === selectedLocation.value;
    const matchesStatus = selectedStatus.value === 'all' || item.status === selectedStatus.value;
    return matchesQuery && matchesCategory && matchesLocation && matchesStatus;
  });
});

// Paginacion (sobre la lista filtrada).
const paginaActual = ref(1);
const porPagina = 10;
const totalPages = computed(() => Math.ceil(filteredInventory.value.length / porPagina));
const paginaInicio = computed(() => (paginaActual.value - 1) * porPagina);
const paginaFin = computed(() => Math.min(paginaInicio.value + porPagina, filteredInventory.value.length));
const inventoryPaginado = computed(() => filteredInventory.value.slice(paginaInicio.value, paginaFin.value));

// Derivados de inventory, solo lectura.
const operationalPercent = computed(() => {
  if (!inventory.value.length) return 0;
  const operational = inventory.value.filter((item) => item.status === 'Operativo' || item.status === 'Disponible').length;
  return Math.round((operational / inventory.value.length) * 100);
});
const categorySummary = computed(() => {
  const counts = new Map();
  inventory.value.forEach((item) => {
    const key = item.category || 'General';
    counts.set(key, (counts.get(key) || 0) + 1);
  });
  return Array.from(counts.entries()).map(([name, count]) => ({ name, count }));
});
const editingId = ref('');
const isEditorOpen = ref(false);
const feedbackMessage = ref('');
const feedbackTone = ref('info');

const form = reactive({
  name: '',
  category: 'General',
  quantity: 0,
  minQuantity: 1,
  unidad_venta: 'unidad',
  precio_venta: 0,
  location: 'Recepcion',
  status: 'Operativo',
  observations: '',
});

const isTiendaForm = computed(() => String(form.category || '').trim().toLowerCase() === 'tienda');
// En articulos de Tienda el estado lo calcula el backend; solo se marca o desmarca Descontinuado.
const isDiscontinuedForm = computed({
  get: () => form.status === 'Descontinuado',
  set: (value) => { form.status = value ? 'Descontinuado' : 'Disponible'; },
});
const statusPreview = computed(() => {
  if (!isTiendaForm.value || form.status === 'Descontinuado') return form.status;
  const current = inventory.value.find((item) => item.id === editingId.value)?.status;
  return editingId.value && current && current !== 'Descontinuado' ? current : 'Automatico';
});

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

/**
 * Valida los datos recibidos.
 */
const isLowStock = (item) => Number(item.quantity || 0) <= Number(item.minQuantity || 0);

/**
 * Ancho de la barra de stock respecto al minimo (3x el minimo = 100%).
 */
const stockBarPercent = (item) => {
  const min = Number(item.minQuantity || 1);
  const qty = Number(item.quantity || 0);
  const reference = Math.max(min * 3, 1);
  return Math.min(100, Math.round((qty / reference) * 100));
};

// Color del punto por categoria (categoria es texto libre, color estable segun el nombre).
const categoryDotPalette = ['#0d9488', '#7c3aed', '#2563eb', '#db2777', '#4f46e5'];
const categoryDotColor = (category) => {
  const key = category || 'General';
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) hash = (hash + key.charCodeAt(i)) % categoryDotPalette.length;
  return categoryDotPalette[hash];
};

/**
 * Gestiona esta acción de la vista.
 */
const inventoryStatusClass = (status) => {
  if (status === 'Operativo') return 'bg-green-100 text-green-700 border-green-300';
  if (status === 'Disponible') return 'bg-blue-100 text-blue-700 border-blue-300';
  if (status === 'En mantenimiento') return 'bg-violet-100 text-violet-700 border-violet-300';
  if (status === 'Stock bajo') return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  if (status === 'Agotado') return 'bg-rose-100 text-rose-700 border-rose-300';
  if (status === 'Descontinuado') return 'bg-slate-300 text-slate-600 border-slate-400 line-through';
  return 'bg-slate-200 text-slate-700 border-slate-300';
};

const currentInventoryCode = computed(() => {
  if (editingId.value) {
    return inventory.value.find((item) => item.id === editingId.value)?.inventoryCode || 'Se generara automaticamente';
  }

  return 'Se generara automaticamente';
});

/**
 * Gestiona esta acción de la vista.
 */
const resetForm = () => {
  editingId.value = '';
  form.name = '';
  form.category = 'General';
  form.quantity = 0;
  form.minQuantity = 1;
  form.unidad_venta = 'unidad';
  form.precio_venta = 0;
  form.location = 'Recepcion';
  form.status = 'Operativo';
  form.observations = '';
};

/**
 * Gestiona esta acción de la vista.
 */
const openNewItem = () => {
  resetForm();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

/**
 * Gestiona esta acción de la vista.
 */
const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

/**
 * Gestiona esta acción de la vista.
 */
const editItem = (item) => {
  editingId.value = item.id;
  form.name = item.name;
  form.category = item.category || 'General';
  form.quantity = Number(item.quantity || 0);
  form.minQuantity = Number(item.minQuantity || 1);
  form.unidad_venta = item.unidad_venta || 'unidad';
  form.precio_venta = Number(item.precio_venta || 0);
  form.location = item.location || 'Recepcion';
  form.status = item.status || 'Operativo';
  form.observations = item.observations || '';
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

/**
 * Gestiona esta acción de la vista.
 */
const handleSubmit = async () => {
  try {
    await gymStore.upsertInventoryItem({ id: editingId.value || undefined, ...form });
    const savedLabel = editingId.value ? 'Articulo actualizado.' : 'Articulo registrado.';
    closeEditor();
    feedbackTone.value = 'success';
    feedbackMessage.value = savedLabel;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el articulo.';
  }
};

/**
 * Elimina el registro indicado.
 */
const deleteItem = async (id) => {
  if (!window.confirm('Eliminar este articulo?\n\nSi ya tiene movimientos o se vende en Tienda no se borrara: quedara como "Descontinuado" para conservar su historial.')) return;
  try {
    const result = await gymStore.deleteInventoryItem(id);
    feedbackTone.value = 'success';
    feedbackMessage.value = result?.accion === 'descontinuado'
      ? 'El articulo tiene historial o se vende en Tienda: se marco como Descontinuado.'
      : 'Articulo eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el articulo.';
  }
};

onMounted(() => {
  gymStore.fetchFromBackend?.({ section: 'inventory' }).catch((error) => console.warn('No se pudo refrescar inventario:', error));
});
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