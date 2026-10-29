// Stock is stored as a PostgreSQL integer. Validate before numeric conversion.
export const MAX_QUANTITY = 2147483647;

export const parseQuantity = (value, { min = 0, label = 'La cantidad' } = {}) => {
  if (!['string', 'number'].includes(typeof value) || !/^[0-9]+$/.test(String(value))) {
    throw new Error(`${label} debe contener solo dígitos enteros.`);
  }
  const quantity = Number(value);
  if (!Number.isSafeInteger(quantity) || quantity < min || quantity > MAX_QUANTITY) {
    throw new Error(`${label} debe estar entre ${min} y ${MAX_QUANTITY}.`);
  }
  return quantity;
};
