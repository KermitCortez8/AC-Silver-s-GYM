import { feedbackClass as noticeClassFor } from '../../utils/feedback.js';
import { MAX_QUANTITY, parseQuantity } from '../../../domain/utils/quantities.js';
import { limaDate } from '../../../domain/utils/dates.js';
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { ArrowDownToLine, ArrowUpFromLine, SlidersHorizontal } from 'lucide-vue-next';
import { useAuthStore } from '../../../application/stores/authStore';
import { useGymStore } from '../../../application/stores/gymStore';

/** Gestiona filtros, exportación y registro de movimientos del almacén. */
export const useInventoryMovements = () => {
  const authStore = useAuthStore();
  const gymStore = useGymStore();

  const feedback = ref('');
  const feedbackTone = ref('success');
  const isSaving = ref(false);
  const search = ref('');
  const dateFrom = ref('');
  const dateTo = ref('');
  const filterType = ref('todos');
  const visibleCount = ref(8);
  const pageSize = 8;
  const errors = reactive({ id_item: '', cantidad: '' });

  const inventory = computed(() => gymStore.inventory);
  const activeInventory = computed(() => inventory.value.filter((item) => !item.archived));
  const movements = computed(() =>
    [...(gymStore.inventoryMovements || [])].sort(
      (a, b) =>
        String(b.fecha_movimiento || '').localeCompare(
          String(a.fecha_movimiento || ''),
        ) || Number(b.id_mov) - Number(a.id_mov),
    ),
  );

  const form = reactive({
    id_item: 0,
    tipo_movimiento: 'entrada',
    cantidad: 1,
    fecha_movimiento: limaDate(),
    descripcion: '',
  });

  const movementTypes = [
    {
      value: 'entrada',
      label: 'Entrada',
      icon: ArrowDownToLine,
      activeClass: 'ws-border-success ws-tint-success ws-success',
    },
    {
      value: 'salida',
      label: 'Salida',
      icon: ArrowUpFromLine,
      activeClass: 'ws-border-danger ws-tint-danger ws-danger',
    },
    {
      value: 'ajuste',
      label: 'Ajuste',
      icon: SlidersHorizontal,
      activeClass: 'ws-border-info ws-tint-info ws-info',
    },
  ];

  const feedbackClass = computed(() => noticeClassFor(feedbackTone.value));

  /**
   * Devuelve el id numerico normalizado de un item de inventario.
   */
  const itemId = (item) => Number(String(item.id).replace('item-', ''));

  /**
   * Busca el nombre de un item por su id.
   */
  const itemName = (idItem) =>
    inventory.value.find((item) => itemId(item) === Number(idItem))?.name ||
    `Item #${idItem}`;

  /**
   * Busca el nombre de usuario que registro el movimiento.
   */
  const userName = (idUsuario) => {
    if (!idUsuario) return 'Sistema';
    const match = gymStore.users?.find(
      (user) =>
        String(user.id_usuario) === String(idUsuario) ||
        String(user.id) === String(idUsuario),
    );
    return match?.nombre || `Usuario #${idUsuario}`;
  };

  /**
   * Formatea una fecha ISO a un formato legible corto.
   */
  const formatDate = (value) => {
    if (!value) return 'Sin fecha';
    const parsed = new Date(`${value}T00:00:00`);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString('es-PE', {
      timeZone: 'UTC',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const movementLabel = (type) =>
    ({ entrada: 'Entrada', salida: 'Salida', ajuste: 'Ajuste' })[type] || type;
  const movementIcon = (type) =>
    ({
      entrada: ArrowDownToLine,
      salida: ArrowUpFromLine,
      ajuste: SlidersHorizontal,
    })[type] || SlidersHorizontal;
  const movementClass = (type) =>
    type === 'entrada'
      ? 'ws-tint-success ws-success'
      : type === 'salida'
        ? 'ws-tint-danger ws-danger'
        : 'ws-tint-info ws-info';
  const quantityClass = (type) =>
    type === 'entrada'
      ? 'ws-success'
      : type === 'salida'
        ? 'ws-danger'
        : 'ws-info';
  const signedQuantity = (movement) => {
    if (movement.tipo_movimiento === 'salida') return `-${movement.cantidad}`;
    if (movement.tipo_movimiento === 'entrada') return `+${movement.cantidad}`;
    return `= ${movement.cantidad}`;
  };

  const dateInRange = (value) => {
    if (!value) return !dateFrom.value && !dateTo.value ? true : false;
    if (dateFrom.value && value < dateFrom.value) return false;
    if (dateTo.value && value > dateTo.value) return false;
    return true;
  };

  const baseFiltered = computed(() => {
    const query = search.value.trim().toLowerCase();
    return movements.value.filter((movement) => {
      if (
        query &&
        ![
          itemName(movement.id_item),
          movement.tipo_movimiento,
          movement.descripcion,
        ]
          .join(' ')
          .toLowerCase()
          .includes(query)
      )
        return false;
      if (dateFrom.value || dateTo.value) {
        if (!dateInRange(movement.fecha_movimiento)) return false;
      }
      return true;
    });
  });

  const typeChips = computed(() => [
    {
      value: 'todos',
      label: 'Todos',
      count: baseFiltered.value.length,
      activeClass: 'ws-border-warning ws-tint-warning ws-warning',
    },
    {
      value: 'entrada',
      label: 'Entradas',
      count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'entrada')
        .length,
      activeClass: 'ws-border-success ws-tint-success ws-success',
    },
    {
      value: 'salida',
      label: 'Salidas',
      count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'salida')
        .length,
      activeClass: 'ws-border-danger ws-tint-danger ws-danger',
    },
    {
      value: 'ajuste',
      label: 'Ajustes',
      count: baseFiltered.value.filter((m) => m.tipo_movimiento === 'ajuste')
        .length,
      activeClass: 'ws-border-info ws-tint-info ws-info',
    },
  ]);

  const filteredMovements = computed(() => {
    if (filterType.value === 'todos') return baseFiltered.value;
    return baseFiltered.value.filter(
      (movement) => movement.tipo_movimiento === filterType.value,
    );
  });

  const visibleMovements = computed(() =>
    filteredMovements.value.slice(0, visibleCount.value),
  );
  const hasActiveFilters = computed(() =>
    Boolean(
      search.value.trim() ||
      dateFrom.value ||
      dateTo.value ||
      filterType.value !== 'todos',
    ),
  );

  const periodLabel = computed(() =>
    dateFrom.value || dateTo.value ? 'en el rango' : 'totales',
  );
  const periodMovements = computed(() => baseFiltered.value);
  const stats = computed(() => ({
    entradas: periodMovements.value
      .filter((m) => m.tipo_movimiento === 'entrada')
      .reduce((sum, m) => sum + Number(m.cantidad || 0), 0),
    salidas: periodMovements.value
      .filter((m) => m.tipo_movimiento === 'salida')
      .reduce((sum, m) => sum + Number(m.cantidad || 0), 0),
    ajustes: periodMovements.value.filter((m) => m.tipo_movimiento === 'ajuste')
      .length,
  }));

  const selectedItem = computed(() =>
    inventory.value.find((item) => itemId(item) === Number(form.id_item)),
  );
  const resultingStock = computed(() => {
    const item = selectedItem.value;
    if (!item || !form.cantidad) return '';
    const current = Number(item.quantity || 0);
    const unit = item.unidad_venta || 'unidad';
    if (form.tipo_movimiento === 'entrada')
      return `El stock quedará en ${current + Number(form.cantidad)} ${unit}.`;
    if (form.tipo_movimiento === 'salida') {
      const next = current - Number(form.cantidad);
      return next < 0
        ? `Atención: el stock actual es ${current} ${unit}.`
        : `El stock quedará en ${next} ${unit}.`;
    }
    return `Stock actual: ${current} ${unit}.`;
  });

  /**
   * Incrementa o decrementa la cantidad del formulario.
   */
  const stepCantidad = (delta) => {
    try {
      form.cantidad = Math.min(MAX_QUANTITY, Math.max(1, parseQuantity(form.cantidad, { min: 1 }) + delta));
      errors.cantidad = '';
    } catch (error) {
      errors.cantidad = error.message;
    }
  };

  /**
   * Limpia los filtros de busqueda, fecha y tipo.
   */
  const resetFilters = () => {
    search.value = '';
    dateFrom.value = '';
    dateTo.value = '';
    filterType.value = 'todos';
  };

  /**
   * Descarga los movimientos filtrados como archivo CSV.
   */
  const exportCsv = () => {
    const header = [
      'Fecha',
      'Artículo',
      'Tipo',
      'Cantidad',
      'Usuario',
      'Observación',
    ];
    const rows = filteredMovements.value.map((movement) => [
      movement.fecha_movimiento || '',
      itemName(movement.id_item),
      movementLabel(movement.tipo_movimiento),
      movement.cantidad,
      userName(movement.id_usuario),
      (movement.descripcion || '').replace(/"/g, "'"),
    ]);
    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${cell}"`).join(','))
      .join('\n');
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `movimientos-inventario-${limaDate()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  /**
   * Valida el formulario antes de enviarlo.
   */
  const validate = () => {
    errors.id_item = form.id_item ? '' : 'Selecciona un artículo de inventario.';
    errors.cantidad = '';
    try { parseQuantity(form.cantidad, { min: 1 }); }
    catch (error) { errors.cantidad = error.message; }
    return !errors.id_item && !errors.cantidad;
  };

  /**
   * Gestiona esta accion de la vista.
   */
  const save = async () => {
    if (isSaving.value || !validate()) return;
    isSaving.value = true;
    try {
      await gymStore.registrarMovimientoToServer({
        ...form,
        cantidad: parseQuantity(form.cantidad, { min: 1 }),
        id_usuario: authStore.user?.id_usuario || authStore.user?.id || 1,
      });
      feedbackTone.value = 'success';
      feedback.value = 'Movimiento registrado y stock actualizado.';
      Object.assign(form, {
        id_item: 0,
        tipo_movimiento: 'entrada',
        cantidad: 1,
        fecha_movimiento: limaDate(),
        descripcion: '',
      });
      visibleCount.value = pageSize;
    } catch (error) {
      feedbackTone.value = 'error';
      feedback.value =
        error instanceof Error
          ? error.message
          : 'No se pudo registrar el movimiento.';
    } finally {
      isSaving.value = false;
    }
  };

  watch([search, dateFrom, dateTo, filterType], () => {
    visibleCount.value = pageSize;
  });

  let feedbackTimeout = null;
  watch(feedback, (value) => {
    if (feedbackTimeout) clearTimeout(feedbackTimeout);
    if (!value || feedbackTone.value === 'error') return;
    feedbackTimeout = setTimeout(() => {
      feedback.value = '';
    }, 5000);
  });

  onBeforeUnmount(() => clearTimeout(feedbackTimeout));
  onMounted(() =>
    gymStore.fetchFromBackend?.({ section: 'inventory' }).catch(() => {
      feedbackTone.value = 'error';
      feedback.value =
        'No se pudo actualizar el inventario. Recarga la página para intentarlo de nuevo.';
    }),
  );

  return {
    authStore, gymStore, feedback, feedbackTone, isSaving,
    search, dateFrom, dateTo, filterType, visibleCount,
    pageSize, errors, inventory, activeInventory, movements,
    form, movementTypes, feedbackClass, itemId, itemName,
    userName, formatDate, movementLabel, movementIcon, movementClass,
    quantityClass, signedQuantity, dateInRange, baseFiltered, typeChips,
    filteredMovements, visibleMovements, hasActiveFilters, periodLabel, periodMovements,
    stats, selectedItem, resultingStock, stepCantidad, resetFilters,
    exportCsv, validate, save, feedbackTimeout,
  };
};
