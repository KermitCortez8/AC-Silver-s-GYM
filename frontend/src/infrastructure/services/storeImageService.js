import { APP_CONFIG } from "../config/appConfig";
import { storeImageUrl } from "../config/publicStorage";
import { parseError } from "./apiResponse.js";

export const createStoreImageService = (
  config = APP_CONFIG,
  imageUrl = storeImageUrl,
) => {
  const apiBase = config.authApiBaseUrl;
  const storeImageUrl = imageUrl;
  const listStoreImages = async () => {
    const response = await fetch(`${apiBase}/tienda/imagenes`);

    if (!response.ok) {
      throw await parseError(response);
    }

    const images = await response.json();
    return Array.isArray(images) ? images : [];
  };

  const uploadStoreImage = async (file, token = "") => {
    if (!file) {
      throw new Error("Selecciona una imagen");
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${apiBase}/tienda/imagenes`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      throw await parseError(response);
    }

    const uploaded = await response.json();
    return {
      ...uploaded,
      url: uploaded.url || storeImageUrl(uploaded.path || uploaded.name),
    };
  };

  return { listStoreImages, uploadStoreImage, storeImageUrl };
};

export const { listStoreImages, uploadStoreImage } = createStoreImageService();
export { storeImageUrl };
