import { parseQuantity } from './quantities.js';

export const MIN_PAGE_SIZE = 1;
export const MAX_PAGE_SIZE = 100;

/** Devuelve el tamaño de página válido (1 a 100) o null si el valor no es un entero. */
export const parsePageSize = (value) => {
  try {
    return Math.min(parseQuantity(value, { min: MIN_PAGE_SIZE }), MAX_PAGE_SIZE);
  } catch {
    return null;
  }
};

/** Sube o baja el tamaño de página sin salir del rango permitido. */
export const stepPageSize = (current, delta) => {
  const base = parsePageSize(current) ?? MIN_PAGE_SIZE;
  return Math.min(MAX_PAGE_SIZE, Math.max(MIN_PAGE_SIZE, base + delta));
};

/** Ajusta la página a una que exista. */
export const clampPage = (page, totalPages) =>
  Math.min(Math.max(1, Number(page) || 1), Math.max(1, totalPages));

/** Clave propia de cada tabla: pageSizeStorageKey('inventory') -> 'acsg:pageSize:inventory'. */
export const pageSizeStorageKey = (table) => `acsg:pageSize:${table}`;

/** Lee el tamaño guardado de una tabla; devuelve null si no hay clave, no hay valor, es inválido o el almacenamiento falla. */
export const readStoredPageSize = (storage, key) => {
  if (!key) return null;
  try {
    return parsePageSize(storage?.getItem(key));
  } catch {
    return null;
  }
};

/** Guarda el tamaño de una tabla; sin clave o con almacenamiento no disponible no hace nada. */
export const storePageSize = (storage, size, key) => {
  if (!key) return;
  try {
    storage?.setItem(key, String(size));
  } catch {
    /* modo privado o cuota llena: se usa el valor solo en esta sesión */
  }
};