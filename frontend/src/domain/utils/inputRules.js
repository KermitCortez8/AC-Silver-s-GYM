/** Reglas de entrada compartidas por Inventario y Tienda (TP2). */

export const SEARCH_MAX_LENGTH = 40;
export const NAME_MAX_LENGTH = 80;
export const PAGE_SIZES = [8, 16, 24, 50];
export const DEFAULT_PAGE_SIZE = 8;

// Letras (con tildes y ñ), números y espacio.
const TEXT_CHAR = /[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ ]/;
const DISALLOWED_TEXT = /[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ ]/g;

/**
 * Limpia un texto libre: quita caracteres especiales y corta al maximo.
 * Devuelve el valor limpio y si hubo que rechazar algo.
 */
export const cleanText = (value, maxLength = SEARCH_MAX_LENGTH) => {
  const raw = String(value ?? '');
  const filtered = raw.replace(DISALLOWED_TEXT, '');
  const result = filtered.slice(0, maxLength);
  return { value: result, rejected: filtered !== raw, truncated: filtered.length > maxLength };
};

/** Indica si el texto que se va a insertar solo tiene caracteres permitidos. */
export const isAllowedText = (text) => [...String(text ?? '')].every((char) => TEXT_CHAR.test(char));

/** Solo digitos: para stock y cantidades enteras positivas. */
export const cleanInteger = (value) => String(value ?? '').replace(/\D/g, '');
export const isAllowedInteger = (text) => /^\d*$/.test(String(text ?? ''));

/** Digitos con un solo punto decimal y como maximo dos decimales: para precios. */
export const cleanDecimal = (value) => {
  const digits = String(value ?? '').replace(/[^\d.]/g, '');
  const [whole, ...rest] = digits.split('.');
  return rest.length ? `${whole}.${rest.join('').slice(0, 2)}` : whole;
};
export const isAllowedDecimal = (text) => /^[\d.]*$/.test(String(text ?? ''));

/** Compara sin tildes ni mayusculas. */
export const normalizeSearch = (value) => String(value ?? '')
  .normalize('NFD')
  .replace(/[̀-ͯ]/g, '')
  .toLowerCase()
  .trim();

/**
 * Busca la consulta en los campos indicados. Los codigos se comparan tambien
 * sin guiones, para que "ACT 0001" o "0001" encuentren "ACT-0001".
 */
export const matchesSearch = (query, fields) => {
  const needle = normalizeSearch(query);
  if (!needle) return true;
  const compactNeedle = needle.replace(/\s+/g, '');
  return fields.some((field) => {
    const haystack = normalizeSearch(field);
    return haystack.includes(needle) || haystack.replace(/[^a-z0-9]/g, '').includes(compactNeedle);
  });
};

/**
 * Ordena filas por una columna de texto (A-Z) o numerica.
 * No modifica el arreglo original.
 */
export const sortRows = (rows, accessor, direction = 'asc', type = 'text') => {
  const factor = direction === 'desc' ? -1 : 1;
  const collator = new Intl.Collator('es', { sensitivity: 'base', numeric: true });
  return [...rows].sort((a, b) => {
    const left = accessor(a);
    const right = accessor(b);
    if (type === 'number') return (Number(left || 0) - Number(right || 0)) * factor;
    return collator.compare(String(left ?? ''), String(right ?? '')) * factor;
  });
};

/** Devuelve las etiquetas de los campos obligatorios que estan vacios. */
export const missingFields = (values, required) => required
  .filter(({ key, isEmpty }) => (isEmpty ? isEmpty(values[key]) : String(values[key] ?? '').trim() === ''))
  .map(({ label }) => label);

/** Mensaje para avisar exactamente que campos faltan. */
export const missingFieldsMessage = (labels) => {
  if (!labels.length) return '';
  if (labels.length === 1) return `Falta completar el campo: ${labels[0]}.`;
  return `Faltan completar los campos: ${labels.slice(0, -1).join(', ')} y ${labels[labels.length - 1]}.`;
};

// La galeria de Tienda solo admite PNG y JPG (el backend aplica la misma regla).
const IMAGE_TYPES = { '.png': ['image/png'], '.jpg': ['image/jpeg'], '.jpeg': ['image/jpeg'] };
export const ALLOWED_IMAGE_MESSAGE = 'Formato no permitido. Solo se aceptan imágenes .png y .jpg.';

/** Acepta el archivo solo si su extension y su tipo son PNG o JPG. */
export const isAllowedImageFile = (file) => {
  const name = String(file?.name || '').toLowerCase();
  const extension = name.includes('.') ? name.slice(name.lastIndexOf('.')) : '';
  const types = IMAGE_TYPES[extension];
  return Boolean(types && (!file.type || types.includes(String(file.type).toLowerCase())));
};

/** Valores unicos, ordenados y sin vacios, para los desplegables extensibles. */
export const uniqueOptions = (...lists) => {
  const seen = new Map();
  lists.flat().forEach((value) => {
    const text = String(value ?? '').trim();
    if (text && !seen.has(normalizeSearch(text))) seen.set(normalizeSearch(text), text);
  });
  return [...seen.values()].sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }));
};
