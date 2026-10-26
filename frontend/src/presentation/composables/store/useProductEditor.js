import { computed, reactive, ref } from "vue";
import { useStoreImagePicker } from "./useStoreImagePicker.js";

export const useProductEditor = ({
  gymStore,
  productos,
  inventario,
  feedbackMessage,
  feedbackTone,
  productCode,
}) => {
  const isSaving = ref(false);

  const editingId = ref("");

  const isProductEditorOpen = ref(false);

  const form = reactive({
    nombre: "",
    descripcion: "",
    categoria: "General",
    id_item: null,
    unidad_venta: "unidad",
    precio: 0,
    cantidad: 0,
    minimo: 5,
    estado: "Disponible",
    imagen_url: "",
  });

  const {
    imageFeedback,
    imageFeedbackTone,
    isUploadingImage,
    isBucketPickerOpen,
    isLoadingBucketImages,
    bucketImages,
    loadBucketImages,
    openBucketPicker,
    closeBucketPicker,
    selectBucketImage,
    clearSelectedImage,
    handleLocalImageUpload,
  } = useStoreImagePicker({ form });

  const currentProductCode = computed(() => {
    if (editingId.value) {
      return productCode(editingId.value);
    }
    return "Se generara automaticamente";
  });

  const itemNumber = (item) => Number(String(item.id).replace("item-", ""));

  const findItem = (idItem) =>
    inventario.value.find((item) => itemNumber(item) === Number(idItem)) ||
    null;

  const availableTiendaItems = computed(() => {
    const vinculados = new Set(
      productos.value
        .filter((p) => p.id_item && p.id_producto !== editingId.value)
        .map((p) => Number(p.id_item)),
    );
    return inventario.value.filter(
      (item) =>
        String(item.category || "")
          .trim()
          .toLowerCase() === "tienda" && !vinculados.has(itemNumber(item)),
    );
  });

  const editingLinked = computed(() =>
    Boolean(
      editingId.value &&
      productos.value.find((p) => p.id_producto === editingId.value)?.id_item,
    ),
  );

  const linkedItemLabel = computed(() => {
    const item = findItem(form.id_item);
    return item
      ? `${item.inventoryCode} - ${item.name}`
      : `Item #${form.id_item}`;
  });

  const stockEditable = computed(() => !editingId.value);

  const stockMostrado = computed(() => Number(form.cantidad || 0));

  const resetForm = () => {
    editingId.value = "";
    form.nombre = "";
    form.descripcion = "";
    form.categoria = "General";
    form.id_item = null;
    form.unidad_venta = "unidad";
    form.precio = 0;
    form.cantidad = 0;
    form.minimo = 5;
    form.estado = "Disponible";
    form.imagen_url = "";
    imageFeedback.value = "";
    isBucketPickerOpen.value = false;
    bucketImages.value = [];
  };

  const openNewProducto = () => {
    resetForm();
    feedbackMessage.value = "";
    isProductEditorOpen.value = true;
  };

  const closeProductEditor = () => {
    if (isSaving.value || isUploadingImage.value) return;
    isProductEditorOpen.value = false;
    resetForm();
  };

  const editProducto = (producto) => {
    editingId.value = producto.id_producto;
    form.nombre = producto.nombre;
    form.descripcion = producto.descripcion || "";
    form.categoria = producto.categoria || "General";
    form.id_item = producto.id_item || null;
    form.unidad_venta = producto.unidad_venta || "unidad";
    form.precio = Number(producto.precio || 0);
    form.cantidad = Number(producto.cantidad || 0);
    form.minimo = Number(producto.minimo ?? 5);
    form.estado = producto.estado || "Disponible";
    form.imagen_url = producto.imagen_url || "";
    feedbackMessage.value = "";
    imageFeedback.value = "";
    isBucketPickerOpen.value = false;
    isProductEditorOpen.value = true;
  };

  const handleSubmit = async () => {
    if (isSaving.value || isUploadingImage.value) return;
    isSaving.value = true;
    feedbackMessage.value = "";
    try {
      await gymStore.upsertProductoTienda({
        id_producto: editingId.value || undefined,
        nombre: form.nombre,
        descripcion: form.descripcion,
        categoria: form.categoria,
        id_item: form.id_item || null,
        unidad_venta: form.unidad_venta,
        precio: form.precio,
        cantidad: form.cantidad,
        minimo: form.minimo,
        estado: form.estado,
        imagen_url: form.imagen_url,
      });
      const savedLabel = editingId.value
        ? "Producto actualizado."
        : "Producto registrado.";
      isSaving.value = false;
      closeProductEditor();
      feedbackTone.value = "success";
      feedbackMessage.value = savedLabel;
    } catch (error) {
      feedbackTone.value = "error";
      feedbackMessage.value =
        error instanceof Error
          ? error.message
          : "No se pudo guardar el producto.";
    } finally {
      isSaving.value = false;
    }
  };

  return {
    isSaving,
    editingId,
    isProductEditorOpen,
    form,
    currentProductCode,
    itemNumber,
    findItem,
    availableTiendaItems,
    editingLinked,
    linkedItemLabel,
    stockEditable,
    stockMostrado,
    resetForm,
    openNewProducto,
    closeProductEditor,
    editProducto,
    handleSubmit,
    imageFeedback,
    imageFeedbackTone,
    isUploadingImage,
    isBucketPickerOpen,
    isLoadingBucketImages,
    bucketImages,
    loadBucketImages,
    openBucketPicker,
    closeBucketPicker,
    selectBucketImage,
    clearSelectedImage,
    handleLocalImageUpload,
  };
};
