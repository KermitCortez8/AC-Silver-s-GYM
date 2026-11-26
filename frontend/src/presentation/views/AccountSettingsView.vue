<template>
  <div v-if="auth.user" class="account-settings">
    <header class="account-heading">
      <h1>Configuración</h1>
      <p>Revisa tus datos y personaliza la apariencia del panel.</p>
    </header>

    <div class="account-layout">
      <section class="account-card account-summary" aria-labelledby="account-summary-title">
        <div class="account-card-header">
          <h2 id="account-summary-title">Mis datos</h2>
          <button type="button" class="account-button account-edit" @click="openEditor">
            <Pencil :size="16" aria-hidden="true" /> Editar datos
          </button>
        </div>
        <div class="account-identity">
          <div class="account-avatar" aria-hidden="true">{{ initials }}</div>
          <div>
            <p class="account-name">{{ auth.user.name }}</p>
            <p class="account-role">{{ roleLabels[auth.user.role] }}</p>
          </div>
        </div>
        <dl class="account-details">
          <div v-for="detail in accountDetails" :key="detail.label" :class="{ 'account-email': detail.wide }">
            <dt>{{ detail.label }}</dt>
            <dd v-if="detail.masked">
              <span class="account-password-mask" aria-hidden="true">••••••••</span>
              <span class="sr-only">Contraseña oculta</span>
            </dd>
            <dd v-else>{{ detail.value }}</dd>
          </div>
        </dl>
      </section>

      <div class="account-controls">
        <section v-if="membership" class="account-card" aria-labelledby="account-membership-title">
          <h2 id="account-membership-title">Membresía vigente</h2>
          <dl class="account-details account-membership">
            <div v-for="detail in membershipDetails" :key="detail.label">
              <dt>{{ detail.label }}</dt><dd>{{ detail.value }}</dd>
            </div>
          </dl>
        </section>

        <section class="account-card" aria-labelledby="account-appearance-title">
          <h2 id="account-appearance-title">Apariencia</h2>
          <p class="account-hint">El tema se guarda en este navegador.</p>
          <fieldset class="account-themes" aria-labelledby="account-appearance-title">
            <label v-for="option in themeOptions" :key="option.value">
              <input type="radio" name="account-theme" :value="option.value" :checked="theme === option.value"
                @change="setTheme(option.value)" />
              <component :is="option.icon" :size="18" aria-hidden="true" />
              {{ option.label }}
            </label>
          </fieldset>
        </section>
      </div>
    </div>
    <dialog ref="editor" class="account-dialog" aria-labelledby="account-editor-title"
      @cancel.prevent="closeEditor" @close="finishEdit">
      <form v-if="editing" class="account-card account-editor" novalidate :aria-busy="saving" @submit.prevent="save">
        <div class="account-card-header">
          <h2 id="account-editor-title">Editar datos</h2>
          <button class="account-icon" type="button" aria-label="Cerrar edición" :disabled="saving" @click="closeEditor">
            <X :size="20" aria-hidden="true" />
          </button>
        </div>
        <div class="account-editor-body">
          <fieldset class="account-fields" :disabled="saving" aria-label="Datos editables">
            <div>
              <label for="account-name">Nombre completo</label>
              <input id="account-name" v-model="draft.nombre" class="field-input"
                autocomplete="name" autofocus required :maxlength="FORM_LIMITS.shortText"
                :aria-invalid="Boolean(errors.nombre)" :aria-describedby="errors.nombre ? 'account-name-error' : undefined" />
              <p v-if="errors.nombre" id="account-name-error" class="account-field-error" role="alert">{{ errors.nombre }}</p>
            </div>
            <div>
              <label for="account-email">Correo electrónico</label>
              <input id="account-email" v-model="draft.correo" class="field-input" type="email"
                autocomplete="username" required :maxlength="FORM_LIMITS.shortText"
                :aria-invalid="Boolean(errors.correo)" :aria-describedby="errors.correo ? 'account-email-error' : undefined" />
              <p v-if="errors.correo" id="account-email-error" class="account-field-error" role="alert">{{ errors.correo }}</p>
            </div>
            <div>
              <label for="account-phone">Teléfono <span class="account-hint">(opcional)</span></label>
              <input id="account-phone" v-model="draft.telefono" class="field-input" type="tel" inputmode="numeric"
                autocomplete="tel-national" :maxlength="FORM_LIMITS.phone" placeholder="987654321"
                :aria-invalid="Boolean(errors.telefono)" :aria-describedby="errors.telefono ? 'account-phone-error' : 'account-phone-hint'" />
              <p v-if="errors.telefono" id="account-phone-error" class="account-field-error" role="alert">{{ errors.telefono }}</p>
              <p v-else id="account-phone-hint" class="account-hint">Ingresa 9 dígitos.</p>
            </div>
            <div>
              <label for="account-dni">DNI <span v-if="!auth.user.id_cliente" class="account-hint">(opcional)</span></label>
              <input id="account-dni" v-model="draft.dni" class="field-input" inputmode="numeric"
                :required="Boolean(auth.user.id_cliente)" :maxlength="FORM_LIMITS.dni"
                :aria-invalid="Boolean(errors.dni)" :aria-describedby="errors.dni ? 'account-dni-error' : 'account-dni-hint'" />
              <p v-if="errors.dni" id="account-dni-error" class="account-field-error" role="alert">{{ errors.dni }}</p>
              <p v-else id="account-dni-hint" class="account-hint">Ingresa 8 dígitos.</p>
            </div>
          </fieldset>
          <fieldset class="account-password-fields account-fields" :disabled="saving" aria-label="Contraseña nueva">
            <div>
              <label for="account-password">Contraseña nueva <span class="account-hint">(opcional)</span></label>
              <input id="account-password" v-model="draft.password_nueva" class="field-input" type="password"
                autocomplete="new-password" maxlength="256" @input="errors.password_nueva = ''"
                :aria-invalid="Boolean(errors.password_nueva)" :aria-describedby="errors.password_nueva ? 'account-password-error' : 'account-password-hint'" />
              <p v-if="errors.password_nueva" id="account-password-error" class="account-field-error" role="alert">{{ errors.password_nueva }}</p>
              <p v-else id="account-password-hint" class="account-hint">Mínimo 6 caracteres.</p>
            </div>
          </fieldset>
        </div>
        <div class="account-actions">
          <button type="button" class="account-button" :disabled="saving" @click="closeEditor">Cancelar</button>
          <button type="submit" class="account-button account-primary" :disabled="!hasChanges || saving">
            {{ saving ? 'Guardando…' : 'Guardar cambios' }}
          </button>
        </div>
        <FloatingNotice in-dialog top-on-mobile :message="requestError" tone="error" @dismiss="requestError = ''" />
      </form>
    </dialog>
    <FloatingNotice top-on-mobile :message="notice" tone="success" @dismiss="notice = ''" />
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue';
import { Moon, Pencil, Sun, X } from 'lucide-vue-next';
import { useAuthStore } from '../../application/stores/authStore.js';
import { FORM_LIMITS } from '../../domain/utils/formLimits.js';
import { dniError, emailError, passwordError, phoneError, requiredTextError } from '../../domain/utils/formValidation.js';
import FloatingNotice from '../components/FloatingNotice.vue';
import { useTheme } from '../composables/useTheme.js';

const auth = useAuthStore();
const { theme, setTheme } = useTheme();
const roleLabels = { user: 'Cliente', admin: 'Administrador', trainer: 'Entrenador', staff: 'Personal' };
const themeOptions = [
  { value: 'light', icon: Sun, label: 'Claro' },
  { value: 'dark', icon: Moon, label: 'Oscuro' },
];
const initials = computed(() => (auth.user?.name || '').trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase());
const membership = computed(() => auth.user?.membresia);
const dateFormat = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeZone: 'UTC' });
const formatDate = (value) => {
  const date = new Date(`${value?.slice(0, 10)}T12:00:00Z`);
  return Number.isNaN(date.getTime()) ? 'Sin registrar' : dateFormat.format(date);
};
const accountDetails = computed(() => {
  const user = auth.user;
  if (!user) return [];

  return [
    { label: 'Correo de acceso', value: user.email, wide: true },
    { label: 'Teléfono', value: user.telefono || 'Sin registrar' },
    { label: 'DNI', value: user.dni || 'Sin registrar' },
    { label: 'Código de cuenta', value: user.id_usuario },
    { label: 'Estado de la cuenta', value: user.estado === 'ACTIVO' ? 'Activa' : user.estado },
    { label: 'Fecha de registro', value: user.id_cliente ? formatDate(user.fecha_registro) : '' },
    { label: 'Acceso con Google', value: typeof user.google_vinculado === 'boolean' ? (user.google_vinculado ? 'Vinculado' : 'Sin vincular') : '' },
    { label: 'Contraseña', masked: user.tiene_contrasena, value: user.tiene_contrasena === false ? 'Sin configurar' : '' },
  ].filter((detail) => detail.value || detail.masked);
});
const membershipDetails = computed(() => {
  const record = membership.value;
  if (!record) return [];

  return [
    { label: 'Plan', value: record.plan || 'Sin registrar' },
    { label: 'Estado del pago', value: record.estado_pago === 'PAGADO' ? 'Pagado' : record.estado_pago },
    { label: 'Inicio', value: formatDate(record.fecha_inicio) },
    { label: 'Vencimiento', value: formatDate(record.fecha_fin) },
  ];
});
const editor = ref(null);
const editing = ref(false);
const profileFields = ['nombre', 'correo', 'telefono', 'dni'];
const draft = reactive({ nombre: '', correo: '', telefono: '', dni: '', password_nueva: '' });
const original = ref({});
const errors = ref({});
const saving = ref(false);
const notice = ref('');
const requestError = ref('');
watch(() => auth.sessionRevision, () => {
  editor.value?.close();
  finishEdit();
  notice.value = '';
});

const changes = computed(() => {
  const payload = {};
  for (const field of profileFields) {
    const value = field === 'correo' ? draft[field].trim().toLowerCase() : draft[field].trim();
    if (value !== original.value[field]) payload[field] = value;
  }
  if (draft.password_nueva) payload.password_nueva = draft.password_nueva;
  return payload;
});
const hasChanges = computed(() => Object.keys(changes.value).length > 0);

const finishEdit = () => {
  editing.value = false;
  draft.password_nueva = '';
};

const openEditor = async () => {
  if (editing.value || saving.value) return;
  original.value = {
    nombre: auth.user.name.trim(),
    correo: auth.user.email.trim().toLowerCase(),
    telefono: (auth.user.telefono || '').trim(),
    dni: (auth.user.dni || '').trim(),
  };
  Object.assign(draft, original.value);
  errors.value = {};
  requestError.value = '';
  notice.value = '';
  editing.value = true;
  await nextTick();
  if (editing.value) editor.value?.showModal();
};

const closeEditor = () => {
  if (!saving.value) editor.value?.close();
};

const save = async () => {
  if (!editing.value || !hasChanges.value || saving.value) return;
  const payload = changes.value;
  errors.value = {
    nombre: payload.nombre === undefined ? '' : requiredTextError(payload.nombre, 'El nombre', FORM_LIMITS.shortText),
    correo: payload.correo === undefined ? '' : emailError(payload.correo),
    dni: payload.dni === undefined ? '' : dniError(payload.dni, Boolean(auth.user.id_cliente)),
    telefono: payload.telefono === undefined ? '' : phoneError(payload.telefono),
    password_nueva: payload.password_nueva ? passwordError(payload.password_nueva) : '',
  };
  requestError.value = '';
  if (Object.values(errors.value).some(Boolean)) {
    await nextTick();
    editor.value?.querySelector('[aria-invalid="true"]')?.focus();
    return;
  }

  saving.value = true;
  try {
    await auth.updateProfile(payload);
    editor.value?.close();
    notice.value = 'Tus datos se actualizaron correctamente.';
  } catch (error) {
    requestError.value = error?.message || 'No se pudieron guardar tus cambios.';
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.account-settings {
  max-width: 68rem;
  margin-inline: auto;
  color: var(--app-text);
}
.account-heading { margin-bottom: 1.55rem; }
.account-heading h1 { font-size: clamp(1.75rem, 3vw, 2.4rem); font-weight: 800; }
.account-heading p, .account-hint { color: var(--app-text-muted); }
.account-heading p { margin-top: .3rem; }
.account-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  align-items: start;
  gap: 1rem;
}
.account-controls { display: grid; gap: 1rem; }
.account-card {
  min-width: 0;
  padding: clamp(1rem, 3vw, 1.55rem);
  border: 1px solid var(--app-border);
  border-radius: 1.25rem;
  background: var(--app-surface);
}
.account-card h2 { font-size: 1.125rem; font-weight: 750; }
.account-card-header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .65rem; }
.account-edit { display: inline-flex; align-items: center; gap: .4rem; }
.account-dialog {
  --account-dialog-padding: clamp(1rem, 3vw, 1.5rem);
  width: min(42rem, calc(100% - 2rem));
  max-height: calc(100dvh - 2rem);
  margin: auto;
  padding: 0;
  border: 0;
  border-radius: 1.25rem;
  background: var(--app-canvas);
  color: var(--app-text);
  overflow: hidden;
}
.account-dialog::backdrop { background: rgb(0 0 0 / 65%); }
.account-editor { display: flex; flex-direction: column; max-height: inherit; padding: 0; }
.account-editor > .account-card-header, .account-editor > .account-actions {
  flex: none;
  padding: .75rem var(--account-dialog-padding);
}
.account-editor > .account-card-header { border-bottom: 1px solid var(--app-border); }
.account-editor > .account-actions { margin-top: 0; border-top: 1px solid var(--app-border); }
.account-editor-body { min-height: 0; padding: var(--account-dialog-padding); overflow-y: auto; overscroll-behavior: contain; }
.account-password-fields { margin-top: 1.2rem; }
.account-password-mask { letter-spacing: .18em; }
.account-icon { display: grid; place-items: center; width: 2.75rem; height: 2.75rem; border-radius: .7rem; color: var(--app-text-muted); }
.account-icon:hover:enabled { background: var(--app-surface-soft); }
.account-identity { display: flex; align-items: center; gap: .85rem; margin-block: 1.2rem; }
.account-avatar {
  display: grid;
  place-items: center;
  flex: none;
  width: 3.5rem;
  height: 3.5rem;
  border: 1px solid var(--app-border-strong);
  border-radius: 1rem;
  background: var(--app-accent-soft);
  color: var(--app-accent-text);
  font-size: 1.15rem;
  font-weight: 800;
}
.account-name { font-weight: 750; overflow-wrap: anywhere; }
.account-role, .account-details dt, .account-hint { color: var(--app-text-muted); font-size: .875rem; }
.account-details { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 1.25rem; }
.account-membership { margin-top: .9rem; }
.account-details > div { padding-block: .8rem; border-top: 1px solid var(--app-border); }
.account-details dd { margin-top: .2rem; font-weight: 600; overflow-wrap: anywhere; }
.account-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.account-fields label { display: block; margin-bottom: .4rem; font-weight: 650; }
.account-fields input { width: 100%; min-height: 2.75rem; padding: .55rem .75rem; border: 1px solid; border-radius: .7rem; }
.account-fields p { margin-top: .35rem; font-size: .875rem; }
.account-field-error { color: var(--app-notice-error); }
.account-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: .55rem; margin-top: 1.25rem; }
.account-button {
  min-height: 2.75rem;
  padding: .55rem .85rem;
  border: 1px solid var(--app-border);
  border-radius: .7rem;
  background: var(--app-surface-soft);
  font-size: .875rem;
  font-weight: 700;
}
.account-primary { color: white; background: var(--app-accent); border-color: var(--app-accent); }
.account-primary:hover:enabled { background: var(--app-accent-hover); }
.account-button:disabled { opacity: .56; cursor: default; }
.account-card > .account-hint { margin-top: .3rem; }
.account-themes { display: flex; flex-wrap: wrap; gap: .65rem; margin-top: .95rem; }
.account-themes label {
  display: flex;
  align-items: center;
  gap: .55rem;
  padding: .55rem .75rem;
  min-height: 2.75rem;
  border: 1px solid var(--app-border);
  border-radius: .75rem;
  background: var(--app-surface-soft);
  cursor: pointer;
}
.account-themes label:has(:checked) { border-color: var(--app-border-strong); background: var(--app-accent-soft); }
.account-themes input { accent-color: var(--app-accent); }
@media (max-width: 1023px) {
  .account-heading h1 { display: none; }
  .account-heading p { margin-top: 0; }
}
@media (max-width: 767px) {
  .account-layout { grid-template-columns: 1fr; }
  .account-email { grid-column: 1 / -1; }
}
@media (max-width: 540px) {
  .account-fields { grid-template-columns: 1fr; }
}
</style>
