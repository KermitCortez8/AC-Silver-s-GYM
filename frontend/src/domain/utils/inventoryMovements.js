// Presentación común de los movimientos de inventario (tabla de Movimientos y detalle del artículo).

export const TRANSFER_TYPE = 'traslado';

// Cantidad con signo según su efecto en el stock; el traslado no cambia el stock.
export const signedQuantity = (movement) => {
  const cantidad = Number(movement?.cantidad || 0);
  if (movement?.tipo_movimiento === 'entrada') return `+${cantidad}`;
  if (movement?.tipo_movimiento === 'salida') return `-${cantidad}`;
  if (movement?.tipo_movimiento === TRANSFER_TYPE) return '0';
  return `= ${cantidad}`;
};

// Hora local (HH:MM) en que se registró el movimiento; vacío en filas anteriores a la migración 027.
export const movementTime = (movement) => {
  const match = String(movement?.hora_movimiento || '').match(/^(\d{2}):(\d{2})/);
  return match ? `${match[1]}:${match[2]}` : '';
};

// Clave de orden cronológico: fecha, hora y número de registro.
export const movementSortKey = (movement) =>
  `${movement?.fecha_movimiento || ''} ${String(movement?.hora_movimiento || '').slice(0, 8).padEnd(8, '0')} ${String(movement?.id_mov || 0).padStart(10, '0')}`;

// Etiqueta legible del tipo de movimiento.
export const MOVEMENT_TYPE_LABELS = { entrada: 'Entrada', salida: 'Salida', ajuste: 'Ajuste', traslado: 'Traslado' };
export const movementTypeLabel = (type) => MOVEMENT_TYPE_LABELS[type] || String(type || '');

// Movimientos que tocan una unidad: los ligados por id_unidad y, en los anteriores a la 027, los que nombran su código.
// El código se compara como palabra completa: 1001-MH-02 no coincide con 1001-MH-022.
const codesIn = (text) => String(text || '').split(/[^A-Za-z0-9-]+/).filter(Boolean);
// Las altas anotan rangos: "1001-MH-023 a 1001-MH-030" incluye a 1001-MH-025.
const inCodeRange = (text, code) => [...String(text || '').matchAll(/([A-Za-z0-9]+-[A-Za-z]+)-(\d+) a \1-(\d+)/g)]
  .some(([, prefix, from, to]) => {
    const match = String(code).match(/^(.*)-(\d+)$/);
    return match && match[1] === prefix && Number(match[2]) >= Number(from) && Number(match[2]) <= Number(to);
  });
const touchesUnit = (movement, unit) => Number(movement?.id_unidad) === Number(unit?.id_unidad)
  || (Boolean(unit?.codigo) && (codesIn(movement?.descripcion).includes(unit.codigo) || inCodeRange(movement?.descripcion, unit.codigo)));

/**
 * Historial del artículo del movimiento, de lo más reciente a lo más antiguo.
 * Con unit, solo los movimientos de esa unidad.
 */
export const movementHistory = (movements, movement, unit = null) => (movements || [])
  .filter((row) => Number(row.id_item) === Number(movement?.id_item) && (!unit || touchesUnit(row, unit)))
  .sort((a, b) => movementSortKey(b).localeCompare(movementSortKey(a)));

// Nombre de quien registró el movimiento; sin usuario es un movimiento automático (pedidos, migraciones).
export const movementAuthor = (movement, users = []) => {
  const id = movement?.id_usuario;
  if (id === null || id === undefined || id === '') return 'Automático';
  const digits = (value) => Number(String(value ?? '').match(/(\d+)$/)?.[1] || NaN);
  const user = users.find((entry) => String(entry.id_usuario) === String(id) || digits(entry.id_usuario) === digits(id));
  return user?.nombre || user?.name || (user ? String(user.id_usuario) : `Usuario #${id}`);
};
