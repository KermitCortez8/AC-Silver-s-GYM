import { APP_CONFIG, DEFAULT_SUPABASE_STORE_IMAGES_BUCKET } from '../config/appConfig';

const storageBaseUrl = `${APP_CONFIG.supabaseUrl}/storage/v1`;
export const storeImagesBucketName =
  APP_CONFIG.supabaseStoreImagesBucket || DEFAULT_SUPABASE_STORE_IMAGES_BUCKET;

const authHeaders = () => ({
  apikey: APP_CONFIG.supabaseAnonKey,
  Authorization: `Bearer ${APP_CONFIG.supabaseAnonKey}`,
});

const assertStorageConfig = () => {
  if (!APP_CONFIG.supabaseUrl || !APP_CONFIG.supabaseAnonKey) {
    throw new Error('Supabase Storage no esta configurado');
  }
};

export const getStoreImagePublicUrl = (path) => {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  return `${storageBaseUrl}/object/public/${storeImagesBucketName}/${encodeURIComponent(path)}`;
};

export const listStoreImages = async () => {
  assertStorageConfig();
  const response = await fetch(`${storageBaseUrl}/object/list/${storeImagesBucketName}`, {
    method: 'POST',
    headers: {
      ...authHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      limit: 100,
      offset: 0,
      sortBy: { column: 'created_at', order: 'desc' },
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'No se pudieron cargar imagenes del bucket');
  }

  const data = await response.json();
  return (Array.isArray(data) ? data : [])
    .filter((item) => item.name && !item.name.endsWith('/'))
    .map((item) => ({
      name: item.name,
      path: item.name,
      url: getStoreImagePublicUrl(item.name),
      size: item.metadata?.size || 0,
      updatedAt: item.updated_at || item.created_at || '',
    }));
};

export const uploadStoreImage = async (file) => {
  assertStorageConfig();
  if (!file) {
    throw new Error('Selecciona una imagen');
  }

  const extension = file.name.includes('.') ? file.name.split('.').pop().toLowerCase() : 'jpg';
  const safeName =
    file.name
      .replace(/\.[^/.]+$/, '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-zA-Z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .toLowerCase() || 'producto';
  const path = `${safeName}-${Date.now()}.${extension}`;

  const response = await fetch(`${storageBaseUrl}/object/${storeImagesBucketName}/${encodeURIComponent(path)}`, {
    method: 'POST',
    headers: {
      ...authHeaders(),
      'Content-Type': file.type || 'image/jpeg',
      'x-upsert': 'false',
    },
    body: file,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'No se pudo subir la imagen');
  }

  return {
    name: file.name,
    path,
    url: getStoreImagePublicUrl(path),
  };
};
