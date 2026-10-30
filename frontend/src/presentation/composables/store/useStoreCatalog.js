import { feedbackClass as noticeClassFor } from '../../utils/feedback.js';
import { useProductEditor } from './useProductEditor.js';
import { computed, onMounted, ref } from 'vue';
import { useStoreFavorites } from './useStoreFavorites.js';
import { blockNonInteger } from '../../utils/inputGuards.js';
import { useAuthStore } from '../../../application/stores/authStore';
import { cleanInteger, DEFAULT_PAGE_SIZE, matchesSearch, sortRows, uniqueOptions } from '../../../domain/utils/inputRules.js';
import { useRoute, useRouter } from 'vue-router';
import { useGymStore } from '../../../application/stores/gymStore';

/** Coordina el catálogo, las cantidades del carrito y la edición de productos. */
export const useStoreCatalog = () => {
  const route = useRoute();
  const router = useRouter();
  const gymStore = useGymStore();

  const isAdmin = computed(() => route.path.startsWith('/admin/store'));
  const tabs = [
    { value: 'productos', label: 'Productos' },
    { value: 'ventas', label: 'Ventas' },
  ];
  // "movimientos" es el nombre anterior de la pestaña Ventas; los enlaces viejos siguen funcionando.
  const activeTab = computed({
    get: () => (['ventas', 'movimientos'].includes(route.query.tab) ? 'ventas' : 'productos'),
    set: (tab) => router.replace({ query: { ...route.query, tab } }),
  });
  const productos = computed(() => gymStore.productos_tienda);
  const productSearch = ref('');
  const categoryFilter = ref('');

  const catalogProducts = computed(() =>
    isAdmin.value
      ? productos.value
      // El cliente no ve productos descatalogados ni sin stock.
      : productos.value.filter((p) => p.estado !== 'Descatalogado' && Number(p.cantidad || 0) > 0),
  );
  const categories = computed(() =>
    [
      ...new Set(catalogProducts.value.map((p) => p.categoria || 'General')),
    ].sort(),
  );
  // El buscador del cliente mira el nombre y la categoria.
  const filteredProducts = computed(() => catalogProducts.value.filter((p) =>
    (!categoryFilter.value || (p.categoria || 'General') === categoryFilter.value)
    && matchesSearch(productSearch.value, [p.nombre, p.categoria || 'General'])
    && (!onlyFavorites.value || isFavorite(p.id_producto))));

  // Favoritos por usuario, guardados en este navegador.
  const authStore = useAuthStore();
  const favoriteOwner = computed(() => authStore.user?.id_usuario || authStore.user?.email || '');
  const { favoriteIds, isFavorite, toggleFavorite } = useStoreFavorites(favoriteOwner);
  const onlyFavorites = ref(false);
  const clientSort = ref('recomendados');
  const canBuy = (producto) => producto.estado === 'Disponible' && Number(producto.cantidad || 0) > 0;
  const CLIENT_SORTS = {
    nombre: (rows) => sortRows(rows, (p) => p.nombre),
    'precio-asc': (rows) => sortRows(rows, (p) => p.precio, 'asc', 'number'),
    'precio-desc': (rows) => sortRows(rows, (p) => p.precio, 'desc', 'number'),
    // Primero lo que se puede comprar, luego los favoritos.
    recomendados: (rows) => [...rows].sort((a, b) => Number(canBuy(b)) - Number(canBuy(a)) || Number(isFavorite(b.id_producto)) - Number(isFavorite(a.id_producto))),
  };
  const visibleProducts = computed(() => (CLIENT_SORTS[clientSort.value] || CLIENT_SORTS.recomendados)(filteredProducts.value));
  const hasClientFilters = computed(() => Boolean(productSearch.value || categoryFilter.value || onlyFavorites.value || clientSort.value !== 'recomendados'));
  const clearClientFilters = () => {
    productSearch.value = '';
    categoryFilter.value = '';
    onlyFavorites.value = false;
    clientSort.value = 'recomendados';
  };

  // Cantidades: solo enteros entre 1 y lo que queda disponible (stock menos lo que ya esta en el carrito).
  const blockQuantityChars = blockNonInteger();
  const inCart = (producto) => Number(gymStore.cart.find((item) => item.id_producto === producto?.id_producto)?.cantidad || 0);
  const availableFor = (producto) => Math.max(0, Number(producto?.cantidad || 0) - inCart(producto));
  const clampQuantity = (value, producto) => Math.max(1, Math.min(Number(value) || 1, availableFor(producto) || 1));
  const stockWarning = ref({});
  const warnStock = (producto, requested) => {
    const max = availableFor(producto);
    stockWarning.value[producto.id_producto] = Number(requested) > max
      ? `Solo hay ${max} disponible${max === 1 ? '' : 's'}${inCart(producto) ? ' (descontando tu carrito)' : ''}.`
      : '';
  };
  const setQuantity = (producto, event) => {
    const digits = cleanInteger(event.target.value);
    if (!digits) {
      event.target.value = '';
      cantidadInput.value[producto.id_producto] = '';
      return;
    }
    warnStock(producto, digits);
    const value = clampQuantity(digits, producto);
    event.target.value = String(value);
    cantidadInput.value[producto.id_producto] = value;
  };

  // Detalle del producto para el cliente.
  const clientDetail = ref(null);
  const detailQuantity = ref(1);
  const openClientDetail = (producto) => {
    clientDetail.value = producto;
    detailQuantity.value = 1;
  };
  const stepDetailQuantity = (delta) => {
    warnStock(clientDetail.value, detailQuantity.value + delta);
    detailQuantity.value = clampQuantity(detailQuantity.value + delta, clientDetail.value);
  };
  const setDetailQuantity = (event) => {
    const digits = cleanInteger(event.target.value);
    if (!digits) {
      event.target.value = '';
      return;
    }
    warnStock(clientDetail.value, digits);
    detailQuantity.value = clampQuantity(digits, clientDetail.value);
    event.target.value = String(detailQuantity.value);
  };
  const addDetailToCart = () => {
    const producto = clientDetail.value;
    if (!producto) return;
    cantidadInput.value[producto.id_producto] = detailQuantity.value;
    agregarAlCarrito(producto);
    clientDetail.value = null;
  };
  const inventario = computed(() => gymStore.inventory.filter((item) => !item.archived));
  const cart = computed(() => gymStore.cart);
  const cartItemStock = (item) => Number(productos.value.find((p) => p.id_producto === item.id_producto)?.cantidad ?? item.cantidad);
  const cartTotal = computed(() => gymStore.cartTotal);

  // Búsqueda y filtro por categoría
  const busqueda = ref('');
  const categoriaActiva = ref('');
  const filtroEstado = ref('');

  const categoriasUnicas = computed(() => {
    const cats = productos.value.map((p) => p.categoria || 'General').filter(Boolean);
    return [...new Set(cats)].sort();
  });

  // Paleta de colores para puntos de categorías
  const CATEGORY_COLORS = [
    '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
    '#ec4899', '#06b6d4', '#f97316', '#84cc16',
  ];
  function categoriaDotColor(cat) {
    const idx = categoriasUnicas.value.indexOf(cat);
    return CATEGORY_COLORS[idx % CATEGORY_COLORS.length] ?? '#94a3b8';
  }
  // Filtro "Stock bajo": productos que hay que reponer desde Inventario.
  // El enlace "Stock bajo" del Home llega con ?stock=bajo y abre la lista ya filtrada.
  const soloStockBajo = ref(route.query.stock === 'bajo');

  // Orden por columna: clic alterna ascendente y descendente.
  const sortKey = ref('');
  const sortDir = ref('asc');
  const SORT_COLUMNS = {
    code: { accessor: (p) => Number(p.id_producto || 0), type: 'number' },
    nombre: { accessor: (p) => p.nombre, type: 'text' },
    precio: { accessor: (p) => p.precio, type: 'number' },
    cantidad: { accessor: (p) => p.cantidad, type: 'number' },
  };
  const toggleSort = (column) => {
    sortDir.value = sortKey.value === column && sortDir.value === 'asc' ? 'desc' : 'asc';
    sortKey.value = column;
    paginaActual.value = 1;
  };
  const toggleStockBajo = () => {
    soloStockBajo.value = !soloStockBajo.value;
    paginaActual.value = 1;
  };

  const productosFiltrados = computed(() => {
    let lista = productos.value;
    if (soloStockBajo.value) {
      lista = lista.filter((p) => isProductLowStock(p));
    }
    if (categoriaActiva.value) {
      lista = lista.filter((p) => (p.categoria || 'General') === categoriaActiva.value);
    }
    if (filtroEstado.value) {
      lista = lista.filter((p) => p.estado === filtroEstado.value);
    }
    // El buscador solo mira el N° de producto y el nombre.
    lista = lista.filter((p) => matchesSearch(busqueda.value, [productCode(p.id_producto), p.nombre]));
    const column = SORT_COLUMNS[sortKey.value];
    return column ? sortRows(lista, column.accessor, sortDir.value, column.type) : lista;
  });

  // Paginación (sobre lista filtrada y ordenada)
  const paginaActual = ref(1);
  const porPagina = ref(DEFAULT_PAGE_SIZE);
  const productosPaginados = computed(() => productosFiltrados.value.slice((paginaActual.value - 1) * porPagina.value, paginaActual.value * porPagina.value));

  // Detalles de solo lectura del producto.
  const detailProduct = ref(null);
  const linkedItemName = (idItem) => {
    const item = findItem(idItem);
    return item ? `${item.inventoryCode} - ${item.name}` : `Item #${idItem}`;
  };
  // Desplegables extensibles del modal: valores existentes en la base + sugeridos.
  const productCategoryOptions = computed(() => uniqueOptions(productos.value.map((p) => p.categoria)));
  const productUnitOptions = computed(() => uniqueOptions(['Unidad', 'Paquete', 'Docena', 'Caja', 'Combo'], productos.value.map((p) => p.unidad_venta)));
  const editFromDetails = () => {
    const producto = detailProduct.value;
    detailProduct.value = null;
    if (producto) editProducto(producto);
  };

  const cantidadInput = ref({});
  const feedbackMessage = ref('');
  const feedbackTone = ref('info');

  const feedbackToneClass = computed(() => noticeClassFor(feedbackTone.value));

  const productCode = (id) => `PROD-${String(id || 0).padStart(4, '0')}`;

  // Items Tipo Tienda que todavia no tienen producto (el vinculo es 1:1).

  // Solo un producto nuevo acepta stock inicial; despues cambia con ventas y reposiciones.

  const isProductLowStock = (producto) => Number(producto.cantidad || 0) <= Number(producto.minimo || 0);

  const productStatusClass = (status) => {
    if (status === 'Disponible')
      return 'ws-border-success ws-tint-success ws-success';
    if (status === 'Agotado') return 'ws-border-danger ws-tint-danger ws-danger';
    return 'ws-border-warning ws-tint-warning ws-warning';
  };

  const productStatusDot = (status) => {
    if (status === 'Disponible') return 'bg-emerald-400';
    if (status === 'Agotado') return 'bg-rose-400';
    return 'bg-orange-400';
  };

  const stockBarColor = (producto) => {
    const cantidad = Number(producto.cantidad || 0);
    const minimo = Number(producto.minimo ?? 1);
    if (cantidad <= minimo) return 'bg-rose-400';
    if (cantidad <= minimo * 2) return 'bg-orange-400';
    return 'bg-emerald-400';
  };

  const deleteProducto = async (idProducto) => {
    if (!window.confirm('¿Eliminar este producto?\n\nSi ya tiene ventas no se borrará: se archivará (deja de mostrarse y venderse) y sus ventas se conservan.')) return;
    try {
      const result = await gymStore.deleteProductoTienda(idProducto);
      feedbackTone.value = 'success';
      feedbackMessage.value = result?.accion === 'archivado'
        ? 'El producto tiene ventas registradas: se archivó y sus ventas se conservan.'
        : 'Producto eliminado.';
    } catch (error) {
      feedbackTone.value = 'error';
      feedbackMessage.value =
        error instanceof Error
          ? error.message
          : 'No se pudo eliminar el producto.';
    }
  };

  const cartError = (error) => {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo actualizar el carrito.';
  };
  // En el carrito un numero mayor al stock se ajusta al maximo y se avisa.
  const updateCart = (id, quantity) => {
    const item = cart.value.find((entry) => entry.id_producto === id);
    const max = item ? cartItemStock(item) : Infinity;
    if (/^[0-9]+$/.test(String(quantity)) && Number(quantity) > max) {
      quantity = max;
      feedbackTone.value = 'error';
      feedbackMessage.value = `Solo hay ${max} disponible${max === 1 ? '' : 's'} de ${item.nombre}.`;
    }
    try { gymStore.updateCartQuantity(id, quantity); }
    catch (error) { cartError(error); }
  };
  const agregarAlCarrito = (producto) => {
    if (!availableFor(producto)) {
      feedbackTone.value = 'error';
      feedbackMessage.value = `Ya tienes en el carrito todo el stock de ${producto.nombre}.`;
      return;
    }
    stockWarning.value[producto.id_producto] = '';
    try {
      gymStore.addToCart(producto, cantidadInput.value[producto.id_producto] ?? 1);
      cantidadInput.value[producto.id_producto] = 1;
      feedbackTone.value = 'success';
      feedbackMessage.value = `${producto.nombre} añadido al carrito.`;
    } catch (error) { cartError(error); }
  };

  const goToCheckout = () => {
    if (!cart.value.length) return;
    router.push('/user/store/payment');
  };

  const { isSaving, editingId, isProductEditorOpen, form, formErrors: productFormErrors, currentProductCode, itemNumber, findItem, availableTiendaItems, editingLinked, linkedItemLabel, stockEditable, stockMostrado, resetForm, openNewProducto, closeProductEditor, editProducto, handleSubmit, imageFeedback, imageFeedbackTone, isUploadingImage, isBucketPickerOpen, isLoadingBucketImages, bucketImages, loadBucketImages, openBucketPicker, closeBucketPicker, selectBucketImage, clearSelectedImage, handleLocalImageUpload } = useProductEditor({ gymStore, productos, inventario, feedbackMessage, feedbackTone, productCode });

  onMounted(() => {
    gymStore
      .fetchFromBackend?.({ section: 'store' })
      .catch((error) => console.warn('No se pudo refrescar tienda:', error));
  });

  return {
    route, router, gymStore, isAdmin, tabs,
    activeTab, productos, productSearch, categoryFilter, catalogProducts,
    categories, filteredProducts, authStore, favoriteOwner, favoriteIds,
    isFavorite, toggleFavorite, onlyFavorites, clientSort, canBuy,
    CLIENT_SORTS, visibleProducts, hasClientFilters, clearClientFilters, blockQuantityChars,
    inCart, availableFor, clampQuantity, stockWarning, warnStock,
    setQuantity, clientDetail, detailQuantity, openClientDetail, stepDetailQuantity,
    setDetailQuantity, addDetailToCart, inventario, cart, cartItemStock,
    cartTotal, busqueda, categoriaActiva, filtroEstado, categoriasUnicas,
    CATEGORY_COLORS, categoriaDotColor, soloStockBajo, sortKey, sortDir,
    SORT_COLUMNS, toggleSort, toggleStockBajo, productosFiltrados, paginaActual,
    porPagina, productosPaginados, detailProduct, linkedItemName, productCategoryOptions,
    productUnitOptions, editFromDetails, cantidadInput, feedbackMessage, feedbackTone,
    feedbackToneClass, productCode, isProductLowStock, productStatusClass, productStatusDot,
    stockBarColor, deleteProducto, cartError, updateCart, agregarAlCarrito,
    goToCheckout, isSaving, editingId, isProductEditorOpen, form,
    productFormErrors, currentProductCode, itemNumber, findItem, availableTiendaItems,
    editingLinked, linkedItemLabel, stockEditable, stockMostrado, resetForm,
    openNewProducto, closeProductEditor, editProducto, handleSubmit, imageFeedback,
    imageFeedbackTone, isUploadingImage, isBucketPickerOpen, isLoadingBucketImages, bucketImages,
    loadBucketImages, openBucketPicker, closeBucketPicker, selectBucketImage, clearSelectedImage,
    handleLocalImageUpload,
  };
};
