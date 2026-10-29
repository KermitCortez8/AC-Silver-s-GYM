import { amountError, requiredTextError } from "../../../domain/utils/formValidation.js";
import { parseQuantity } from "../../../domain/utils/quantities.js";
import { computed, reactive, ref } from "vue";
import { useStoreImagePicker } from "./useStoreImagePicker.js";
import { missingFields, missingFieldsMessage } from "../../../domain/utils/inputRules.js";

const isBlank = (value) => String(value ?? "").trim() === "";
// Obligatorios del TP2: nombre, categoria, precio y stock inicial (solo al crear).
const requiredProductFields = (creating) => [
  { key: "nombre", label: "Nombre" },
  { key: "categoria", label: "Categoria" },
  { key: "precio", label: "Precio", isEmpty: (value) => isBlank(value) || !(Number(value) > 0) },
  ...(creating
    ? [{ key: "cantidad", label: "Stock inicial", isEmpty: (value) => isBlank(value) || !Number.isInteger(Number(value)) }]
    : []),
];

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

  const formErrors = ref([]);

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
    formErrors.value = [];
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
    formErrors.value = [];
    imageFeedback.value = "";
    isBucketPickerOpen.value = false;
    isProductEditorOpen.value = true;
  };

  const handleSubmit = async () => {
    if (isSaving.value || isUploadingImage.value) return;
    formErrors.value = missingFields(form, requiredProductFields(!editingId.value));
    if (formErrors.value.length) {
      feedbackTone.value = "error";
      feedbackMessage.value = missingFieldsMessage(formErrors.value);
      return;
    }
    isSaving.value = true;
    feedbackMessage.value = "";
    try {
      const invalid = requiredTextError(form.nombre, 'El nombre del producto') || amountError(form.precio);
      if (invalid) throw new Error(invalid);
      await gymStore.upsertProductoTienda({
        id_producto: editingId.value || undefined,
        nombre: String(form.nombre).trim(),
        descripcion: form.descripcion,
        categoria: form.categoria,
        id_item: form.id_item || null,
        unidad_venta: form.unidad_venta,
        precio: Number(form.precio),
        cantidad: parseQuantity(form.cantidad, { label: "El stock inicial" }),
        minimo: parseQuantity(form.minimo, { label: "El stock mínimo" }),
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
    formErrors,
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
