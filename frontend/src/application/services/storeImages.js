import { useAuthStore } from "../stores/authStore.js";
import { getApplicationServices } from "../ports/services.js";

export const useStoreImages = () => {
  const { images, storage } = getApplicationServices();
  const auth = useAuthStore();
  return {
    listStoreImages: (...args) => images.listStoreImages(...args),
    uploadStoreImage: (file) => images.uploadStoreImage(file, auth.token),
    storeImageUrl: storage.storeImageUrl,
  };
};
