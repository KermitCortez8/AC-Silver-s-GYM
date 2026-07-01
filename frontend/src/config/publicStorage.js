const normalizeBaseUrl = (value) => String(value || '').trim().replace(/\/$/, '');

const joinPath = (...segments) => segments
  .map((segment) => String(segment || '').trim().replace(/^\/+|\/+$/g, ''))
  .filter(Boolean)
  .join('/');

const encodeStoragePath = (path) => path
  .split('/')
  .map((segment) => encodeURIComponent(segment))
  .join('/');

const supabaseUrl = normalizeBaseUrl(import.meta.env.VITE_SUPABASE_URL);
const landingBucket = String(import.meta.env.VITE_SUPABASE_LANDING_BUCKET || 'imageneslandingpage').trim();
const landingFolder = String(import.meta.env.VITE_SUPABASE_LANDING_FOLDER || 'landingpage').trim();

export const publicStorageUrl = (bucket, path) => {
  const normalizedBucket = String(bucket || '').trim();
  const normalizedPath = joinPath(path);

  if (!supabaseUrl || !normalizedBucket || !normalizedPath) {
    return '';
  }

  return `${supabaseUrl}/storage/v1/object/public/${encodeURIComponent(normalizedBucket)}/${encodeStoragePath(normalizedPath)}`;
};

export const landingImageUrl = (fileName) => publicStorageUrl(
  landingBucket,
  joinPath(landingFolder, fileName),
);
