<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Administración</p>
          <h1 class="mt-2 text-3xl font-black text-white">Usuarios</h1>
          <p class="mt-2 text-slate-300">Gestiona miembros, roles y estado de membresía.</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ members.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Activos</p>
            <p class="text-xl font-black text-white">{{ activeMembers }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Admins</p>
            <p class="text-xl font-black text-white">{{ adminMembers }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Formulario</p>
            <h2 class="text-2xl font-black text-white">{{ editingId ? 'Editar miembro' : 'Nuevo miembro' }}</h2>
          </div>
          <button v-if="editingId" type="button" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm" @click="resetForm">
            Cancelar
          </button>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="form.name" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="Nombre completo" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="form.email" type="email" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="correo@ejemplo.com" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Teléfono</span>
            <input v-model="form.phone" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="999 888 777" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Plan</span>
            <select v-model="form.plan" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Mensual</option>
              <option>Trimestral</option>
              <option>Anual</option>
              <option>Acceso total</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Rol</span>
            <select v-model="form.role" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="user">Miembro</option>
              <option value="admin">Administrador</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="form.status" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Activa</option>
              <option>Pendiente</option>
              <option>Bloqueada</option>
            </select>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar cambios' : 'Agregar miembro' }}
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Lista</p>
            <h2 class="text-2xl font-black text-white">Miembros registrados</h2>
          </div>
          <input v-model="search" class="rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-white outline-none" placeholder="Buscar miembro..." />
        </div>

        <div class="mt-5 space-y-3">
          <article
            v-for="member in filteredMembers"
            :key="member.id"
            class="rounded-3xl border border-white/10 bg-slate-900/80 p-5"
          >
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-bold text-white">{{ member.name }}</p>
                <p class="text-sm text-slate-400">{{ member.email }} · {{ member.phone }}</p>
                <p class="mt-2 text-sm text-slate-300">Plan: {{ member.plan }} · Estado: {{ member.status }} · Rol: {{ member.role }}</p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editMember(member)">
                  Editar
                </button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteMember(member.id)">
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
const members = computed(() => gymStore.members);
const search = ref('');
const editingId = ref('');

const form = reactive({
  name: '',
  email: '',
  phone: '',
  plan: 'Mensual',
  role: 'user',
  status: 'Activa',
});

const filteredMembers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return members.value;

  return members.value.filter((member) =>
    [member.name, member.email, member.phone, member.plan, member.status, member.role]
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
});

const activeMembers = computed(() => members.value.filter((member) => member.status === 'Activa').length);
const adminMembers = computed(() => members.value.filter((member) => member.role === 'admin').length);

const resetForm = () => {
  editingId.value = '';
  form.name = '';
  form.email = '';
  form.phone = '';
  form.plan = 'Mensual';
  form.role = 'user';
  form.status = 'Activa';
};

const editMember = (member) => {
  editingId.value = member.id;
  form.name = member.name;
  form.email = member.email;
  form.phone = member.phone;
  form.plan = member.plan;
  form.role = member.role;
  form.status = member.status;
};

const handleSubmit = () => {
  gymStore.upsertMember({ id: editingId.value || undefined, ...form });
  resetForm();
};
</script>
