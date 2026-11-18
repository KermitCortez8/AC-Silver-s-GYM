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
