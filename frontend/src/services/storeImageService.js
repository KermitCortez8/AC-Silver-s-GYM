import { APP_CONFIG } from '../config/appConfig';
import { storeImageUrl } from '../config/publicStorage';

const apiBase = APP_CONFIG.authApiBaseUrl;

const parseErrorMessage = async (response) => {
  const message = await response.text();
  return message || 'No se pudo completar la operacion de imagenes';
};

export const listStoreImages = async () => {
  const response = await fetch(`${apiBase}/tienda/imagenes`);

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const images = await response.json();
  return Array.isArray(images) ? images : [];
};


export const uploadStoreImage = async (file) => {
  if (!file) {
    throw new Error('Selecciona una imagen');
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${apiBase}/tienda/imagenes`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
       throw new Error(await parseErrorMessage(response));
  }

const uploaded = await response.json();
  return {
    ...uploaded,
    url: uploaded.url || storeImageUrl(uploaded.path || uploaded.name),
  };
};

export { storeImageUrl };