<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Recursos</p>
      <h1 class="mt-2 text-3xl font-black text-white">Inventario</h1>
      <p class="mt-2 max-w-3xl text-slate-300">Controla stock, ubicación, estado operativo y movimientos de cada recurso del gimnasio.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Artículos</p>
        <p class="mt-2 text-3xl font-black text-white">{{ inventory.length }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Stock bajo</p>
        <p class="mt-2 text-3xl font-black text-white">{{ lowStock.length }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Movimientos</p>
        <p class="mt-2 text-3xl font-black text-white">{{ movements.length }}</p>
      </article>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Artículo</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar elemento' : 'Nuevo elemento' }}</h2>

        <div class="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-50">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-200">Identificador único</p>
          <p class="mt-1 font-semibold text-white">{{ currentInventoryCode }}</p>
        </div>

        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="sm:col-span-2 space-y-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="form.nombre_item" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Nombre del artículo" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Tipo</span>
            <input v-model="form.tipo" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Equipos, bebidas..." />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Cantidad</span>
            <input v-model.number="form.cantidad_stock" type="number" min="0" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Mínimo</span>
            <input v-model.number="form.stock_minimo" type="number" min="0" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="form.estado" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Operativo</option>
              <option>En mantenimiento</option>
              <option>Fuera de servicio</option>
              <option>Dado de baja</option>
            </select>
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Observaciones</span>
            <textarea v-model="form.observaciones" rows="3" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Estado del equipo, mantenimiento pendiente, incidencias..."></textarea>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar cambios' : 'Agregar artículo' }}
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Listado</p>
            <h2 class="mt-2 text-2xl font-black text-white">Inventario y movimientos</h2>
          </div>
          <div class="rounded-2xl bg-slate-950/70 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Stock bajo</p>
            <p class="text-xl font-black text-white">{{ lowStock.length }}</p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="item in inventory" :key="item.id_item" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.5em] text-cyan-200">#{{ item.id_item }}</p>
                <p class="mt-1 font-semibold text-white">{{ item.nombre_item }}</p>
                <p class="text-sm text-slate-400">{{ item.tipo }}</p>
                <p class="mt-1 text-sm text-slate-300">Cantidad: {{ item.cantidad_stock }} · Mínimo: {{ item.stock_minimo }}</p>
                <p class="mt-1 text-sm text-cyan-200">Estado: {{ item.estado }}</p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editItem(item)">Editar</button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteItem(item.id_item)">Eliminar</button>
              </div>
            </div>
          </article>
        </div>

        <div class="mt-8 rounded-[1.75rem] border border-white/10 bg-slate-950/60 p-5">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Movimientos recientes</p>
          <form class="mt-4 grid gap-4 sm:grid-cols-2" @submit.prevent="handleMovementSubmit">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Artículo</span>
              <select v-model.number="movementForm.id_item" class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none">
                <option v-for="item in inventory" :key="item.id_item" :value="item.id_item">{{ item.nombre_item }}</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Usuario responsable</span>
              <select v-model.number="movementForm.id_usuario" class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none">
                <option v-for="user in users" :key="user.id_usuario" :value="user.id_usuario">{{ user.email || `Usuario #${user.id_usuario}` }}</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Tipo</span>
              <select v-model="movementForm.tipo_movimiento" class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none">
                <option value="entrada">Entrada</option>
                <option value="salida">Salida</option>
                <option value="ajuste">Ajuste</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Cantidad</span>
              <input v-model.number="movementForm.cantidad" type="number" min="1" class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none" />
            </label>
            <label class="sm:col-span-2 space-y-2">
              <span class="text-sm text-slate-300">Descripción</span>
              <input v-model="movementForm.descripcion" class="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none" placeholder="Motivo del ajuste" />
            </label>
            <button class="sm:col-span-2 rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300" type="submit">Registrar movimiento</button>
          </form>

          <div class="mt-5 space-y-3">
            <article v-for="movement in movements.slice(0, 5)" :key="movement.id_mov" class="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
              <div class="flex items-center justify-between gap-4">
                <div>
                  <p class="font-semibold text-white">{{ movement.tipo_movimiento }}</p>
                  <p class="text-slate-400">Item #{{ movement.id_item }} · Cantidad {{ movement.cantidad }}</p>
                </div>
                <p class="text-slate-300">{{ movement.fecha_movimiento }}</p>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const { user } = useAuth();
const inventory = computed(() => gymStore.inventory);
const movements = computed(() => gymStore.movements || []);
const lowStock = computed(() => gymStore.lowStockInventory);
const users = computed(() => gymStore.users);
const editingId = ref('');
const currentInventoryCode = computed(() => (editingId.value ? `#${editingId.value}` : 'Se generará automáticamente'));

const form = reactive({
  nombre_item: '',
  tipo: 'General',
  cantidad_stock: 0,
  stock_minimo: 0,
  estado: 'Operativo',
  observaciones: '',
});

const movementForm = reactive({
  id_item: 0,
  id_usuario: 0,
  tipo_movimiento: 'entrada',
  cantidad: 1,
  descripcion: '',
});

watch(
  inventory,
  (items) => {
    if (!movementForm.id_item && items.length) {
      movementForm.id_item = items[0].id_item;
    }
  },
  { immediate: true },
);

watch(
  users,
  (list) => {
    if (!movementForm.id_usuario && list.length) {
      const currentUser = list.find((entry) => entry.email === user.value?.email) || list[0];
      movementForm.id_usuario = currentUser?.id_usuario || 0;
    }
  },
  { immediate: true },
);

const resetForm = () => {
  editingId.value = '';
  form.nombre_item = '';
  form.tipo = 'General';
  form.cantidad_stock = 0;
  form.stock_minimo = 0;
  form.estado = 'Operativo';
  form.observaciones = '';
};

const editItem = (item) => {
  editingId.value = String(item.id_item);
  form.nombre_item = item.nombre_item;
  form.tipo = item.tipo;
  form.cantidad_stock = item.cantidad_stock;
  form.stock_minimo = item.stock_minimo;
  form.estado = item.estado;
  form.observaciones = item.observaciones || '';
};

const handleSubmit = async () => {
  await gymStore.upsertInventoryItem({ id_item: editingId.value || undefined, ...form });
  resetForm();
};

const deleteItem = async (idItem) => {
  await gymStore.deleteInventoryItem(idItem);
};

const handleMovementSubmit = async () => {
  await gymStore.registrarMovimientoToServer({
    ...movementForm,
    fecha_movimiento: new Date().toISOString().slice(0, 10),
  });
};
</script>
