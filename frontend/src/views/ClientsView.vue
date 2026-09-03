<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Administracion</p>
          <h1 class="mt-2 text-3xl font-black text-white">Clientes del sistema</h1>
          <p class="mt-2 text-slate-300">Gestiona clientes, datos de contacto y activacion de membresias.</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ clients.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Activos</p>
            <p class="text-xl font-black text-white">{{ activeClients }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">En tramite</p>
            <p class="text-xl font-black text-white">{{ pendingClients }}</p>
          </div>
        </div>
      </div>

      <div class="mt-5 flex gap-2 border-b border-white/10">
        <button
          class="px-4 py-2 text-sm font-medium transition"
          :class="activeTab === 'clientes' ? 'border-b-2 border-cyan-400 text-cyan-300' : 'text-slate-400 hover:text-slate-200'"
          @click="activeTab = 'clientes'"
        >
          Gestion de Clientes
        </button>
        <button
          class="px-4 py-2 text-sm font-medium transition"
          :class="activeTab === 'tienda' ? 'border-b-2 border-cyan-400 text-cyan-300' : 'text-slate-400 hover:text-slate-200'"
          @click="activeTab = 'tienda'"
        >
          Tienda para Clientes
        </button>
      </div>
    </section>

    <section v-if="activeTab === 'clientes'" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Lista</p>
          <h2 class="mt-2 text-2xl font-black text-white">Clientes registrados</h2>
        </div>
        <div class="flex flex-col gap-3 sm:flex-row">
          <input v-model="search" class="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none" placeholder="Buscar por ID, nombre, DNI o correo..." />
          <button class="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950" @click="openNewClient">
            Nuevo cliente
          </button>
        </div>
      </div>

      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <div class="mt-5 overflow-x-auto">
        <table class="w-full min-w-[960px] text-left text-sm">
          <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <th class="px-5 py-4 font-bold">ID</th>
              <th class="px-5 py-4 font-bold">Cliente</th>
              <th class="px-5 py-4 font-bold">Plan</th>
              <th class="px-5 py-4 font-bold">Membresia</th>
              <th class="px-5 py-4 font-bold">Vigencia</th>
              <th class="px-5 py-4 font-bold">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="client in filteredClients" :key="client.id" class="transition hover:bg-white/[0.04]">
              <td class="px-5 py-4 align-top">
                <span class="rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-cyan-100">{{ client.id }}</span>
              </td>
              <td class="px-5 py-4 align-top font-bold text-white">{{ client.name || 'Sin nombre' }}</td>
              <td class="px-5 py-4 align-top text-slate-300">{{ client.plan || 'MENSUAL' }}</td>
              <td class="px-5 py-4 align-top">
                <span :class="statusClass(displayMembershipStatus(client))">{{ displayMembershipStatus(client) }}</span>
              </td>
              <td class="px-5 py-4 align-top text-slate-400">
                {{ client.membershipStart || 'por activar' }} - {{ client.membershipEnd || 'por activar' }}
              </td>
              <td class="px-5 py-4 align-top">
                <div class="flex shrink-0 flex-wrap gap-2">
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-white/10 text-white hover:bg-white/5"
                    title="Ver detalles"
                    @click="openDetails(client)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
                      <circle cx="12" cy="12" r="9" />
                      <line x1="12" y1="11" x2="12" y2="16" />
                      <circle cx="12" cy="7.5" r="0.75" fill="currentColor" stroke="none" />
                    </svg>
                  </button>
                  <button
                    v-if="isPendingMembership(client)"
                    type="button"
                    class="rounded-xl bg-emerald-400 px-3 py-2 text-xs font-bold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                    :disabled="activatingClientId === client.id"
                    @click="activateMembership(client)"
                  >
                    {{ activatingClientId === client.id ? 'Activando...' : 'Activar' }}
                  </button>
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-white/10 text-white hover:bg-white/5"
                    title="Editar"
                    @click="editClient(client)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
                      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-rose-400/30 text-rose-100 hover:bg-rose-400/10"
                    title="Eliminar"
                    @click="confirmDelete(client)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
                      <path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!filteredClients.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
        No hay clientes para mostrar.
      </p>
    </section>

    <section v-if="activeTab === 'tienda'" class="space-y-6">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catalogo</p>
        <h2 class="mt-2 text-2xl font-black text-white">Productos disponibles</h2>
        <p class="mt-1 text-sm text-slate-400">Estos productos se muestran en la tienda del cliente.</p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
        <div v-for="producto in productos" :key="producto.id_producto" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
          <div class="mb-3 flex aspect-square items-center justify-center rounded-xl bg-cyan-400/10 text-sm font-black uppercase tracking-[0.2em] text-cyan-100">
            Stock
          </div>
          <p class="text-xs font-bold uppercase text-cyan-200">{{ producto.categoria }}</p>
          <p class="mt-1 truncate font-semibold text-white">{{ producto.nombre }}</p>
          <p class="mt-1 line-clamp-2 text-xs text-slate-400">{{ producto.descripcion }}</p>
          <p class="mt-3 text-lg font-black text-emerald-300">S/. {{ Number(producto.precio || 0).toFixed(2) }}</p>
          <p class="mt-1 text-xs text-slate-400">Stock: {{ producto.cantidad }}</p>
        </div>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="isEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <form class="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl" @submit.prevent="handleSubmit">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Cliente</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar cliente' : 'Nuevo cliente' }}</h2>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeEditor">
              Cerrar
            </button>
          </div>

          <div class="mt-6 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Nombre</span>
              <input v-model="form.nombre" class="field-input" placeholder="Jose Perez" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Correo</span>
              <input v-model="form.correo" type="email" class="field-input" placeholder="cliente@correo.com" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Contrasena</span>
              <input v-model="form.password" type="password" autocomplete="new-password" class="field-input" :placeholder="editingId ? 'Dejar vacio para conservar la actual' : 'Minimo 6 caracteres'" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Telefono</span>
              <input v-model="form.telefono" class="field-input" placeholder="999 111 222" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">DNI</span>
              <input v-model="form.dni" class="field-input" placeholder="12345678" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Plan</span>
              <select v-model="form.plan" class="field-input">
                <option value="MENSUAL">MENSUAL</option>
                <option value="3 MESES">3 MESES</option>
                <option value="ANUAL">ANUAL</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Promocion</span>
              <select v-model="form.promocion" class="field-input">
                <option value="SIN PROMOCION">SIN PROMOCION</option>
                <option v-for="p in gymStore.promotions" :key="p.id" :value="p.name">{{ p.name }}</option>
              </select>
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Estado</span>
              <select v-model="form.estado" class="field-input">
                <option value="EN_TRAMITE">EN_TRAMITE</option>
                <option value="ACTIVO">ACTIVO</option>
                <option value="INACTIVO">INACTIVO</option>
              </select>
            </label>
          </div>

          <button type="submit" class="mt-6 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
            {{ editingId ? 'Guardar cambios' : 'Registrar cliente' }}
          </button>
        </form>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="isDetailsOpen && viewingClient" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <div class="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Detalles</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ viewingClient.name || 'Sin nombre' }}</h2>
              <span class="mt-2 inline-block rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-cyan-100">{{ viewingClient.id }}</span>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeDetails">
              Cerrar
            </button>
          </div>

          <div class="mt-6 space-y-2">
            <p class="text-sm text-slate-400">Correo: <span class="text-slate-200">{{ viewingClient.email || 'Sin correo' }}</span></p>
            <p class="text-sm text-slate-400">DNI: <span class="text-slate-200">{{ viewingClient.dni || 'Sin DNI' }}</span></p>
            <p class="text-sm text-slate-400">Telefono: <span class="text-slate-200">{{ viewingClient.phone || 'Sin telefono' }}</span></p>
            <p class="text-sm text-slate-300">Plan: <span class="text-slate-200">{{ viewingClient.plan || 'MENSUAL' }} - {{ viewingClient.promocion || 'SIN PROMOCION' }}</span></p>
            <p class="text-sm text-slate-300">
              Membresia: <span :class="statusClass(displayMembershipStatus(viewingClient))">{{ displayMembershipStatus(viewingClient) }}</span>
            </p>
            <p class="text-sm text-slate-400">
              Vigencia: <span class="text-slate-200">{{ viewingClient.membershipStart || 'por activar' }} - {{ viewingClient.membershipEnd || 'por activar' }}</span>
            </p>
            <p v-if="viewingClient.paymentReference || viewingClient.paymentStatus" class="text-sm text-slate-400">
              Pago: <span class="text-slate-200">{{ viewingClient.paymentStatus || 'PENDIENTE' }} {{ viewingClient.paymentReference ? `- ${viewingClient.paymentReference}` : '' }}</span>
            </p>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const clients = computed(() => gymStore.members);
const productos = computed(() => gymStore.productos_tienda);
const search = ref('');
const activeTab = ref('clientes');
const editingId = ref('');
const isEditorOpen = ref(false);
const isDetailsOpen = ref(false);
const viewingClient = ref(null);
const feedbackMessage = ref('');
const feedbackTone = ref('info');
const activatingClientId = ref('');

const form = reactive({
  nombre: '',
  correo: '',
  telefono: '',
  dni: '',
  password: '',
  plan: 'MENSUAL',
  promocion: 'SIN PROMOCION',
  estado: 'EN_TRAMITE',
});

const normalizeStatus = (value) => String(value || '').trim().toUpperCase();
const displayMembershipStatus = (client) => normalizeStatus(client.membershipStatus || client.status || 'EN_TRAMITE');
const isActiveStatus = (value) => ['ACTIVO', 'ACTIVA'].includes(normalizeStatus(value));
const isPendingStatus = (value) => normalizeStatus(value).includes('TRAMITE');
const isPendingMembership = (client) => isPendingStatus(displayMembershipStatus(client)) || isPendingStatus(client.status);

const statusClass = (value) => {
  if (isActiveStatus(value)) return 'font-semibold text-emerald-300';
  if (isPendingStatus(value)) return 'font-semibold text-amber-300';
  return 'font-semibold text-slate-300';
};

const filteredClients = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return clients.value;
  return clients.value.filter((client) =>
    [client.id, client.name, client.email, client.phone, client.dni, client.plan, client.promocion, client.status, client.membershipStatus, client.paymentReference]
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
});

const activeClients = computed(() => clients.value.filter((client) => isActiveStatus(displayMembershipStatus(client))).length);
const pendingClients = computed(() => clients.value.filter((client) => isPendingMembership(client)).length);
const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const resetForm = () => {
  editingId.value = '';
  form.nombre = '';
  form.correo = '';
  form.telefono = '';
  form.dni = '';
  form.password = '';
  form.plan = 'MENSUAL';
  form.promocion = 'SIN PROMOCION';
  form.estado = 'EN_TRAMITE';
};

const openNewClient = () => {
  resetForm();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

const editClient = (client) => {
  editingId.value = client.id;
  form.nombre = client.name || '';
  form.correo = client.email || '';
  form.telefono = client.phone || '';
  form.dni = client.dni || '';
  form.password = '';
  form.plan = client.plan || 'MENSUAL';
  form.promocion = client.promocion || 'SIN PROMOCION';
  form.estado = client.status || 'ACTIVO';
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

const openDetails = (client) => {
  viewingClient.value = client;
  isDetailsOpen.value = true;
};

const closeDetails = () => {
  isDetailsOpen.value = false;
  viewingClient.value = null;
};

const confirmDelete = async (client) => {
  if (!window.confirm(`Eliminar al cliente ${client.id}?`)) return;
  try {
    await gymStore.deleteClient(client.id);
    feedbackTone.value = 'success';
    feedbackMessage.value = `Cliente ${client.id} eliminado.`;
    if (editingId.value === client.id) closeEditor();
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el cliente.';
  }
};

const activateMembership = async (client) => {
  const idCliente = client.id_cliente || Number(String(client.id || '').replace(/^SGCLI/i, ''));
  if (!idCliente) {
    feedbackTone.value = 'error';
    feedbackMessage.value = 'No se encontro el ID numerico del cliente.';
    return;
  }

  activatingClientId.value = client.id;
  try {
    const saved = await gymStore.activateClientMembership(idCliente);
    feedbackTone.value = 'success';
    feedbackMessage.value = `Membresia de ${saved.id} activada.`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo activar la membresia.';
  } finally {
    activatingClientId.value = '';
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
      password: form.password,
      plan: form.plan,
      promocion: form.promocion,
      estado: form.estado,
    });

    closeEditor();
    feedbackTone.value = 'success';
    feedbackMessage.value = `Cliente ${saved.id} guardado con estado ${saved.status || form.estado}.`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el cliente.';
  }
};

onMounted(() => {
  gymStore.fetchFromBackend?.().catch((error) => console.warn('No se pudo refrescar clientes:', error));
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
