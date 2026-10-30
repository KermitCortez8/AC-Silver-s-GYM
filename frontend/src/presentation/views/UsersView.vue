<template>
  <div class="workspace-view space-y-6">
    <header class="ws-panel ws-hero ws-toolbar">
      <div>
        <p class="ws-eyebrow">Administración · Equipo</p>
        <h1 class="ws-title">Usuarios del sistema</h1>
        <p class="ws-description">
          Gestiona los accesos de tu equipo y encuentra a cada persona por
          nombre, correo o DNI.
        </p>
      </div>
      <button type="button" class="ws-btn ws-primary" @click="openNewUser">
        <Plus :size="18" /> Nuevo usuario
      </button>
    </header>

    <section class="grid gap-4 sm:grid-cols-3" aria-label="Resumen de usuarios">
      <article class="ws-metric">
        <p class="ws-muted text-sm">Usuarios registrados</p>
        <p class="ws-metric-value">{{ users.length }}</p>
        <p class="ws-muted text-xs">Miembros del equipo</p>
      </article>
      <article class="ws-metric">
        <p class="ws-muted text-sm">Con contraseña</p>
        <p class="ws-metric-value ws-success">{{ usersWithPassword }}</p>
        <p class="ws-muted text-xs">Credencial configurada</p>
      </article>
      <article class="ws-metric">
        <p class="ws-muted text-sm">Sin contraseña</p>
        <p class="ws-metric-value ws-warning">
          {{ users.length - usersWithPassword }}
        </p>
        <p class="ws-muted text-xs">Revisa su método de acceso</p>
      </article>
    </section>

    <p
      v-if="feedbackMessage && !isEditorOpen"
      role="status"
      class="ws-notice"
      :class="feedbackToneClass"
    >
      {{ feedbackMessage }}
    </p>
    <section class="ws-panel space-y-5" :aria-busy="isLoading">
      <div class="ws-toolbar">
        <div>
          <h2 class="ws-heading">Tu equipo</h2>
          <p class="ws-muted text-sm mt-1" role="status">
            {{ filteredUsers.length }} de {{ users.length }} usuarios
          </p>
        </div>
        <label class="ws-search max-w-md"
          ><span class="sr-only">Buscar usuarios</span
          ><Search :size="18" /><SearchInput
            v-model="search"
            class="ws-input"
            placeholder="Nombre, correo, DNI, teléfono o ID"
        /></label>
      </div>
      <div
        class="flex flex-wrap gap-2"
        role="group"
        aria-label="Filtrar por rol"
      >
        <button
          v-for="role in roleFilters"
          :key="role.value"
          type="button"
          class="ws-chip"
          :aria-pressed="roleFilter === role.value"
          @click="roleFilter = role.value"
        >
          {{ role.label }}
          <span class="opacity-70">{{
            role.value
              ? users.filter((u) => u.rol === role.value).length
              : users.length
          }}</span>
        </button>
        <button
          v-if="search || roleFilter"
          type="button"
          class="ws-btn"
          @click="
            search = '';
            roleFilter = '';
          "
        >
          Limpiar filtros
        </button>
      </div>
      <p
        v-if="isLoading && !users.length"
        role="status"
        class="ws-notice ws-tint-info ws-info"
      >
        <LoaderCircle :size="18" class="ws-spin" /> Cargando usuarios…
      </p>
      <template v-else-if="filteredUsers.length">
        <div class="ws-table-wrap ws-desktop-table">
          <table class="ws-table">
            <caption class="sr-only">
              Usuarios registrados y acciones de administración
            </caption>
            <thead>
              <tr>
                <th scope="col">Usuario</th>
                <th scope="col">Rol</th>
                <th scope="col">Contacto</th>
                <th scope="col">DNI</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="systemUser in filteredUsers"
                :key="systemUser.id_usuario"
              >
                <td>
                  <div class="flex items-center gap-3">
                    <span class="ws-avatar" aria-hidden="true">{{
                      initials(systemUser.nombre)
                    }}</span>
                    <div>
                      <p class="font-bold">
                        {{ systemUser.nombre || 'Sin nombre' }}
                      </p>
                      <p class="ws-muted text-xs mt-1">
                        ID {{ systemUser.id_usuario }}
                      </p>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="ws-badge ws-info ws-tint-info">{{
                    roleLabel(systemUser.rol)
                  }}</span>
                </td>
                <td>
                  <p class="ws-soft break-all">
                    {{ systemUser.correo || 'Sin correo' }}
                  </p>
                  <p class="ws-muted text-xs mt-1">
                    {{ systemUser.telefono || 'Sin teléfono' }}
                  </p>
                </td>
                <td class="ws-soft whitespace-nowrap">
                  {{ systemUser.dni || 'Sin DNI' }}
                </td>
                <td>
                  <div class="ws-actions flex-nowrap">
                    <button
                      class="ws-btn"
                      :aria-label="`Ver detalles de ${systemUser.nombre || systemUser.id_usuario}`"
                      @click="openDetails(systemUser)"
                    >
                      <Eye :size="16" /><span class="sr-only"
                        >Ver detalles</span
                      >
                    </button>
                    <button
                      class="ws-btn"
                      :aria-label="`Editar a ${systemUser.nombre || systemUser.id_usuario}`"
                      @click="editUser(systemUser)"
                    >
                      <Pencil :size="16" /><span>Editar</span>
                    </button>
                    <button
                      class="ws-btn ws-danger ws-hover-danger"
                      :aria-label="`Eliminar a ${systemUser.nombre || systemUser.id_usuario}`"
                      @click="confirmDelete(systemUser)"
                    >
                      <Trash2 :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="ws-mobile-list">
          <article
            v-for="systemUser in filteredUsers"
            :key="systemUser.id_usuario"
            class="ws-mobile-card"
          >
            <div class="flex items-center gap-3">
              <span class="ws-avatar" aria-hidden="true">{{
                initials(systemUser.nombre)
              }}</span>
              <div class="min-w-0">
                <h3 class="font-bold break-words">
                  {{ systemUser.nombre || 'Sin nombre' }}
                </h3>
                <span class="ws-badge ws-tint-info ws-info mt-1">{{
                  roleLabel(systemUser.rol)
                }}</span>
              </div>
            </div>
            <p class="ws-soft text-sm break-all mt-4">
              {{ systemUser.correo || 'Sin correo' }}
            </p>
            <p class="ws-muted text-xs mt-1">
              DNI: {{ systemUser.dni || 'Sin DNI' }} ·
              {{ systemUser.telefono || 'Sin teléfono' }}
            </p>
            <div class="ws-actions mt-4">
              <button class="ws-btn" @click="openDetails(systemUser)">
                <Eye :size="16" /> Detalles</button
              ><button class="ws-btn" @click="editUser(systemUser)">
                <Pencil :size="16" /> Editar</button
              ><button
                class="ws-btn ws-danger"
                :aria-label="`Eliminar a ${systemUser.nombre || systemUser.id_usuario}`"
                @click="confirmDelete(systemUser)"
              >
                <Trash2 :size="16" />
              </button>
            </div>
          </article>
        </div>
      </template>
      <div v-else class="ws-empty">
        <UsersRound :size="32" />
        <h3>
          {{
            users.length
              ? 'No encontramos coincidencias'
              : 'Tu equipo empieza aquí'
          }}
        </h3>
        <p>
          {{
            users.length
              ? 'Prueba con otro nombre o cambia el filtro de rol.'
              : 'Crea un usuario para darle acceso al equipo.'
          }}
        </p>
        <button
          v-if="search || roleFilter"
          class="ws-btn mt-4"
          @click="
            search = '';
            roleFilter = '';
          "
        >
          Limpiar filtros</button
        ><button v-else class="ws-btn ws-primary mt-4" @click="openNewUser">
          Crear usuario
        </button>
      </div>
    </section>

    <WorkspaceDialog
      :open="isEditorOpen"
      :title="editingId ? 'Editar usuario' : 'Nuevo usuario'"
      :busy="isSaving"
      @close="closeEditor"
    >
      <form novalidate @submit.prevent="handleSubmit">
        <p class="ws-muted text-sm mb-5">
          Define los datos y el rol de acceso de esta persona.
        </p>
        <p
          v-if="feedbackMessage && feedbackTone === 'error'"
          role="alert"
          class="ws-notice ws-tint-danger ws-danger mb-4"
        >
          {{ feedbackMessage }}
        </p>
        <fieldset :disabled="isSaving" class="grid gap-4 sm:grid-cols-2">
          <label class="sm:col-span-2"
            ><span class="ws-field-label">Nombre</span
            ><input
              v-model="form.nombre"
              :aria-invalid="Boolean(fieldErrors.nombre)"
              :aria-describedby="fieldErrors.nombre ? 'user-nombre-error' : undefined"
              @blur="validateField('nombre')" @input="revalidateField('nombre')"
              class="ws-input"
              autocomplete="name"
              required
              placeholder="Nombre y apellidos"
          />
            <FieldError id="user-nombre-error" :message="fieldErrors.nombre" /></label>
          <label class="sm:col-span-2"
            ><span class="ws-field-label">Correo electrónico</span
            ><input
              v-model="form.correo"
              :aria-invalid="Boolean(fieldErrors.correo)"
              :aria-describedby="fieldErrors.correo ? 'user-correo-error' : undefined"
              @blur="validateField('correo')" @input="revalidateField('correo')"
              class="ws-input"
              type="email"
              autocomplete="email"
              required
              placeholder="nombre@gmail.com"
          />
            <FieldError id="user-correo-error" :message="fieldErrors.correo" /></label>
          <label class="sm:col-span-2"
            ><span class="ws-field-label"
              >Contraseña {{ editingId ? '(opcional)' : '' }}</span
            ><input
              v-model="form.password"
              :aria-invalid="Boolean(fieldErrors.password)"
              :aria-describedby="fieldErrors.password ? 'user-password-error' : undefined"
              @blur="validateField('password')" @input="revalidateField('password')"
              class="ws-input"
              type="password"
              autocomplete="new-password"
              minlength="6"
              :required="!editingId"
              :placeholder="
                editingId
                  ? 'Dejar vacía para conservar la actual'
                  : 'Mínimo 6 caracteres'
              "
          />
            <FieldError id="user-password-error" :message="fieldErrors.password" /></label>
          <label
            ><span class="ws-field-label">Teléfono</span
            ><input
              v-model="form.telefono"
              :aria-invalid="Boolean(fieldErrors.telefono)"
              :aria-describedby="fieldErrors.telefono ? 'user-telefono-error' : undefined"
              @blur="validateField('telefono')" @input="revalidateField('telefono')"
              class="ws-input"
              type="tel"
              autocomplete="tel"
              placeholder="999111222"
          />
            <FieldError id="user-telefono-error" :message="fieldErrors.telefono" /></label>
          <label
            ><span class="ws-field-label">DNI</span
            ><input
              v-model="form.dni"
              :aria-invalid="Boolean(fieldErrors.dni)"
              :aria-describedby="fieldErrors.dni ? 'user-dni-error' : undefined"
              @blur="validateField('dni')" @input="revalidateField('dni')"
              class="ws-input"
              inputmode="numeric"
              maxlength="8"
              placeholder="12345678"
          />
            <FieldError id="user-dni-error" :message="fieldErrors.dni" /></label>
          <label class="sm:col-span-2"
            ><span class="ws-field-label">Rol</span
            ><select v-model="form.rol" class="ws-input">
              <option value="admin">Administrador</option>
              <option value="trainer">Entrenador</option>
              <option value="staff">Personal</option>
            </select></label
          >
        </fieldset>
        <div class="ws-actions mt-6 justify-end">
          <button
            type="button"
            class="ws-btn"
            :disabled="isSaving"
            @click="closeEditor"
          >
            Cancelar</button
          ><button type="submit" class="ws-btn ws-primary" :disabled="isSaving">
            <LoaderCircle v-if="isSaving" :size="16" class="ws-spin" />{{
              isSaving
                ? 'Guardando…'
                : editingId
                  ? 'Guardar cambios'
                  : 'Crear usuario'
            }}
          </button>
        </div>
      </form>
    </WorkspaceDialog>
    <WorkspaceDialog
      :open="isDetailsOpen"
      title="Detalles del usuario"
      @close="closeDetails"
    >
      <template v-if="viewingUser">
        <div class="flex items-center gap-3 mb-5">
          <span class="ws-avatar">{{ initials(viewingUser.nombre) }}</span>
          <div>
            <h3 class="font-bold text-lg">
              {{ viewingUser.nombre || 'Sin nombre' }}
            </h3>
            <p class="ws-muted text-sm">ID {{ viewingUser.id_usuario }}</p>
          </div>
        </div>
        <dl class="grid gap-4 sm:grid-cols-2">
          <div
            v-for="(value, label) in {
              Correo: viewingUser.correo || 'Sin correo',
              Teléfono: viewingUser.telefono || 'Sin teléfono',
              DNI: viewingUser.dni || 'Sin DNI',
              Rol: roleLabel(viewingUser.rol),
              Acceso: viewingUser.hasPassword
                ? 'Con contraseña'
                : 'Sin contraseña',
            }"
            :key="label"
          >
            <dt class="ws-muted text-xs">{{ label }}</dt>
            <dd class="ws-soft mt-1 break-all">{{ value }}</dd>
          </div>
        </dl>
      </template>
    </WorkspaceDialog>
  </div>
</template>
<script setup>
import FieldError from '../components/FieldError.vue';
import SearchInput from '../components/SearchInput.vue';
import { Eye, LoaderCircle, Pencil, Plus, Search, Trash2, UsersRound } from 'lucide-vue-next';
import WorkspaceDialog from '../components/WorkspaceDialog.vue';
import { initials } from '../utils/attendance';
import { useUserDirectory } from '../composables/users/useUserDirectory.js';

const {
  gymStore, users, search, roleFilter, isSaving,
  isLoading, roleFilters, roleLabel, editingId, isEditorOpen,
  isDetailsOpen, viewingUser, feedbackMessage, feedbackTone, form,
  fieldErrors, validateField, revalidateField, validateForm, resetValidation,
  filteredUsers, usersWithPassword, feedbackToneClass, resetForm, openNewUser,
  closeEditor, editUser, openDetails, closeDetails, confirmDelete,
  handleSubmit,
} = useUserDirectory();
</script>
