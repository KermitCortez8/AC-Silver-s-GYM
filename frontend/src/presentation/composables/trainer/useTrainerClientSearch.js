import { computed, nextTick, ref } from 'vue';
export const useTrainerClientSearch = ({
  overview,
  loadOverview,
  loadClient,
  feedback,
  setFeedback,
  showToast,
  onSearchStart,
}) => {
  const dni = ref('');
  const clientData = ref(null);
  const searching = ref(false);
  const isSearching = computed(() => searching.value);
  const open = ref(false);
  const activeIndex = ref(-1);
  const activeClients = computed(() => {
    const seen = new Map();
    for (const row of overview.value.schedule_monitor || []) {
      const clientDni = String(row.cliente_dni || '').trim();
      if (clientDni && !seen.has(clientDni)) {
        seen.set(clientDni, {
          dni: clientDni,
          nombre: row.cliente_nombre || 'Cliente',
        });
      }
    }
    return [...seen.values()].sort((a, b) => a.nombre.localeCompare(b.nombre));
  });
  const suggestions = computed(() => {
    const prefix = dni.value.trim();
    return activeClients.value
      .filter((client) => client.dni.startsWith(prefix))
      .slice(0, 50);
  });
  const showSuggestions = computed(
    () => open.value && (suggestions.value.length > 0 || dni.value.length > 0),
  );
  const onDniInput = () => {
    dni.value = dni.value.replace(/\D/g, '').slice(0, 8);
    feedback.value = '';
    open.value = true;
    activeIndex.value = -1;
  };
  const openSuggestions = () => {
    open.value = true;
    activeIndex.value = -1;
  };
  const onDniBlur = (event) => {
    // En móvil el desplegable ocupa espacio. Cerrarlo al enfocar el botón
    // lo desplazaría entre pointerdown y click, impidiendo enviar el formulario.
    if (!event.currentTarget.form?.contains(event.relatedTarget)) {
      open.value = false;
    }
  };
  const moveActive = (step) => {
    open.value = true;
    const total = suggestions.value.length;
    if (!total) return;
    activeIndex.value =
      activeIndex.value < 0
        ? step > 0
          ? 0
          : total - 1
        : (activeIndex.value + step + total) % total;
    nextTick(() =>
      document
        .getElementById(`dni-option-${activeIndex.value}`)
        ?.scrollIntoView({ block: 'nearest' }),
    );
  };
  const onEnter = (event) => {
    if (
      showSuggestions.value &&
      activeIndex.value >= 0 &&
      suggestions.value[activeIndex.value]
    ) {
      event.preventDefault();
      pickClient(suggestions.value[activeIndex.value].dni);
    }
  };
  const pickClient = (value) => {
    dni.value = value;
    open.value = false;
    searchClient();
  };
  const searchClient = async () => {
    if (searching.value) return;
    open.value = false;
    const query = dni.value.trim();
    if (!/^\d{8}$/.test(query)) {
      setFeedback(
        'Ingresa un DNI válido de 8 dígitos o selecciona una sugerencia.',
        'error',
      );
      return;
    }
    searching.value = true;
    feedback.value = '';
    clientData.value = null;
    onSearchStart();
    try {
      const [, client] = await Promise.all([loadOverview(), loadClient(query)]);
      if (!client?.cliente)
        throw new Error('No se encontró información del cliente.');
      clientData.value = client;

      showToast(`Cliente ${client.cliente.nombre} cargado exitosamente.`);
    } catch (error) {
      clientData.value = null;
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo buscar el cliente.';
      setFeedback(message, 'error');
      showToast(message, 'error');
    } finally {
      searching.value = false;
    }
  };
  const reloadClient = async () => {
    if (!dni.value.trim()) return;
    clientData.value = await loadClient(dni.value.trim());
  };
  return {
    dni,
    clientData,
    searching,
    isSearching,
    open,
    activeIndex,
    suggestions,
    showSuggestions,
    onDniInput,
    onDniBlur,
    openSuggestions,
    moveActive,
    onEnter,
    pickClient,
    searchClient,
    reloadClient,
  };
};
