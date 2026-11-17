/** Reglas del N° de activo por unidad (equipos y accesorios); las mismas del backend y la migración 026. */

export const UNIT_STATUSES = ['Operativo', 'En mantenimiento', 'Fuera de servicio'];
export const RETIRED_UNIT_STATUS = 'Dado de baja';

const STOP_WORDS = new Set(['de', 'del', 'la', 'las', 'el', 'los', 'para', 'por', 'con', 'y', 'a', 'al', 'en', 'un', 'una']);

/** Solo las categorías que empiezan con "Equipo" o "Accesorio" llevan número por unidad. */
export const isUnitCategory = (category) => {
  const value = String(category ?? '').trim().toLowerCase();
  return value.startsWith('equipo') || value.startsWith('accesorio');
};

/** Iniciales de las dos primeras palabras significativas: "Maquina para correr" -> "MC". */
export const unitPrefix = (name) => {
  const words = String(name ?? '')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .split(/[^a-z]+/)
    .filter((word) => word && !STOP_WORDS.has(word));
  if (!words.length) return 'AC';
  if (words.length === 1) return words[0].slice(0, 2).padEnd(2, 'x').toUpperCase();
  return `${words[0][0]}${words[1][0]}`.toUpperCase();
};

export const isActiveUnit = (unit) => unit?.estado !== RETIRED_UNIT_STATUS;
