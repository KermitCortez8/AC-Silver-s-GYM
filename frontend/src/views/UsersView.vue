<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Administracion</p>
          <h1 class="mt-2 text-3xl font-black text-white">Usuarios del sistema</h1>
          <p class="mt-2 text-slate-300">Gestiona accesos internos por rol, correo, telefono y DNI.</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ users.length }}</p>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300">
            <p class="text-slate-400">Con contrasena</p>
            <p class="text-xl font-black text-white">{{ usersWithPassword }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Lista</p>
          <h2 class="mt-2 text-2xl font-black text-white">Usuarios registrados</h2>
        </div>
        <div class="flex flex-col gap-3 sm:flex-row">
          <input v-model="search" class="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none" placeholder="Buscar por ID, correo, rol o DNI..." />
          <button class="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950" @click="openNewUser">
            Nuevo usuario
          </button>
        </div>
      </div>

      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <div class="mt-5 grid gap-4 xl:grid-cols-2">
        <article v-for="systemUser in filteredUsers" :key="systemUser.id_usuario" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-lg font-bold text-white">{{ systemUser.nombre || 'Sin nombre' }}</p>
                <span class="rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-cyan-100">{{ systemUser.id_usuario }}</span>
              </div>
              <p class="mt-2 text-sm text-slate-400">Correo: {{ systemUser.correo || 'Sin correo' }}</p>
              <p class="text-sm text-slate-400">DNI: {{ systemUser.dni || 'Sin DNI' }}</p>
              <p class="text-sm text-slate-400">Telefono: {{ systemUser.telefono || 'Sin telefono' }}</p>
              <p class="mt-2 text-sm text-slate-300">Rol: {{ systemUser.rol }}</p>
              <p class="mt-1 text-sm text-slate-400">Acceso: {{ systemUser.hasPassword ? 'Con contrasena' : 'Sin contrasena' }}</p>
            </div>

            <div class="flex shrink-0 gap-2">
              <button class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="editUser(systemUser)">
                Editar
              </button>
              <button class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 hover:bg-rose-400/10" @click="confirmDelete(systemUser)">
                Eliminar
              </button>
            </div>
          </div>
        </article>
      </div>

      <p v-if="!filteredUsers.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
        No hay usuarios para mostrar.
      </p>
    </section>

    <Teleport to="body">
      <div v-if="isEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <form class="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl" @submit.prevent="handleSubmit">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Usuario</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar usuario' : 'Nuevo usuario' }}</h2>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeEditor">
              Cerrar
            </button>
          </div>

          <div class="mt-6 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Nombre</span>
              <input v-model="form.nombre" class="field-input" placeholder="Renato Cortez" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Correo</span>
              <input v-model="form.correo" type="email" class="field-input" placeholder="usuario@correo.com" />
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
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Rol</span>
              <select v-model="form.rol" class="field-input">
                <option value="admin">admin</option>
                <option value="trainer">trainer</option>
                <option value="staff">staff</option>
              </select>
            </label>
          </div>

          <button type="submit" class="mt-6 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
            {{ editingId ? 'Guardar cambios' : 'Registrar usuario' }}
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
const users = computed(() => gymStore.users);
const search = ref('');
const editingId = ref('');
const isEditorOpen = ref(false);
const feedbackMessage = ref('');
const feedbackTone = ref('info');

const form = reactive({
  nombre: '',
  correo: '',
  telefono: '',
  dni: '',
  password: '',
  rol: 'staff',
});

const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return users.value;
  return users.value.filter((systemUser) =>
    [systemUser.id_usuario, systemUser.nombre, systemUser.correo, systemUser.telefono, systemUser.dni, systemUser.rol, systemUser.hasPassword ? 'con contrasena' : 'sin contrasena']
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
});

const usersWithPassword = computed(() => users.value.filter((systemUser) => systemUser.hasPassword).length);
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
  form.rol = 'staff';
};

const openNewUser = () => {
  resetForm();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

const editUser = (systemUser) => {
  editingId.value = systemUser.id_usuario;
  form.nombre = systemUser.nombre || '';
  form.correo = systemUser.correo || systemUser.email || '';
  form.telefono = systemUser.telefono || '';
  form.dni = systemUser.dni || '';
  form.password = '';
  form.rol = systemUser.rol || 'staff';
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

const confirmDelete = async (systemUser) => {
  if (!window.confirm(`Eliminar al usuario ${systemUser.id_usuario}?`)) return;
  try {
    await gymStore.deleteUser(systemUser.id_usuario);
    feedbackTone.value = 'success';
    feedbackMessage.value = `Usuario ${systemUser.id_usuario} eliminado.`;
    if (editingId.value === systemUser.id_usuario) closeEditor();
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
      password: form.password,
      rol: form.rol,
    });

    closeEditor();
    feedbackTone.value = 'success';
    feedbackMessage.value = `Usuario ${saved.id_usuario} guardado.`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el usuario.';
  }
};

onMounted(() => {
  gymStore.fetchFromBackend?.().catch((error) => console.warn('No se pudo refrescar usuarios:', error));
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
