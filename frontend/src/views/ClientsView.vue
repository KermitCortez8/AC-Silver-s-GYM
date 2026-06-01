<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Administración</p>
          <h1 class="mt-2 text-3xl font-black text-white">Clientes del sistema</h1>
          <p class="mt-2 text-slate-300">Administra expedientes de clientes con id SGCLI, datos de contacto y membresía fija.</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ clients.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Activos</p>
            <p class="text-xl font-black text-white">{{ activeClients }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Formulario</p>
            <h2 class="text-2xl font-black text-white">{{ editingId ? 'Editar cliente' : 'Nuevo cliente' }}</h2>
          </div>
          <button v-if="editingId" type="button" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm" @click="resetForm">
            Cancelar
          </button>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="form.nombre" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="Jose Perez" />
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="form.correo" type="email" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="cliente@correo.com" />
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Teléfono</span>
            <input v-model="form.telefono" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="999 111 222" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">DNI</span>
            <input v-model="form.dni" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="12345678" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Plan</span>
            <select v-model="form.plan" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="MENSUAL">MENSUAL</option>
              <option value="3 MESES">3 MESES</option>
              <option value="ANUAL">ANUAL</option>
            </select>
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Promoción</span>
            <select v-model="form.promocion" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="SIN PROMOCION">SIN PROMOCION</option>
              <option v-for="p in gymStore.promotions" :key="p.id" :value="p.name">{{ p.name }}</option>
            </select>
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="form.estado" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="ACTIVO">ACTIVO</option>
            </select>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar cliente' : 'Registrar cliente' }}
        </button>

        <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
          {{ feedbackMessage }}
        </p>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Lista</p>
            <h2 class="text-2xl font-black text-white">Clientes registrados</h2>
          </div>
          <input v-model="search" class="rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-white outline-none" placeholder="Buscar por ID, nombre o correo..." />
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="client in filteredClients" :key="client.id" class="rounded-3xl border border-white/10 bg-slate-900/80 p-5">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-bold text-white">{{ client.name || 'Sin nombre' }}</p>
                <p class="text-sm text-slate-400">ID: {{ client.id }}</p>
                <p class="text-sm text-slate-400">Correo: {{ client.email || 'Sin correo' }}</p>
                <p class="text-sm text-slate-400">Teléfono: {{ client.phone || 'Sin teléfono' }}</p>
                <p class="text-sm text-slate-400">DNI: {{ client.dni || 'Sin DNI' }}</p>
                <p class="mt-2 text-sm text-slate-300">Plan: {{ client.plan || 'MENSUAL' }} · Promoción: {{ client.promocion || 'SIN PROMOCION' }}</p>
                <p class="mt-1 text-sm text-cyan-200">Estado: {{ client.status || 'ACTIVO' }}</p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editClient(client)">
                  Editar
                </button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="confirmDelete(client)">
                  Eliminar
                </button>
              </div>
            </div>
          </article>
        </div>

        <p v-if="!filteredClients.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
          No hay clientes para mostrar.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const clients = computed(() => gymStore.members);
const search = ref('');
const editingId = ref('');
const feedbackMessage = ref('');
const feedbackTone = ref('info');

const form = reactive({
  nombre: '',
  correo: '',
  telefono: '',
  dni: '',
  plan: 'MENSUAL',
  promocion: 'SIN PROMOCION',
  estado: 'ACTIVO',
});

const filteredClients = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) {
    return clients.value;
  }

  return clients.value.filter((client) =>
    [client.id, client.name, client.email, client.phone, client.dni, client.plan, client.promocion, client.status]
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
});

const activeClients = computed(() => clients.value.filter((client) => String(client.status).toUpperCase() === 'ACTIVO').length);
const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') {
    return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  }

  if (feedbackTone.value === 'error') {
    return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  }

  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const resetForm = () => {
  editingId.value = '';
  form.nombre = '';
  form.correo = '';
  form.telefono = '';
  form.dni = '';
  form.plan = 'MENSUAL';
  form.promocion = 'SIN PROMOCION';
  form.estado = 'ACTIVO';
};

const editClient = (client) => {
  editingId.value = client.id;
  form.nombre = client.name || '';
  form.correo = client.email || '';
  form.telefono = client.phone || '';
  form.dni = client.dni || '';
  form.plan = client.plan || 'MENSUAL';
  form.promocion = client.promocion || 'SIN PROMOCION';
  form.estado = client.status || 'ACTIVO';
};

const confirmDelete = async (client) => {
  const confirmed = window.confirm(`Eliminar al cliente ${client.id}?`);
  if (!confirmed) {
    return;
  }

  try {
    await gymStore.deleteClient(client.id);
    feedbackTone.value = 'success';
    feedbackMessage.value = `Cliente ${client.id} eliminado.`;
    if (editingId.value === client.id) {
      resetForm();
    }
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el cliente.';
  }
};

const handleSubmit = async () => {
  try {
    const saved = await gymStore.upsertClient({
      id_usuario: editingId.value || undefined,
      nombre: form.nombre,
      correo: form.correo,
      telefono: form.telefono,
      dni: form.dni,
      plan: form.plan,
      promocion: form.promocion,
      estado: form.estado,
    });

    resetForm();
    feedbackTone.value = 'success';
    feedbackMessage.value = `Cliente ${saved.id} guardado con estado ACTIVO.`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el cliente.';
    console.error('Error al guardar cliente:', error);
  }
};

onMounted(() => {
  if (gymStore.fetchFromBackend) {
    gymStore.fetchFromBackend().catch((error) => console.warn('No se pudo refrescar clientes:', error));
  }
});
</script>
