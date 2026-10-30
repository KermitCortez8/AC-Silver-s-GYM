import { APP_CONFIG } from "../config/appConfig";
import { storeImageUrl } from "../config/publicStorage";
import { parseError, parseResponse } from "./apiResponse.js";
import { fetchWithTimeout } from "./httpTransport.js";

export const createStoreImageService = (
  config = APP_CONFIG,
  imageUrl = storeImageUrl,
) => {
  const apiBase = config.authApiBaseUrl;
  const storeImageUrl = imageUrl;
  const listStoreImages = async () => {
    const response = await fetchWithTimeout(`${apiBase}/tienda/imagenes`, {}, config.requestTimeoutMs);

    if (!response.ok) {
      throw await parseError(response);
    }

    const images = await parseResponse(response);
    if (!Array.isArray(images) || images.some(image => !image || typeof image.url !== 'string' || !image.url)) {
      throw new Error('El servidor devolvió una galería de imágenes inválida. Inténtalo de nuevo.');
    }
    return images;
  };

  const uploadStoreImage = async (file, token = "") => {
    if (!file) {
      throw new Error("Selecciona una imagen");
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchWithTimeout(`${apiBase}/tienda/imagenes`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    }, config.requestTimeoutMs);

    if (!response.ok) {
      throw await parseError(response);
    }

    const uploaded = await parseResponse(response);
    if (!uploaded || typeof uploaded !== 'object' || Array.isArray(uploaded)
      || !(uploaded.url || uploaded.path || uploaded.name)) {
      throw new Error('El servidor no confirmó la imagen subida. Actualiza la galería antes de repetir la operación.');
    }
    return {
      ...uploaded,
      url: uploaded.url || storeImageUrl(uploaded.path || uploaded.name),
    };
  };

  return { listStoreImages, uploadStoreImage, storeImageUrl };
};

export const { listStoreImages, uploadStoreImage } = createStoreImageService();
export { storeImageUrl };
