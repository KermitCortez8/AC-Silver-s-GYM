import { validateAccountForm } from '../../../domain/utils/formValidation.js';
import { useFormValidation } from '../useFormValidation.js';
import { feedbackClass as noticeClassFor } from '../../utils/feedback.js';
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../../../application/stores/gymStore';

/** Gestiona el directorio y los formularios de usuarios internos. */
export const useUserDirectory = () => {
  const gymStore = useGymStore();

  const users = computed(() => gymStore.users);

  const search = ref('');
  const roleFilter = ref('');
  const isSaving = ref(false);
  const isLoading = ref(false);
  const roleFilters = [
    { value: '', label: 'Todos' },
    { value: 'admin', label: 'Administradores' },
    { value: 'trainer', label: 'Entrenadores' },
    { value: 'staff', label: 'Personal' },
  ];
  const roleLabel = (role) =>
    ({ admin: 'Administrador', trainer: 'Entrenador', staff: 'Personal' })[
      role
    ] || role;
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

  const { fieldErrors, validateField, revalidateField, validateForm, resetValidation } = useFormValidation(form,
    value => validateAccountForm(value, { requirePassword: !editingId.value, requireDni: false }));

  const filteredUsers = computed(() => {
    const query = search.value.trim().toLowerCase();

    const matchingRole = users.value.filter(
      (user) => !roleFilter.value || user.rol === roleFilter.value,
    );
    if (!query) return matchingRole;

    return matchingRole.filter((systemUser) =>
      [
        systemUser.id_usuario,
        systemUser.nombre,
        systemUser.correo,
        systemUser.telefono,
        systemUser.dni,
        systemUser.rol,
        systemUser.hasPassword ? 'con contraseña' : 'sin contraseña',
      ]
        .join(' ')
        .toLowerCase()
        .includes(query),
    );
  });

  const usersWithPassword = computed(
    () => users.value.filter((systemUser) => systemUser.hasPassword).length,
  );

  const feedbackToneClass = computed(() => noticeClassFor(feedbackTone.value));

  /**
   * Restablece los datos del formulario.
   */
  const resetForm = () => {
    resetValidation();
    editingId.value = '';

    form.nombre = '';
    form.correo = '';
    form.telefono = '';
    form.dni = '';
    form.password = '';
    form.rol = 'staff';
  };

  /**
   * Abre el formulario para registrar un usuario nuevo.
   */
  const openNewUser = () => {
    resetForm();

    feedbackMessage.value = '';
    isEditorOpen.value = true;
  };

  /**
   * Cierra el formulario de creación o edición.
   */
  const closeEditor = () => {
    if (isSaving.value) return;
    isEditorOpen.value = false;

    resetForm();
  };

  /**
   * Carga los datos del usuario seleccionado para editarlo.
   */
  const editUser = (systemUser) => {
    resetValidation();
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

  /**
   * Abre el modal con los detalles del usuario seleccionado.
   */
  const openDetails = (systemUser) => {
    viewingUser.value = systemUser;
    isDetailsOpen.value = true;
  };

  /**
   * Cierra el modal de detalles y limpia el usuario seleccionado.
   */
  const closeDetails = () => {
    isDetailsOpen.value = false;
    viewingUser.value = null;
  };

  /**
   * Elimina un usuario previa confirmación.
   */
  const confirmDelete = async (systemUser) => {
    const confirmed = window.confirm(
      `Eliminar al usuario ${systemUser.id_usuario}?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      await gymStore.deleteUser(systemUser.id_usuario);

      feedbackTone.value = 'success';

      feedbackMessage.value = `Usuario ${systemUser.id_usuario} eliminado.`;

      if (editingId.value === systemUser.id_usuario) {
        closeEditor();
      }
    } catch (error) {
      feedbackTone.value = 'error';

      feedbackMessage.value =
        error instanceof Error
          ? error.message
          : 'No se pudo eliminar el usuario.';
    }
  };

  /**
   * Registra o actualiza los datos del usuario.
   */
  const handleSubmit = async () => {
    if (isSaving.value) return;
    isSaving.value = true;
    feedbackMessage.value = '';
    try {
      if (!validateForm()) throw new Error(Object.values(fieldErrors)[0]);
      const saved = await gymStore.upsertUser({
        id_usuario: editingId.value || undefined,

        nombre: form.nombre,

        correo: form.correo.trim().toLowerCase(),

        telefono: form.telefono,

        dni: form.dni,

        password: form.password,

        rol: form.rol,
      });

      isSaving.value = false;
      closeEditor();

      feedbackTone.value = 'success';

      feedbackMessage.value = `Usuario ${saved.id_usuario} guardado.`;
    } catch (error) {
      feedbackTone.value = 'error';

      feedbackMessage.value =
        error instanceof Error ? error.message : 'No se pudo guardar el usuario.';
      Object.assign(fieldErrors, error?.fieldErrors || {});
    } finally {
      isSaving.value = false;
    }
  };

  onMounted(async () => {
    isLoading.value = true;
    try {
      await gymStore.fetchFromBackend?.({ section: 'users' });
    } catch {
      feedbackTone.value = 'error';
      feedbackMessage.value =
        'No se pudieron actualizar los usuarios. Inténtalo de nuevo más tarde.';
    } finally {
      isLoading.value = false;
    }
  });

  return {
    gymStore, users, search, roleFilter, isSaving,
    isLoading, roleFilters, roleLabel, editingId, isEditorOpen,
    isDetailsOpen, viewingUser, feedbackMessage, feedbackTone, form,
    fieldErrors, validateField, revalidateField, validateForm, resetValidation,
    filteredUsers, usersWithPassword, feedbackToneClass, resetForm, openNewUser,
    closeEditor, editUser, openDetails, closeDetails, confirmDelete,
    handleSubmit,
  };
};
