<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Administración</p>
      <h1 class="mt-2 text-3xl font-black text-white">Clientes, usuarios, planes y tickets</h1>
      <p class="mt-2 max-w-4xl text-slate-300">Esta vista agrupa los recursos que el backend expone por separado para que la operación diaria no salte entre pantallas.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-5">
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Clientes</p>
        <p class="mt-2 text-3xl font-black text-white">{{ memberCards.length }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Usuarios</p>
        <p class="mt-2 text-3xl font-black text-white">{{ users.length }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Planes</p>
        <p class="mt-2 text-3xl font-black text-white">{{ plans.length }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Membresías</p>
        <p class="mt-2 text-3xl font-black text-white">{{ memberships.length }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Tickets</p>
        <p class="mt-2 text-3xl font-black text-white">{{ tickets.length }}</p>
      </article>
    </section>

    <section class="flex flex-wrap gap-2">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="rounded-full px-4 py-2 text-sm font-medium transition"
        :class="activeTab === tab.key ? 'bg-cyan-400 text-slate-950' : 'bg-white/5 text-slate-200'"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">{{ activeTitle }}</p>
            <h2 class="mt-2 text-2xl font-black text-white">{{ formTitle }}</h2>
          </div>
          <button v-if="editingKey" type="button" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white" @click="resetForms">Cancelar</button>
        </div>

        <div v-if="activeTab === 'clientes'" class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nombres</span>
            <input v-model="clientForm.nombres" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="María" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Apellidos</span>
            <input v-model="clientForm.apellidos" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Fernández" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">DNI</span>
            <input v-model="clientForm.dni" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="74281635" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Teléfono</span>
            <input v-model="clientForm.telefono" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="999 111 222" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="clientForm.email" type="email" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="correo@ejemplo.com" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Registro</span>
            <input v-model="clientForm.fecha_registro" type="date" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="clientForm.estado" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option :value="true">Activa</option>
              <option :value="false">Inactiva</option>
            </select>
          </label>
          <label class="sm:col-span-2 flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3">
            <input v-model="clientForm.assignMembership" type="checkbox" class="h-4 w-4 accent-cyan-300" />
            <span class="text-sm text-slate-300">Asignar membresía al guardar</span>
          </label>
          <label v-if="clientForm.assignMembership" class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Plan</span>
            <select v-model.number="clientForm.id_pm" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option v-for="plan in plans" :key="plan.id_pm" :value="plan.id_pm">{{ plan.nombre_plan }} · S/ {{ plan.precio }}</option>
            </select>
          </label>
        </div>

        <div v-if="activeTab === 'usuarios'" class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">DNI</span>
            <input v-model="userForm.dni" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="71928451" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="userForm.email" type="email" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="admin@urp.edu.pe" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Contraseña</span>
            <input v-model="userForm.contrasena" type="password" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Opcional" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Rol</span>
            <select v-model="userForm.rol" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="admin">admin</option>
              <option value="user">user</option>
              <option value="trainer">trainer</option>
              <option value="staff">staff</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="userForm.estado" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option :value="true">Activo</option>
              <option :value="false">Inactivo</option>
            </select>
          </label>
        </div>

        <div v-if="activeTab === 'planes'" class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nombre del plan</span>
            <input v-model="planForm.nombre_plan" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Mensual" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Duración</span>
            <input v-model="planForm.duracion" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="30 días" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Precio</span>
            <input v-model.number="planForm.precio" type="number" min="0" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
        </div>

        <div v-if="activeTab === 'tickets'" class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Cliente</span>
            <select v-model.number="ticketForm.id_cliente" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option v-for="member in memberCards" :key="member.id_cliente" :value="member.id_cliente">{{ member.name }}</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Usuario responsable</span>
            <select v-model.number="ticketForm.id_usuario" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option v-for="userItem in users" :key="userItem.id_usuario" :value="userItem.id_usuario">{{ userItem.email || `Usuario #${userItem.id_usuario}` }}</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Tipo</span>
            <input v-model="ticketForm.tipo_ticket" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Consulta" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="ticketForm.estado_ticket" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Abierto</option>
              <option>En proceso</option>
              <option>Cerrado</option>
            </select>
          </label>
          <label class="sm:col-span-2 space-y-2">
            <span class="text-sm text-slate-300">Descripción</span>
            <textarea v-model="ticketForm.descripcion" rows="4" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Detalle del ticket"></textarea>
          </label>
        </div>

        <button type="submit" class="mt-6 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ submitLabel }}
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">{{ activeTitle }}</p>
            <h2 class="mt-2 text-2xl font-black text-white">{{ listTitle }}</h2>
          </div>
          <input v-model="search" class="w-full max-w-xs rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-white outline-none" placeholder="Buscar..." />
        </div>

        <div class="mt-5 space-y-3">
          <article v-if="activeTab === 'clientes'" v-for="member in filteredMembers" :key="member.id" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="font-semibold text-white">{{ member.name }}</p>
                <p class="text-sm text-slate-400">{{ member.email }} · {{ member.phone }}</p>
                <p class="text-sm text-slate-400">DNI: {{ member.dni || 'N/D' }} · Código: {{ member.internalCode }}</p>
                <p class="mt-1 text-sm text-cyan-200">{{ member.plan }} · {{ member.status }}</p>
              </div>
              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editMember(member)">Editar</button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteMember(member.id)">Eliminar</button>
              </div>
            </div>
          </article>

          <article v-if="activeTab === 'usuarios'" v-for="item in users" :key="item.id_usuario" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="font-semibold text-white">{{ item.email || `Usuario #${item.id_usuario}` }}</p>
                <p class="text-sm text-slate-400">DNI: {{ item.dni }} · Rol: {{ item.rol }}</p>
              </div>
              <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteUsuario(item.id_usuario)">Eliminar</button>
            </div>
          </article>

          <article v-if="activeTab === 'planes'" v-for="plan in plans" :key="plan.id_pm" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="font-semibold text-white">{{ plan.nombre_plan }}</p>
                <p class="text-sm text-slate-400">{{ plan.duracion }}</p>
              </div>
              <p class="text-cyan-200">S/ {{ plan.precio }}</p>
            </div>
          </article>

          <article v-if="activeTab === 'membresias'" v-for="membership in memberships" :key="membership.id_membresia" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <p class="font-semibold text-white">Cliente #{{ membership.id_cliente }} · Plan #{{ membership.id_pm }}</p>
            <p class="text-sm text-slate-400">{{ membership.fecha_inicio }} → {{ membership.fecha_fin }} · {{ membership.estado }}</p>
          </article>

          <article v-if="activeTab === 'tickets'" v-for="ticket in tickets" :key="ticket.id_ticket" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <p class="font-semibold text-white">{{ ticket.tipo_ticket }} · {{ ticket.estado_ticket }}</p>
            <p class="text-sm text-slate-400">Cliente #{{ ticket.id_cliente }} · Usuario #{{ ticket.id_usuario }}</p>
            <p class="mt-1 text-sm text-slate-300">{{ ticket.descripcion }}</p>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const { user } = useAuth();

const activeTab = ref('clientes');
const search = ref('');
const editingKey = ref('');

const memberCards = computed(() => gymStore.members);
const users = computed(() => gymStore.users);
const plans = computed(() => gymStore.plans);
const memberships = computed(() => gymStore.memberships);
const tickets = computed(() => gymStore.tickets);

const tabs = [
  { key: 'clientes', label: 'Clientes' },
  { key: 'usuarios', label: 'Usuarios' },
  { key: 'planes', label: 'Planes' },
  { key: 'membresias', label: 'Membresías' },
  { key: 'tickets', label: 'Tickets' },
];

const clientForm = reactive({
  id_cliente: '',
  nombres: '',
  apellidos: '',
  dni: '',
  telefono: '',
  email: '',
  fecha_registro: new Date().toISOString().slice(0, 10),
  estado: true,
  assignMembership: true,
  id_pm: plans.value[0]?.id_pm || 1,
});

const userForm = reactive({
  id_usuario: '',
  dni: '',
  contrasena: '',
  rol: 'user',
  estado: true,
  email: '',
});

const planForm = reactive({
  id_pm: '',
  nombre_plan: '',
  duracion: '',
  precio: 0,
});

const ticketForm = reactive({
  id_ticket: '',
  id_cliente: memberCards.value[0]?.id_cliente || 0,
  id_usuario: users.value.find((item) => item.email === user.value?.email)?.id_usuario || users.value[0]?.id_usuario || 0,
  tipo_ticket: 'Consulta',
  descripcion: '',
  estado_ticket: 'Abierto',
});

const filteredMembers = computed(() => {
  const normalized = search.value.trim().toLowerCase();
  if (!normalized) {
    return memberCards.value;
  }

  return memberCards.value.filter((member) => [member.name, member.dni, member.email, member.internalCode, member.plan].join(' ').toLowerCase().includes(normalized));
});

const activeTitle = computed(() => tabs.find((tab) => tab.key === activeTab.value)?.label || 'Clientes');
const listTitle = computed(() => {
  if (activeTab.value === 'clientes') return 'Expedientes de clientes';
  if (activeTab.value === 'usuarios') return 'Cuentas del sistema';
  if (activeTab.value === 'planes') return 'Planes de membresía';
  if (activeTab.value === 'membresias') return 'Historial de membresías';
  return 'Tickets de atención';
});

const formTitle = computed(() => {
  if (activeTab.value === 'clientes') return editingKey.value ? 'Editar cliente' : 'Nuevo cliente';
  if (activeTab.value === 'usuarios') return editingKey.value ? 'Editar usuario' : 'Nuevo usuario';
  if (activeTab.value === 'planes') return editingKey.value ? 'Editar plan' : 'Nuevo plan';
  return 'Nuevo ticket';
});

const submitLabel = computed(() => {
  if (activeTab.value === 'clientes') return 'Guardar cliente';
  if (activeTab.value === 'usuarios') return 'Guardar usuario';
  if (activeTab.value === 'planes') return 'Guardar plan';
  return 'Crear ticket';
});

const resetForms = () => {
  editingKey.value = '';
  clientForm.id_cliente = '';
  clientForm.nombres = '';
  clientForm.apellidos = '';
  clientForm.dni = '';
  clientForm.telefono = '';
  clientForm.email = '';
  clientForm.fecha_registro = new Date().toISOString().slice(0, 10);
  clientForm.estado = true;
  clientForm.assignMembership = true;
  clientForm.id_pm = plans.value[0]?.id_pm || 1;
  userForm.id_usuario = '';
  userForm.dni = '';
  userForm.contrasena = '';
  userForm.rol = 'user';
  userForm.estado = true;
  userForm.email = '';
  planForm.id_pm = '';
  planForm.nombre_plan = '';
  planForm.duracion = '';
  planForm.precio = 0;
  ticketForm.descripcion = '';
};

const editMember = (member) => {
  activeTab.value = 'clientes';
  editingKey.value = member.id;
  clientForm.id_cliente = member.id_cliente;
  clientForm.nombres = member.name.split(' ')[0] || member.name;
  clientForm.apellidos = member.name.split(' ').slice(1).join(' ');
  clientForm.dni = member.dni;
  clientForm.telefono = member.phone;
  clientForm.email = member.email;
  clientForm.fecha_registro = member.joinedAt || new Date().toISOString().slice(0, 10);
  clientForm.estado = member.status !== 'Inactiva';
  clientForm.assignMembership = Boolean(member.planId);
  clientForm.id_pm = Number(String(member.planId || '').replace(/^pm-/, '')) || plans.value[0]?.id_pm || 1;
};

const deleteMember = async (id) => {
  await gymStore.deleteMember(id);
};

const deleteUsuario = async (idUsuario) => {
  await gymStore.deleteUsuario(idUsuario);
};

const handleSubmit = async () => {
  if (activeTab.value === 'clientes') {
    await gymStore.upsertMember({
      ...clientForm,
      planId: clientForm.assignMembership ? `pm-${clientForm.id_pm}` : '',
      fecha_inicio: clientForm.fecha_registro,
    });
    resetForms();
    return;
  }

  if (activeTab.value === 'usuarios') {
    await gymStore.upsertUsuario(userForm);
    resetForms();
    return;
  }

  if (activeTab.value === 'planes') {
    await gymStore.upsertPlan(planForm);
    resetForms();
    return;
  }

  if (activeTab.value === 'tickets') {
    await gymStore.upsertTicket(ticketForm);
    ticketForm.descripcion = '';
  }
};
</script>