import { APP_CONFIG } from '../config/appConfig';
import { storeImageUrl } from '../config/publicStorage';

const apiBase = APP_CONFIG.authApiBaseUrl;

import { parseError } from './apiResponse.js';

export const listStoreImages = async () => {
  const response = await fetch(`${apiBase}/tienda/imagenes`);

  if (!response.ok) {
    throw await parseError(response);
  }

  const images = await response.json();
  return Array.isArray(images) ? images : [];
};


export const uploadStoreImage = async (file, token = '') => {
  if (!file) {
    throw new Error('Selecciona una imagen');
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${apiBase}/tienda/imagenes`, {
    method: 'POST',
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

export { storeImageUrl };