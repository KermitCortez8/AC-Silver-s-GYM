export const INVENTORY_CATEGORIES = ['General', 'Tienda', 'Equipo de fuerza', 'Equipo cardiovascular', 'Accesorios', 'Limpieza'];
export const INVENTORY_LOCATIONS = ['Recepcion', 'Almacén', 'Sala 1', 'Sala de fuerza', 'Sala de cardio', 'Tienda'];
export const INVENTORY_UNITS = ['unidad', 'botella', 'paquete', 'caja', 'par', 'juego'];

// Keep legacy and custom values selectable while offering useful defaults on an empty inventory.
export const inventoryOptions = (defaults, values, current) =>
  [...new Set([...defaults, ...values, current].filter(Boolean))].sort((a, b) => a.localeCompare(b, 'es'));
