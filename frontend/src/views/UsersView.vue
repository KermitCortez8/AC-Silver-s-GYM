<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Administración</p>
          <h1 class="mt-2 text-3xl font-black text-white">Usuarios del sistema</h1>
          <p class="mt-2 text-slate-300">Administra los accesos del backend con ID automático por rol, correo, teléfono y DNI.</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ users.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Registrados</p>
            <p class="text-xl font-black text-white">{{ activeUsers }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Formulario</p>
            <h2 class="text-2xl font-black text-white">{{ editingId ? 'Editar usuario' : 'Nuevo usuario' }}</h2>
          </div>
          <button v-if="editingId" type="button" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm" @click="resetForm">
            Cancelar
          </button>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nombre</span>
            <input v-model="form.nombre" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="Renato Cortez" />
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="form.correo" type="email" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="usuario@correo.com" />
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Teléfono</span>
            <input v-model="form.telefono" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="999 111 222" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Rol</span>
            <div class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white">{{ form.rol }}</div>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">DNI</span>
            <input v-model="form.dni" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500" placeholder="12345678" />
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar usuario' : 'Registrar usuario' }}
        </button>

        <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
          {{ feedbackMessage }}
        </p>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Lista</p>
            <h2 class="text-2xl font-black text-white">Usuarios registrados</h2>
          </div>
          <input v-model="search" class="rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-sm text-white outline-none" placeholder="Buscar por ID, correo o promoción..." />
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="user in filteredUsers" :key="user.id_usuario" class="rounded-3xl border border-white/10 bg-slate-900/80 p-5">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-bold text-white">{{ user.nombre || 'Sin nombre' }}</p>
                <p class="text-sm text-slate-400">ID: {{ user.id_usuario }}</p>
                <p class="text-sm text-slate-400">Nombre: {{ user.nombre || 'Sin nombre' }}</p>
                <p class="text-sm text-slate-400">Correo: {{ user.correo || 'Sin correo' }}</p>
                <p class="text-sm text-slate-400">Teléfono: {{ user.telefono || 'Sin teléfono' }}</p>
                <p class="text-sm text-slate-400">DNI: {{ user.dni || 'Sin DNI' }}</p>
                <p class="mt-2 text-sm text-slate-300">Rol: {{ user.rol }}</p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editUser(user)">
                  Editar
                </button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="confirmDelete(user)">
                  Eliminar
                </button>
              </div>
            </div>
          </article>
        </div>

        <p v-if="!filteredUsers.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
          No hay usuarios para mostrar.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const users = computed(() => gymStore.users);
const search = ref('');
const editingId = ref('');
const feedbackMessage = ref('');
const feedbackTone = ref('info');

const form = reactive({
  nombre: '',
  correo: '',
  telefono: '',
  dni: '',
  rol: 'staff',
});

const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) {
    return users.value;
  }

    return users.value.filter((user) =>
      [user.id_usuario, user.nombre, user.correo, user.telefono, user.dni, user.rol]
        .join(' ')
        .toLowerCase()
        .includes(query),
    );
});

    const activeUsers = computed(() => users.value.length);
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
  form.rol = 'staff';
};

const editUser = (user) => {
  editingId.value = user.id_usuario;
  form.nombre = user.nombre || '';
  form.correo = user.correo || user.email || '';
  form.telefono = user.telefono || '';
  form.dni = user.dni || '';
  form.rol = user.rol || 'staff';
};

const confirmDelete = async (user) => {
  const confirmed = window.confirm(`Eliminar al usuario ${user.id_usuario}?`);
  if (!confirmed) {
    return;
  }

  try {
    await gymStore.deleteUser(user.id_usuario);
    feedbackTone.value = 'success';
    feedbackMessage.value = `Usuario ${user.id_usuario} eliminado.`;
    if (editingId.value === user.id_usuario) {
      resetForm();
    }
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el usuario.';
  }
};

const handleSubmit = async () => {
  try {
    const saved = await gymStore.upsertUser({
      id_usuario: editingId.value || undefined,
      nombre: form.nombre,
      correo: form.correo,
      telefono: form.telefono,
      dni: form.dni,
      rol: form.rol,
    });

    resetForm();
    feedbackTone.value = 'success';
    feedbackMessage.value = `Usuario ${saved.id_usuario} guardado con estado Activo.`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el usuario.';
    console.error('Error al guardar usuario:', error);
  }
};

onMounted(() => {
  if (gymStore.fetchFromBackend) {
    gymStore.fetchFromBackend().catch((error) => console.warn('No se pudo refrescar usuarios:', error));
  }
});
</script>
