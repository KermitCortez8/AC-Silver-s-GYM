import { feedbackClass as noticeClassFor } from '../../utils/feedback.js';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { blockSpecialChars } from '../../utils/inputGuards.js';
import { cleanText, DEFAULT_PAGE_SIZE, matchesSearch, missingFields, NAME_MAX_LENGTH, sortRows } from '../../../domain/utils/inputRules.js';
import { useGymStore } from '../../../application/stores/gymStore';
import { parseQuantity, MAX_QUANTITY } from '../../../domain/utils/quantities.js';
import { INVENTORY_CATEGORIES, INVENTORY_LOCATIONS, INVENTORY_UNITS, inventoryOptions } from '../../utils/inventoryOptions.js';

/** Coordina búsqueda, edición y operaciones de inventario. */
export const useInventoryWorkspace = () => {
  const route = useRoute();
  const router = useRouter();
  const gymStore = useGymStore();
  const tabs = [
    { value: 'articulos', label: 'Artículos' },
    { value: 'movimientos', label: 'Movimientos' },
  ];
  const activeTab = computed({
    get: () => (tabs.some((tab) => tab.value === route.query.tab) ? route.query.tab : 'articulos'),
    set: (tab) => router.replace({ query: { ...route.query, tab } }),
  });
  const inventory = computed(() => gymStore.inventory.filter((item) => !item.archived));

  // Filtros de la tabla (solo lectura, no afectan el store).
  const searchQuery = ref('');
  const selectedCategory = ref('all');
  const selectedLocation = ref('all');
  const selectedStatus = ref('all');

  const locationOptions = computed(() => {
    const set = new Set(inventory.value.map((item) => item.location).filter(Boolean));
    return Array.from(set);
  });
  const locationChoices = computed(() => inventoryOptions(INVENTORY_LOCATIONS, locationOptions.value, form.location));

  // Buscar por codigo, nombre o categoria, conservando los filtros de la tabla.
  const filteredInventory = computed(() => inventory.value.filter((item) => {
    const matchesQuery = matchesSearch(searchQuery.value, [item.inventoryCode, item.name, item.category]);
    const matchesCategory = selectedCategory.value === 'all' || (item.category || 'General') === selectedCategory.value;
    const matchesLocation = selectedLocation.value === 'all' || item.location === selectedLocation.value;
    const matchesStatus = selectedStatus.value === 'all' || item.status === selectedStatus.value;
    return matchesQuery && matchesCategory && matchesLocation && matchesStatus;
  }));

  // Orden por columna: clic alterna ascendente y descendente.
  const sortKey = ref('');
  const sortDir = ref('asc');
  const SORT_COLUMNS = {
    code: { accessor: (item) => item.inventoryCode, type: 'text' },
    name: { accessor: (item) => item.name, type: 'text' },
    quantity: { accessor: (item) => item.quantity, type: 'number' },
  };
  const toggleSort = (column) => {
    sortDir.value = sortKey.value === column && sortDir.value === 'asc' ? 'desc' : 'asc';
    sortKey.value = column;
    paginaActual.value = 1;
  };
  const sortedInventory = computed(() => {
    const column = SORT_COLUMNS[sortKey.value];
    return column ? sortRows(filteredInventory.value, column.accessor, sortDir.value, column.type) : filteredInventory.value;
  });

  // Paginacion (sobre la lista filtrada y ordenada).
  const paginaActual = ref(1);
  const porPagina = ref(DEFAULT_PAGE_SIZE);
  const paginaInicio = computed(() => (paginaActual.value - 1) * porPagina.value);
  const totalPages = computed(() => Math.max(1, Math.ceil(sortedInventory.value.length / porPagina.value)));
  const inventoryPaginado = computed(() => sortedInventory.value.slice(paginaInicio.value, paginaInicio.value + porPagina.value));

  watch([searchQuery, selectedCategory, selectedLocation, selectedStatus], () => { paginaActual.value = 1; });
  watch(totalPages, (pages) => { paginaActual.value = Math.max(1, Math.min(paginaActual.value, pages)); });

  // Derivados de inventory, solo lectura.
  const categorySummary = computed(() => {
    const counts = new Map();
    inventory.value.forEach((item) => {
      const key = item.category || 'General';
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    return Array.from(counts.entries()).map(([name, count]) => ({ name, count }));
  });
  const editingId = ref('');
  const isEditorOpen = ref(false);
  const isSaving = ref(false);
  const editorError = ref('');
  const feedbackMessage = ref('');
  const feedbackTone = ref('info');
  const formErrors = ref([]);
  const nameWarning = ref('');
  const numberWarning = reactive({ quantity: '', minQuantity: '' });

  const form = reactive({
    name: '',
    category: 'General',
    quantity: 0,
    minQuantity: '',
    unidad_venta: 'unidad',
    precio_venta: 0,
    location: 'Recepción',
    status: 'Operativo',
    observations: '',
  });

  const categoryOptions = computed(() => inventoryOptions(INVENTORY_CATEGORIES, inventory.value.map(item => item.category), form.category));
  const editorLocationOptions = computed(() => inventoryOptions(INVENTORY_LOCATIONS, inventory.value.map(item => item.location), form.location));
  const unitOptions = computed(() => inventoryOptions(INVENTORY_UNITS, inventory.value.map(item => item.unidad_venta), form.unidad_venta));
  const stepQuantity = (delta) => {
    try {
      form.quantity = Math.min(MAX_QUANTITY, Math.max(0, parseQuantity(form.quantity) + delta));
      editorError.value = '';
    } catch (error) { editorError.value = error.message; }
  };

  const isTiendaForm = computed(() => String(form.category || '').trim().toLowerCase() === 'tienda');
  // En articulos de Tienda el estado lo calcula el backend; solo se marca o desmarca Descontinuado.
  const isDiscontinuedForm = computed({
    get: () => form.status === 'Descontinuado',
    set: (value) => { form.status = value ? 'Descontinuado' : 'Disponible'; },
  });
  const statusPreview = computed(() => {
    if (!isTiendaForm.value || form.status === 'Descontinuado') return form.status;
    const current = inventory.value.find((item) => item.id === editingId.value)?.status;
    return editingId.value && current && current !== 'Descontinuado' ? current : 'Automático';
  });

  const feedbackToneClass = computed(() => noticeClassFor(feedbackTone.value));

  /**
   * Valida los datos recibidos.
   */
  const isLowStock = (item) => Number(item.quantity || 0) <= Number(item.minQuantity || 0);

  // Color del punto por categoria (categoria es texto libre, color estable segun el nombre).
  const categoryDotPalette = ['#0d9488', '#7c3aed', '#2563eb', '#db2777', '#4f46e5'];
  const categoryDotColor = (category) => {
    const key = category || 'General';
    let hash = 0;
    for (let i = 0; i < key.length; i += 1) hash = (hash + key.charCodeAt(i)) % categoryDotPalette.length;
    return categoryDotPalette[hash];
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const inventoryStatusClass = (status) => {
    if (status === 'Operativo') return 'bg-green-100 text-green-700 border-green-300';
    if (status === 'Disponible') return 'bg-blue-100 text-blue-700 border-blue-300';
    if (status === 'En mantenimiento') return 'bg-violet-100 text-violet-700 border-violet-300';
    if (status === 'Stock bajo') return 'bg-orange-100 text-orange-800 border-orange-300';
    if (status === 'Agotado') return 'bg-rose-100 text-rose-700 border-rose-300';
    if (status === 'Descontinuado') return 'bg-slate-300 text-slate-600 border-slate-400 line-through';
    return 'bg-slate-200 text-slate-700 border-slate-300';
  };

  const currentInventoryCode = computed(() => {
    if (editingId.value) {
      return inventory.value.find((item) => item.id === editingId.value)?.inventoryCode || 'Se generará automáticamente';
    }

    return 'Se generará automáticamente';
  });

  // Bloqueo al escribir: nombre sin caracteres especiales y stock solo con enteros.
  const blockNameChars = blockSpecialChars((message) => { nameWarning.value = message; });

  const cleanNameField = (event) => {
    const { value, rejected } = cleanText(event.target.value, NAME_MAX_LENGTH);
    if (value !== event.target.value) {
      event.target.value = value;
      form.name = value;
    }
    nameWarning.value = rejected ? 'Sin caracteres especiales: solo letras, números y espacios.' : '';
    formErrors.value = formErrors.value.filter((label) => label !== 'Nombre');
  };

  const clearFormWarnings = () => {
    formErrors.value = [];
    nameWarning.value = '';
    numberWarning.quantity = '';
    numberWarning.minQuantity = '';
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const resetForm = () => {
    editingId.value = '';
    form.name = '';
    form.category = 'General';
    form.quantity = 0;
    form.minQuantity = '';
    form.unidad_venta = 'unidad';
    form.precio_venta = 0;
    form.location = 'Recepción';
    form.status = 'Operativo';
    form.observations = '';
    clearFormWarnings();
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const openNewItem = () => {
    resetForm();
    editorError.value = '';
    feedbackMessage.value = '';
    isEditorOpen.value = true;
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const closeEditor = () => {
    if (isSaving.value) return;
    editorError.value = '';
    isEditorOpen.value = false;
    resetForm();
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const editItem = (item) => {
    editorError.value = '';
    editingId.value = item.id;
    form.name = item.name;
    form.category = item.category || 'General';
    form.quantity = Number(item.quantity || 0);
    form.minQuantity = Number(item.minQuantity ?? 1);
    form.unidad_venta = item.unidad_venta || 'unidad';
    form.precio_venta = Number(item.precio_venta || 0);
    form.location = item.location || 'Recepción';
    form.status = item.status || 'Operativo';
    form.observations = item.observations || '';
    clearFormWarnings();
    feedbackMessage.value = '';
    isEditorOpen.value = true;
  };

  // Obligatorios: nombre siempre y stock inicial al crear.
  const requiredFields = () => [
    { key: 'name', label: 'Nombre' },
    ...(editingId.value ? [] : [{ key: 'quantity', label: 'Stock inicial', isEmpty: (value) => value === '' || value === null || !Number.isInteger(Number(value)) }]),
  ];

  /**
   * Gestiona esta acción de la vista.
   */
  const handleSubmit = async () => {
    if (isSaving.value) return;
    editorError.value = '';
    try {
      if (!form.name.trim()) throw new Error('El nombre del artículo es obligatorio.');
      const quantity = parseQuantity(form.quantity, { label: 'El stock inicial' });
      // No hay un minimo por defecto: el usuario lo escribe al crear el articulo.
      if (form.minQuantity === '' || form.minQuantity === null || form.minQuantity === undefined) {
        formErrors.value = ['Stock mínimo'];
        throw new Error('El stock mínimo es obligatorio.');
      }
      const minQuantity = parseQuantity(form.minQuantity, { label: 'El stock mínimo' });
      formErrors.value = missingFields(form, requiredFields());
      if (formErrors.value.length) return;
      isSaving.value = true;
      await gymStore.upsertInventoryItem({ id: editingId.value || undefined, ...form, name: form.name.trim(), quantity, minQuantity });
      const savedLabel = editingId.value ? 'Artículo actualizado.' : 'Artículo registrado.';
      isSaving.value = false;
      closeEditor();
      feedbackTone.value = 'success';
      feedbackMessage.value = savedLabel;
    } catch (error) {
      feedbackTone.value = 'error';
      editorError.value = error instanceof Error ? error.message : 'No se pudo guardar el artículo.';
    } finally {
      isSaving.value = false;
    }
  };

  /**
   * Elimina el registro indicado.
   */
  const deleteItem = async (id) => {
    if (!window.confirm('¿Eliminar este artículo?\n\nSi ya tiene movimientos o se vende en Tienda no se borrará: se archivará (deja de mostrarse) y su historial se conserva.')) return;
    try {
      const result = await gymStore.deleteInventoryItem(id);
      feedbackTone.value = 'success';
      feedbackMessage.value = result?.accion === 'archivado'
        ? 'El artículo tiene historial o se vende en Tienda: se archivó y su historial se conserva.'
        : 'Artículo eliminado.';
    } catch (error) {
      feedbackTone.value = 'error';
      feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el artículo.';
    }
  };

  // Detalles: datos del articulo y sus ultimos movimientos, solo lectura.
  const detailItem = ref(null);
  const itemNumber = (item) => Number(String(item?.id ?? '').replace('item-', ''));
  const detailMovements = computed(() => {
    if (!detailItem.value) return [];
    const id = itemNumber(detailItem.value);
    return (gymStore.inventoryMovements || [])
      .filter((movement) => Number(movement.id_item) === id)
      .sort((a, b) => String(b.fecha_movimiento || '').localeCompare(String(a.fecha_movimiento || '')) || Number(b.id_mov || 0) - Number(a.id_mov || 0))
      .slice(0, 6);
  });
  const movementClass = (type) => {
    if (type === 'entrada') return 'bg-emerald-400/15 text-emerald-200';
    if (type === 'salida') return 'bg-rose-400/15 text-rose-200';
    return 'bg-cyan-400/15 text-cyan-200';
  };
  const signedQuantity = (movement) => {
    if (movement.tipo_movimiento === 'entrada') return `+${movement.cantidad}`;
    if (movement.tipo_movimiento === 'salida') return `-${movement.cantidad}`;
    return `= ${movement.cantidad}`;
  };
  const openDetails = (item) => {
    detailItem.value = item;
  };
  const editFromDetails = () => {
    const item = detailItem.value;
    detailItem.value = null;
    if (item) editItem(item);
  };

  onMounted(() => {
    gymStore.fetchFromBackend?.({ section: 'inventory' }).catch((error) => console.warn('No se pudo refrescar inventario:', error));
  });

  return {
    route, router, gymStore, tabs, activeTab,
    inventory, searchQuery, selectedCategory, selectedLocation, selectedStatus,
    locationOptions, locationChoices, filteredInventory, sortKey, sortDir,
    SORT_COLUMNS, toggleSort, sortedInventory, paginaActual, porPagina,
    paginaInicio, totalPages, inventoryPaginado, categorySummary, editingId,
    isEditorOpen, isSaving, editorError, feedbackMessage, feedbackTone,
    formErrors, nameWarning, numberWarning, form, categoryOptions,
    editorLocationOptions, unitOptions, stepQuantity, isTiendaForm, isDiscontinuedForm,
    statusPreview, feedbackToneClass, isLowStock, categoryDotPalette, categoryDotColor,
    inventoryStatusClass, currentInventoryCode, blockNameChars, cleanNameField, clearFormWarnings,
    resetForm, openNewItem, closeEditor, editItem, requiredFields,
    handleSubmit, deleteItem, detailItem, itemNumber, detailMovements,
    movementClass, signedQuantity, openDetails, editFromDetails,
  };
};
