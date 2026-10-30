import { computed, reactive, ref } from "vue";
import { useStoreImages } from "../../../application/services/storeImages.js";
import { ALLOWED_IMAGE_MESSAGE, isAllowedImageFile } from "../../../domain/utils/inputRules.js";

export const useStoreImagePicker = ({ form }) => {
  const { uploadStoreImage, listStoreImages } = useStoreImages();
  const imageFeedback = ref("");

  const imageFeedbackTone = ref("success");

  const isUploadingImage = ref(false);

  const isBucketPickerOpen = ref(false);

  const isLoadingBucketImages = ref(false);

  const bucketImages = ref([]);

  const loadBucketImages = async () => {
    if (isLoadingBucketImages.value) return;
    imageFeedback.value = '';
    isLoadingBucketImages.value = true;
    try {
      bucketImages.value = await listStoreImages();
    } catch (error) {
      imageFeedbackTone.value = "error";
      imageFeedback.value =
        error instanceof Error
          ? error.message
          : "No se pudieron cargar las imágenes del bucket.";
    } finally {
      isLoadingBucketImages.value = false;
    }
  };

  const openBucketPicker = async () => {
    isBucketPickerOpen.value = true;
    if (!bucketImages.value.length) {
      await loadBucketImages();
    }
  };

  const closeBucketPicker = () => {
    isBucketPickerOpen.value = false;
  };

  const selectBucketImage = (image) => {
    form.imagen_url = image.url;
    imageFeedbackTone.value = "success";
    imageFeedback.value = `Imagen seleccionada: ${image.name}`;
    isBucketPickerOpen.value = false;
  };

  const clearSelectedImage = () => {
    form.imagen_url = "";
    imageFeedback.value = "";
  };

  const handleLocalImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!isAllowedImageFile(file)) {
      imageFeedbackTone.value = "error";
      imageFeedback.value = ALLOWED_IMAGE_MESSAGE;
      event.target.value = "";
      return;
    }

    isUploadingImage.value = true;
    imageFeedback.value = "";
    try {
      const uploaded = await uploadStoreImage(file);
      form.imagen_url = uploaded.url;
      imageFeedbackTone.value = "success";
      imageFeedback.value = "Imagen subida correctamente.";
    } catch (error) {
      imageFeedbackTone.value = "error";
      imageFeedback.value =
        error instanceof Error ? error.message : "No se pudo subir la imagen.";
    } finally {
      isUploadingImage.value = false;
      event.target.value = "";
    }
  };

  return {
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
