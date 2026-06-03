<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Recursos</p>
      <h1 class="mt-2 text-3xl font-black text-white">Inventario</h1>
      <p class="mt-2 text-slate-300">Controla stock, ubicación, estado operativo y observaciones de cada recurso del gimnasio.</p>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Artículo</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar elemento' : 'Nuevo elemento' }}</h2>

        <div class="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-50">
          <p class="text-xs uppercase tracking-[0.35em] text-cyan-200">Identificador único</p>
          <p class="mt-1 font-semibold text-white">{{ currentInventoryCode }}</p>
        </div>

        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="form.name" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Nombre del artículo" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Categoría</span>
            <input v-model="form.category" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Equipos, bebidas..." />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Cantidad</span>
            <input v-model.number="form.quantity" type="number" min="0" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Ubicación</span>
            <input v-model="form.location" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Sala 1" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="form.status" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
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
            <textarea
              v-model="form.observations"
              rows="3"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none"
              placeholder="Estado del equipo, mantenimiento pendiente, incidencias..."
            ></textarea>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar cambios' : 'Agregar artículo' }}
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
            <h2 class="mt-2 text-2xl font-black text-white">Listado de inventario</h2>
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

        <div class="mt-5 space-y-3">
          <article v-for="item in inventory" :key="item.id" class="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.35em] text-cyan-200">{{ item.inventoryCode }}</p>
                <p class="mt-1 font-semibold text-white">{{ item.name }}</p>
                <p class="text-sm text-slate-400">{{ item.category }} · {{ item.location }}</p>
                <p class="mt-1 text-sm text-slate-300">Cantidad: {{ item.quantity }}</p>
                <p class="mt-1 text-sm text-cyan-200">Estado: {{ item.status }}</p>
                <p class="mt-1 text-sm text-slate-400">{{ item.observations || 'Sin observaciones' }}</p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editItem(item)">
                  Editar
                </button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteItem(item.id)">
                  Eliminar
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const inventory = computed(() => gymStore.inventory);
const lowStock = computed(() => gymStore.lowStockInventory);
const maintenanceItems = computed(() => inventory.value.filter((item) => item.status === 'En mantenimiento').length);
const editingId = ref('');
const currentInventoryCode = computed(() => {
  if (editingId.value) {
    return inventory.value.find((item) => item.id === editingId.value)?.inventoryCode || 'Se generará automáticamente';
  }

  return 'Se generará automáticamente';
});

const form = reactive({
  name: '',
  category: 'General',
  quantity: 0,
  location: 'Recepción',
  status: 'Operativo',
  observations: '',
});

const resetForm = () => {
  editingId.value = '';
  form.name = '';
  form.category = 'General';
  form.quantity = 0;
  form.location = 'Recepción';
  form.status = 'Operativo';
  form.observations = '';
};

const editItem = (item) => {
  editingId.value = item.id;
  form.name = item.name;
  form.category = item.category;
  form.quantity = item.quantity;
  form.location = item.location;
  form.status = item.status;
  form.observations = item.observations || '';
};

const handleSubmit = async () => {
  try {
    await gymStore.upsertInventoryItem({ id: editingId.value || undefined, ...form });
    resetForm();
  } catch (error) {
    console.error('Error al guardar inventario:', error);
  }
};

const deleteItem = (id) => {
  gymStore.deleteInventoryItem(id);
};
</script>
