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

      <div class="mt-5 overflow-x-auto">
        <table class="w-full min-w-[960px] text-left text-sm">
          <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <th class="px-5 py-4 font-bold">ID</th>
              <th class="px-5 py-4 font-bold">Usuario</th>
              <th class="px-5 py-4 font-bold">Rol</th>
              <th class="px-5 py-4 font-bold">Correo electronico</th>
              <th class="px-5 py-4 font-bold">DNI</th>
              <th class="px-5 py-4 font-bold">Telefono</th>
              <th class="px-5 py-4 font-bold">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="systemUser in filteredUsers" :key="systemUser.id_usuario" class="transition hover:bg-white/[0.04]">
              <td class="px-5 py-4 align-top">
                <span class="rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-cyan-100">{{ systemUser.id_usuario }}</span>
              </td>
              <td class="px-5 py-4 align-top font-bold text-white">{{ systemUser.nombre || 'Sin nombre' }}</td>
              <td class="px-5 py-4 align-top text-slate-300">{{ systemUser.rol }}</td>
              <td class="px-5 py-4 align-top text-slate-400">{{ systemUser.correo || 'Sin correo' }}</td>
              <td class="px-5 py-4 align-top text-slate-400">{{ systemUser.dni || 'Sin DNI' }}</td>
              <td class="px-5 py-4 align-top text-slate-400">{{ systemUser.telefono || 'Sin telefono' }}</td>
              <td class="px-5 py-4 align-top">
                <div class="flex shrink-0 gap-2">
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-white/10 text-white hover:bg-white/5"
                    title="Ver detalles"
                    @click="openDetails(systemUser)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
                      <circle cx="12" cy="12" r="9" />
                      <line x1="12" y1="11" x2="12" y2="16" />
                      <circle cx="12" cy="7.5" r="0.75" fill="currentColor" stroke="none" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-white/10 text-white hover:bg-white/5"
                    title="Editar"
                    @click="editUser(systemUser)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
                      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-rose-400/30 text-rose-100 hover:bg-rose-400/10"
                    title="Eliminar"
                    @click="confirmDelete(systemUser)"
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

    <Teleport to="body">
      <div v-if="isDetailsOpen && viewingUser" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <div class="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Detalles</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ viewingUser.nombre || 'Sin nombre' }}</h2>
              <span class="mt-2 inline-block rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-cyan-100">{{ viewingUser.id_usuario }}</span>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeDetails">
              Cerrar
            </button>
          </div>

          <div class="mt-6 space-y-2">
            <p class="text-sm text-slate-400">Correo: <span class="text-slate-200">{{ viewingUser.correo || 'Sin correo' }}</span></p>
            <p class="text-sm text-slate-400">DNI: <span class="text-slate-200">{{ viewingUser.dni || 'Sin DNI' }}</span></p>
            <p class="text-sm text-slate-400">Telefono: <span class="text-slate-200">{{ viewingUser.telefono || 'Sin telefono' }}</span></p>
            <p class="text-sm text-slate-300">Rol: <span class="text-slate-200">{{ viewingUser.rol }}</span></p>
            <p class="text-sm text-slate-400">Acceso: <span class="text-slate-200">{{ viewingUser.hasPassword ? 'Con contrasena' : 'Sin contrasena' }}</span></p>
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
const users = computed(() => gymStore.users);
const search = ref('');
const editingId = ref('');
const isEditorOpen = ref(false);
const isDetailsOpen = ref(false);
const viewingUser = ref(null);
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

const openDetails = (systemUser) => {
  viewingUser.value = systemUser;
  isDetailsOpen.value = true;
};

const closeDetails = () => {
  isDetailsOpen.value = false;
  viewingUser.value = null;
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
