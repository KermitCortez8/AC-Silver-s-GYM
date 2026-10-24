/** Aritmética decimal en enteros, con el mismo redondeo que el backend. */
const scaled = (value, places) => {
  const match = String(value ?? 0).trim().match(/^([+-]?)(\d+)(?:\.(\d*))?(?:e([+-]?\d+))?$/i);
  if (!match) throw new Error('Importe monetario inválido');
  const fraction = match[3] || '';
  const power = places + Number(match[4] || 0) - fraction.length;
  if (Math.abs(power) > 308) throw new Error('Importe monetario fuera de rango');
  let units = BigInt(match[2] + fraction);
  if (power >= 0) units *= 10n ** BigInt(power);
  else {
    const divisor = 10n ** BigInt(-power);
    units = (units + divisor / 2n) / divisor;
  }
  const result = Number(match[1] === '-' ? -units : units);
  if (!Number.isSafeInteger(result)) throw new Error('Importe monetario fuera de rango');
  return result;
};

export const toCents = (value) => scaled(value, 2);

export const discountedPrice = (price, discount, kind = 'percent') => {
  const base = toCents(price);
  const reduction = kind === 'fixed'
    ? toCents(discount)
    : Number((BigInt(base) * BigInt(scaled(discount, 6)) + 50_000_000n) / 100_000_000n);
  return Math.max(0, base - reduction) / 100;
};

export const orderTotals = (items) => {
  const subtotal = items.reduce((sum, item) => sum + toCents(item.precio) * item.cantidad, 0);
  const igv = Number((BigInt(subtotal) * 18n + 50n) / 100n);
  return { subtotal: subtotal / 100, igv: igv / 100, total: (subtotal + igv) / 100 };
};
