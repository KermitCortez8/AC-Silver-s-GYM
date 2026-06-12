<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Recursos</p>
          <h1 class="mt-2 text-3xl font-black text-white">Inventario</h1>
          <p class="mt-2 text-slate-300">Controla stock, ubicacion, estado operativo y observaciones de cada recurso del gimnasio.</p>
        </div>

        <button class="rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300" @click="openNewItem">
          Ingresar Nuevo Articulo
        </button>
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
          <h2 class="mt-2 text-2xl font-black text-white">Listado de inventario</h2>
        </div>
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ inventory.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Stock bajo</p>
            <p class="text-xl font-black text-white">{{ lowStock.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">En mantenimiento</p>
            <p class="text-xl font-black text-white">{{ maintenanceItems }}</p>
          </div>
        </div>
      </div>

      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <div class="mt-5 grid gap-4 xl:grid-cols-2">
        <article v-for="item in inventory" :key="item.id" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-lg font-bold text-white">{{ item.name }}</p>
                <span class="rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-amber-100">{{ item.inventoryCode }}</span>
              </div>
              <p class="mt-2 text-sm text-slate-400">{{ item.category }} | {{ item.location }}</p>
              <p class="mt-1 text-sm text-slate-300">Cantidad: {{ item.quantity }} | Stock min.: {{ item.minQuantity }}</p>
              <p class="mt-1 text-sm text-slate-300">Unidad venta: {{ item.unidad_venta }} | Precio venta: S/. {{ Number(item.precio_venta || 0).toFixed(2) }}</p>
              <p class="mt-1 text-sm text-amber-200">N. Activo: {{ item.n_activo || 'Auto' }} | Estado: {{ item.status }}</p>
              <p class="mt-1 text-sm text-slate-400">{{ item.observations || 'Sin observaciones' }}</p>
            </div>

            <div class="flex shrink-0 gap-2">
              <button class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="editItem(item)">
                Editar
              </button>
              <button class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 hover:bg-rose-400/10" @click="deleteItem(item.id)">
                Eliminar
              </button>
            </div>
          </div>
        </article>
      </div>

      <p v-if="!inventory.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
        No hay articulos en inventario. Usa "Ingresar Nuevo Articulo" para registrar el primero.
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

          <div class="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-50">
            <p class="text-xs uppercase tracking-[0.35em] text-amber-200">Identificador unico</p>
            <p class="mt-1 font-semibold text-white">{{ currentInventoryCode }}</p>
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Nombre</span>
              <input v-model="form.name" class="field-input" placeholder="Nombre del articulo" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Categoria</span>
              <input v-model="form.category" class="field-input" placeholder="Equipos, bebidas..." />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Cantidad</span>
              <input v-model.number="form.quantity" type="number" min="0" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Unidad de venta</span>
              <input v-model="form.unidad_venta" class="field-input" placeholder="unidad, botella, paquete..." />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Precio de venta (S/.)</span>
              <input v-model.number="form.precio_venta" type="number" min="0" step="0.01" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Stock minimo</span>
              <input v-model.number="form.minQuantity" type="number" min="0" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Ubicacion</span>
              <input v-model="form.location" class="field-input" placeholder="Sala 1" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Estado</span>
              <select v-model="form.status" class="field-input">
                <option>Operativo</option>
                <option>En mantenimiento</option>
                <option>Fuera de servicio</option>
                <option>Dado de baja</option>
                <option>Stock bajo</option>
                <option>Agotado</option>
              </select>
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Observaciones</span>
              <textarea v-model="form.observations" rows="3" class="field-input" placeholder="Estado del equipo, mantenimiento pendiente, incidencias..."></textarea>
            </label>
          </div>

          <button type="submit" class="mt-6 w-full rounded-2xl bg-amber-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-amber-300">
            {{ editingId ? 'Guardar cambios' : 'Agregar articulo' }}
          </button>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const inventory = computed(() => gymStore.inventory);
const lowStock = computed(() => gymStore.lowStockInventory);
const maintenanceItems = computed(() => inventory.value.filter((item) => item.status === 'En mantenimiento').length);
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

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const currentInventoryCode = computed(() => {
  if (editingId.value) {
    return inventory.value.find((item) => item.id === editingId.value)?.inventoryCode || 'Se generara automaticamente';
  }

  return 'Se generara automaticamente';
});

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

const openNewItem = () => {
  resetForm();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

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

const deleteItem = async (id) => {
  if (!window.confirm('Eliminar este articulo?')) return;
  try {
    await gymStore.deleteInventoryItem(id);
    feedbackTone.value = 'success';
    feedbackMessage.value = 'Articulo eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el articulo.';
  }
};

onMounted(() => {
  gymStore.fetchFromBackend?.().catch((error) => console.warn('No se pudo refrescar inventario:', error));
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
