import { APP_CONFIG } from '../config/appConfig';

export const uploadStoreImage = async (file) => {
  if (!file) {
    throw new Error('Selecciona una imagen');
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${APP_CONFIG.authApiBaseUrl}/tienda/imagenes`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'No se pudo subir la imagen');
  }

  return response.json();
};
