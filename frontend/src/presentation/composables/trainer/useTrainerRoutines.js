import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useGymStore } from '../../../application/stores/gymStore';

/** Coordina el catálogo de rutinas y la validación de sus ejercicios. */
export const useTrainerRoutines = () => {
  const gymStore = useGymStore();

  const MAX_NOMBRE = 60;
  const MAX_ZONAS = 300;
  const MAX_EJERCICIO = 80;

  const isSaving = ref(false);
  const isLoading = ref(false);
  const errorMessage = ref('');
  const showRoutineModal = ref(false);
  const searchQuery = ref('');
  const selectedServiceFilter = ref('todos');
  const sortBy = ref('nombre');

  // Paginación de la Tabla
  const itemsPerPage = ref(5);
  const currentPage = ref(1);

  const setItemsPerPage = (size) => {
    itemsPerPage.value = size;
    currentPage.value = 1;
  };

  const setServiceFilter = (service) => {
    selectedServiceFilter.value = service;
    currentPage.value = 1;
  };

  // Toasts flotantes
  const toastMessage = ref('');
  const toastType = ref('success');
  let toastTimer = null;

  const showToast = (message, type = 'success') => {
    toastMessage.value = message;
    toastType.value = type;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastMessage.value = '';
    }, 4000);
  };

  const serviceOptions = [
    { value: 'fitness', label: 'Fitness' },
    { value: 'musculacion', label: 'Musculación' },
    { value: 'cardio', label: 'Cardio' },
    { value: 'baile', label: 'Baile' },
  ];

  const quickZones = ['Pierna', 'Glúteos', 'Core', 'Pecho', 'Espalda', 'Hombro', 'Brazos', 'Cardio'];

  const routineForm = reactive({
    id_rutina: null,
    servicio: 'fitness',
    nombre_rutina: '',
    zonas_musculares: '',
    color: 'Azul',
    ejercicios: [],
  });

  // Estado de validación / edición
  const touched = reactive({ nombre_rutina: false, zonas_musculares: false });
  const submitted = ref(false);
  const baselineSignature = ref(''); // "foto" del formulario al abrir el modal
  const editingName = ref(''); // nombre original de la rutina en edición

  const overview = computed(() => gymStore.trainerOverview || {});
  const routines = computed(() => overview.value.routines || []);

  /**
   * Normaliza texto para comparar (minúsculas, sin tildes, sin espacios extra).
   */
  const norm = (value) =>
    String(value || '')
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

  // Métricas KPI
  const routinesWithExercisesCount = computed(() => routines.value.filter((r) => Array.isArray(r.ejercicios) && r.ejercicios.length > 0).length);

  const averageExercisesPerRoutine = computed(() => {
    if (!routines.value.length) return 0;
    const totalEx = routines.value.reduce((acc, r) => acc + (Array.isArray(r.ejercicios) ? r.ejercicios.length : 0), 0);
    return (totalEx / routines.value.length).toFixed(1);
  });

  const activeServicesCount = computed(() => new Set(routines.value.map((r) => norm(r.servicio))).size);

  // Filtros, búsqueda y orden
  const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';

  const routinesForService = (service) => routines.value.filter((routine) => norm(routine.servicio) === norm(service));

  const exerciseCount = (routine) => (Array.isArray(routine.ejercicios) ? routine.ejercicios.length : 0);

  const filteredRoutines = computed(() => {
    const query = norm(searchQuery.value);
    const list = routines.value.filter((r) => {
      const matchesService = selectedServiceFilter.value === 'todos' || norm(r.servicio) === selectedServiceFilter.value;
      const matchesSearch =
        !query ||
        norm(r.nombre_rutina).includes(query) ||
        norm(r.zonas_musculares).includes(query) ||
        (Array.isArray(r.ejercicios) && r.ejercicios.some((ex) => norm(ex.nombre_ejercicio).includes(query)));
      return matchesService && matchesSearch;
    });

    return [...list].sort((a, b) => {
      if (sortBy.value === 'asignados') return Number(b.clientes_asignados || 0) - Number(a.clientes_asignados || 0);
      if (sortBy.value === 'ejercicios') return exerciseCount(b) - exerciseCount(a);
      return String(a.nombre_rutina || '').localeCompare(String(b.nombre_rutina || ''), 'es');
    });
  });

  const clearFilters = () => {
    searchQuery.value = '';
    setServiceFilter('todos');
  };

  const totalPages = computed(() => Math.ceil(filteredRoutines.value.length / itemsPerPage.value) || 1);

  const paginatedRoutines = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage.value;
    return filteredRoutines.value.slice(start, start + itemsPerPage.value);
  });

  const showingStart = computed(() => {
    if (!filteredRoutines.value.length) return 0;
    return (currentPage.value - 1) * itemsPerPage.value + 1;
  });

  const showingEnd = computed(() => Math.min(currentPage.value * itemsPerPage.value, filteredRoutines.value.length));

  // Al cambiar búsqueda u orden vuelve a la página 1; si la página actual ya no existe (p. ej. tras guardar), se ajusta
  watch([searchQuery, sortBy], () => {
    currentPage.value = 1;
  });
  watch(totalPages, (pages) => {
    if (currentPage.value > pages) currentPage.value = pages;
  });

  // Ayudantes de parsing y sincronización de modos de repetición
  const parseRepeticiones = (repStr) => {
    const str = String(repStr || '').trim();
    if (str.toLowerCase().includes('fallo')) {
      return { rep_modo: 'fallo', rep_fijo: '', rep_min: '', rep_max: '', repeticiones: 'Al fallo' };
    }
    if (str.includes('-')) {
      const parts = str.split('-');
      return {
        rep_modo: 'rango',
        rep_fijo: '',
        rep_min: (parts[0] || '10').trim(),
        rep_max: (parts[1] || '12').trim(),
        repeticiones: str,
      };
    }
    return {
      rep_modo: 'fijo',
      rep_fijo: str || '10',
      rep_min: '',
      rep_max: '',
      repeticiones: str || '10',
    };
  };

  /**
   * Construye el texto de repeticiones según el modo (sin modificar el ejercicio).
   */
  const buildRepString = (ex) => {
    if (ex.rep_modo === 'fijo') return String(ex.rep_fijo || '10');
    if (ex.rep_modo === 'rango') return `${ex.rep_min || '10'}-${ex.rep_max || '12'}`;
    return 'Al fallo';
  };

  const syncRepString = (ex) => {
    ex.repeticiones = buildRepString(ex);
  };

  const setRepMode = (ex, mode) => {
    ex.rep_modo = mode;
    if (mode === 'fijo' && !ex.rep_fijo) ex.rep_fijo = '10';
    if (mode === 'rango') {
      if (!ex.rep_min) ex.rep_min = '10';
      if (!ex.rep_max) ex.rep_max = '12';
    }
    syncRepString(ex);
  };

  /**
   * Convierte un ejercicio del formulario al formato que se envía / compara.
   */
  const buildExercise = (ex) => ({
    id_ejercicio: ex.id_ejercicio ?? null,
    nombre_ejercicio: String(ex.nombre_ejercicio || '').trim(),
    grupo_muscular: String(ex.grupo_muscular || '').trim(),
    series: Number(ex.series || 3),
    repeticiones: buildRepString(ex),
    descanso_segundos: Number(ex.descanso_segundos || 60),
    peso_sugerido_kg: ex.peso_sugerido_kg !== null && ex.peso_sugerido_kg !== undefined && ex.peso_sugerido_kg !== '' ? Number(ex.peso_sugerido_kg) : null,
    notas: ex.notas || '',
  });

  /**
   * Datos del formulario ya limpios (los que se guardan).
   */
  const buildPayload = () => ({
    ...routineForm,
    nombre_rutina: routineForm.nombre_rutina.trim(),
    zonas_musculares: routineForm.zonas_musculares.trim(),
    ejercicios: routineForm.ejercicios.map(buildExercise),
  });

  const buildSignature = () => {
    const { servicio, nombre_rutina, zonas_musculares, ejercicios } = buildPayload();
    return JSON.stringify({ servicio, nombre_rutina, zonas_musculares, ejercicios });
  };

  // ---------- Cambios sin guardar ----------
  const hasChanges = computed(() => buildSignature() !== baselineSignature.value);

  const editingAssignedCount = computed(() => {
    const current = routines.value.find((r) => r.id_rutina === routineForm.id_rutina);
    return Number(current?.clientes_asignados || 0);
  });

  // ---------- Validaciones (en vivo) ----------
  const exerciseErrors = computed(() =>
    routineForm.ejercicios.map((ex) => {
      const result = {};
      const nombre = String(ex.nombre_ejercicio || '').trim();
      const series = Number(ex.series);

      if (!nombre) result.nombre = 'El nombre es obligatorio.';
      else if (nombre.length > MAX_EJERCICIO) result.nombre = `Máximo ${MAX_EJERCICIO} caracteres.`;

      if (!Number.isInteger(series) || series < 1 || series > 20) result.series = 'Entre 1 y 20.';

      if (ex.rep_modo === 'fijo') {
        const fijo = Number(ex.rep_fijo);
        if (!Number.isInteger(fijo) || fijo < 1) result.reps = 'Indica un número de repeticiones válido.';
      } else if (ex.rep_modo === 'rango') {
        const min = Number(ex.rep_min);
        const max = Number(ex.rep_max);
        if (!Number.isInteger(min) || !Number.isInteger(max) || min < 1) result.reps = 'Indica un mínimo y un máximo válidos.';
        else if (max <= min) result.reps = 'El máximo debe ser mayor que el mínimo.';
      }

      const peso = ex.peso_sugerido_kg;
      if (peso !== null && peso !== undefined && peso !== '' && (!Number.isFinite(Number(peso)) || Number(peso) < 0)) {
        result.peso = 'El peso no puede ser negativo.';
      }
      return result;
    }),
  );

  const errors = computed(() => {
    const result = {};
    const nombre = routineForm.nombre_rutina.trim();
    const zonas = routineForm.zonas_musculares.trim();

    if (!serviceOptions.some((service) => service.value === routineForm.servicio)) {
      result.servicio = 'Selecciona un servicio válido.';
    }

    if (!nombre) {
      result.nombre_rutina = 'El nombre es obligatorio.';
    } else if (nombre.length < 3) {
      result.nombre_rutina = 'Usa al menos 3 caracteres.';
    } else if (nombre.length > MAX_NOMBRE) {
      result.nombre_rutina = `Máximo ${MAX_NOMBRE} caracteres.`;
    } else if (
      routines.value.some(
        (r) => r.id_rutina !== routineForm.id_rutina && norm(r.servicio) === routineForm.servicio && norm(r.nombre_rutina) === norm(nombre),
      )
    ) {
      result.nombre_rutina = 'Ya existe una rutina con ese nombre en este servicio.';
    }

    if (!zonas) {
      result.zonas_musculares = 'Indica al menos una zona muscular.';
    } else if (zonas.length < 3) {
      result.zonas_musculares = 'Describe las zonas con más detalle.';
    } else if (zonas.length > MAX_ZONAS) {
      result.zonas_musculares = `Máximo ${MAX_ZONAS} caracteres.`;
    }

    const badExercises = exerciseErrors.value.filter((e) => Object.keys(e).length).length;
    if (badExercises) {
      result.ejercicios = `Revisa ${badExercises} ${badExercises === 1 ? 'ejercicio' : 'ejercicios'} con datos incompletos o inválidos.`;
    }

    return result;
  });

  /**
   * Muestra el error solo si el campo fue tocado o ya se intentó guardar.
   */
  const fieldError = (field) => (submitted.value || touched[field] ? errors.value[field] : '');

  /**
   * Error de un campo de un ejercicio (solo después de intentar guardar).
   */
  const exError = (index, field) => (submitted.value ? exerciseErrors.value[index]?.[field] : '');

  // ---------- Zonas rápidas ----------
  const zoneActive = (zone) => routineForm.zonas_musculares.split(',').some((part) => norm(part) === norm(zone));

  const toggleZone = (zone) => {
    const parts = routineForm.zonas_musculares.split(',').map((part) => part.trim()).filter(Boolean);
    const index = parts.findIndex((part) => norm(part) === norm(zone));
    if (index >= 0) parts.splice(index, 1);
    else parts.push(zone);
    routineForm.zonas_musculares = parts.join(', ');
    touched.zonas_musculares = true;
  };

  // ---------- Modal & ejercicios ----------
  const addExercise = () => {
    routineForm.ejercicios.push({
      nombre_ejercicio: '',
      series: 3,
      rep_modo: 'rango',
      rep_fijo: '10',
      rep_min: '10',
      rep_max: '12',
      repeticiones: '10-12',
      descanso_segundos: 60,
      peso_sugerido_kg: null,
      grupo_muscular: '',
      notas: '',
    });
  };

  const removeExercise = (index) => {
    routineForm.ejercicios.splice(index, 1);
  };

  const resetRoutineForm = () => {
    routineForm.id_rutina = null;
    routineForm.servicio = 'fitness';
    routineForm.nombre_rutina = '';
    routineForm.zonas_musculares = '';
    routineForm.color = 'Azul';
    routineForm.ejercicios = [];
    submitted.value = false;
    touched.nombre_rutina = false;
    touched.zonas_musculares = false;
    editingName.value = '';
    baselineSignature.value = buildSignature();
  };

  /**
   * Abre el modal y guarda la "foto" inicial para detectar cambios.
   */
  const openModal = () => {
    baselineSignature.value = buildSignature();
    showRoutineModal.value = true;
  };

  const openCreateModal = () => {
    resetRoutineForm();
    // Si hay un servicio filtrado, la rutina nueva se crea en ese servicio
    if (selectedServiceFilter.value !== 'todos') routineForm.servicio = selectedServiceFilter.value;
    openModal();
  };

  const editRoutine = (routine) => {
    resetRoutineForm();
    routineForm.id_rutina = routine.id_rutina;
    routineForm.servicio = routine.servicio || 'fitness';
    routineForm.nombre_rutina = routine.nombre_rutina || '';
    routineForm.zonas_musculares = routine.zonas_musculares || '';
    routineForm.color = routine.color || 'Azul';
    routineForm.ejercicios = Array.isArray(routine.ejercicios)
      ? routine.ejercicios.map((ex) => ({
          ...ex,
          ...parseRepeticiones(ex.repeticiones),
        }))
      : [];
    editingName.value = routineForm.nombre_rutina;
    openModal();
  };

  /**
   * Cierra el modal sin preguntar (después de guardar).
   */
  const closeRoutineModal = () => {
    showRoutineModal.value = false;
    resetRoutineForm();
  };

  /**
   * Cierra el modal pidiendo confirmación solo si hay cambios sin guardar.
   */
  const requestCloseModal = () => {
    if (hasChanges.value && !window.confirm('Tienes cambios sin guardar. ¿Descartarlos?')) return;
    closeRoutineModal();
  };

  const saveRoutine = async () => {
    submitted.value = true;
    if (Object.keys(errors.value).length) {
      showToast('Revisa los campos marcados antes de guardar.', 'error');
      return;
    }

    if (isSaving.value) return;
    const wasEditing = routineForm.id_rutina !== null;
    try {
      isSaving.value = true;
      await gymStore.upsertTrainerRoutine(buildPayload());
      showToast(wasEditing ? 'Rutina actualizada exitosamente.' : 'Nueva rutina creada exitosamente.', 'success');
      closeRoutineModal();
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'No se pudo guardar la rutina.', 'error');
    } finally {
      isSaving.value = false;
    }
  };

  const refresh = async (notify = true) => {
    if (isLoading.value) return;
    try {
      isLoading.value = true;
      errorMessage.value = '';
      await gymStore.fetchTrainerOverview({ force: notify });
      if (notify) showToast('Datos del catálogo actualizados.', 'success');
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'No se pudo cargar rutinas.';
      showToast(errorMessage.value, 'error');
    } finally {
      isLoading.value = false;
    }
  };

  // Carga inicial silenciosa (sin toast de "actualizados")
  onMounted(() => refresh(false));
  onUnmounted(() => {
    if (toastTimer) clearTimeout(toastTimer);
  });

  return {
    gymStore, MAX_NOMBRE, MAX_ZONAS, MAX_EJERCICIO, isSaving,
    isLoading, errorMessage, showRoutineModal, searchQuery, selectedServiceFilter,
    sortBy, itemsPerPage, currentPage, setItemsPerPage, setServiceFilter,
    toastMessage, toastType, toastTimer, showToast, serviceOptions,
    quickZones, routineForm, touched, submitted, baselineSignature,
    editingName, overview, routines, norm, routinesWithExercisesCount,
    averageExercisesPerRoutine, activeServicesCount, serviceLabel, routinesForService, exerciseCount,
    filteredRoutines, clearFilters, totalPages, paginatedRoutines, showingStart,
    showingEnd, parseRepeticiones, buildRepString, syncRepString, setRepMode,
    buildExercise, buildPayload, buildSignature, hasChanges, editingAssignedCount,
    exerciseErrors, errors, fieldError, exError, zoneActive,
    toggleZone, addExercise, removeExercise, resetRoutineForm, openModal,
    openCreateModal, editRoutine, closeRoutineModal, requestCloseModal, saveRoutine,
    refresh,
  };
};
